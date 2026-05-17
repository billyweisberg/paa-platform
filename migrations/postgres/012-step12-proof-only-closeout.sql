-- Step 12: Proof-only closeout support
--
-- Adds an explicit proof-only acceptance decision and updates full-chain
-- reporting so proof-only terminal slices remain visibly distinct from
-- live accepted / merged slices.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa'
      AND t.typname = 'acceptance_decision'
      AND e.enumlabel = 'proof_only_closed'
  ) THEN
    ALTER TYPE paa.acceptance_decision ADD VALUE 'proof_only_closed';
  END IF;
END
$$;

COMMIT;

-- Recreate reporting view so proof-only closeout remains distinct from
-- accepted live-delivery closeout in projections.

-- PAA full-chain reporting view
--
-- Reusable reporting surface for one-row work-item traceability across:
-- - design package
-- - coder brief
-- - compiled packet runs
-- - queue transport
-- - evidence
-- - acceptance

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

CREATE OR REPLACE VIEW paa.v_work_item_full_chain_traceability AS
WITH latest_design_package AS (
  SELECT DISTINCT ON (dp.work_item_id)
    dp.design_package_id,
    dp.project_id,
    dp.work_item_id,
    dp.package_id_external,
    dp.status::text AS design_package_status,
    dp.created_at,
    dp.updated_at
  FROM paa.design_packages dp
  WHERE dp.work_item_id IS NOT NULL
  ORDER BY dp.work_item_id, dp.updated_at DESC, dp.created_at DESC, dp.design_package_id DESC
), latest_dev_run AS (
  SELECT DISTINCT ON (ar.work_item_id)
    ar.automation_run_id,
    ar.work_item_id,
    ar.handoff_id,
    ar.status::text AS automation_run_status,
    ar.summary,
    ar.started_at,
    ar.finished_at,
    ar.created_at,
    ar.artifacts_json->>'message_id' AS message_id,
    ar.artifacts_json->>'package_id_external' AS package_id_external,
    ar.artifacts_json->>'brief_id_external' AS brief_id_external
  FROM paa.automation_runs ar
  WHERE ar.work_item_id IS NOT NULL
    AND ar.trigger_type IN (
      'packet_compilation:slice_result_packet',
      'packet_compilation:worker_result_packet'
    )
  ORDER BY ar.work_item_id, COALESCE(ar.finished_at, ar.started_at, ar.created_at) DESC, ar.created_at DESC, ar.automation_run_id DESC
), latest_qa_run AS (
  SELECT DISTINCT ON (ar.work_item_id)
    ar.automation_run_id,
    ar.work_item_id,
    ar.handoff_id,
    ar.status::text AS automation_run_status,
    ar.summary,
    ar.started_at,
    ar.finished_at,
    ar.created_at,
    ar.artifacts_json->>'message_id' AS message_id,
    ar.artifacts_json->>'package_id_external' AS package_id_external,
    ar.artifacts_json->>'brief_id_external' AS brief_id_external
  FROM paa.automation_runs ar
  WHERE ar.work_item_id IS NOT NULL
    AND ar.trigger_type = 'packet_compilation:qa_verification_packet'
  ORDER BY ar.work_item_id, COALESCE(ar.finished_at, ar.started_at, ar.created_at) DESC, ar.created_at DESC, ar.automation_run_id DESC
), latest_acceptance AS (
  SELECT DISTINCT ON (ae.work_item_id)
    ae.acceptance_event_id,
    ae.project_id,
    ae.work_item_id,
    ae.handoff_id,
    ae.decision::text AS acceptance_decision,
    ae.notes AS acceptance_notes,
    ae.merge_commit_sha,
    ae.created_at AS acceptance_created_at
  FROM paa.acceptance_events ae
  WHERE ae.work_item_id IS NOT NULL
  ORDER BY ae.work_item_id, ae.created_at DESC, ae.acceptance_event_id DESC
), resolved_brief_keys AS (
  SELECT
    wi.work_item_id,
    COALESCE(ldev.brief_id_external, lqa.brief_id_external) AS brief_id_external,
    COALESCE(ldev.package_id_external, lqa.package_id_external, ldp.package_id_external) AS package_id_external
  FROM paa.work_items wi
  LEFT JOIN latest_dev_run ldev ON ldev.work_item_id = wi.work_item_id
  LEFT JOIN latest_qa_run lqa ON lqa.work_item_id = wi.work_item_id
  LEFT JOIN latest_design_package ldp ON ldp.work_item_id = wi.work_item_id
), resolved_brief AS (
  SELECT
    wi.work_item_id,
    cb.coder_run_brief_id,
    cb.brief_id_external,
    cb.status::text AS coder_brief_status,
    cb.component_assignment_json->>'component_name' AS component_name,
    cb.component_assignment_json->>'component_role' AS component_role,
    cb.component_assignment_json->>'system_layer' AS system_layer
  FROM paa.work_items wi
  LEFT JOIN resolved_brief_keys rbk ON rbk.work_item_id = wi.work_item_id
  LEFT JOIN paa.coder_run_briefs cb ON cb.work_item_id = wi.work_item_id
    AND cb.brief_id_external = rbk.brief_id_external
), latest_dev_queue AS (
  SELECT DISTINCT ON (qm.handoff_id)
    qm.handoff_id,
    qm.queue_message_id,
    qm.queue_name,
    qm.schema_type,
    qm.message_id_external,
    qm.status::text AS queue_status,
    qm.sent_at,
    qm.claimed_at,
    qm.acknowledged_at,
    qm.metadata_json
  FROM paa.queue_messages qm
  JOIN latest_dev_run ldev ON ldev.handoff_id = qm.handoff_id
  ORDER BY qm.handoff_id, qm.updated_at DESC, qm.created_at DESC, qm.queue_message_id DESC
), latest_qa_queue AS (
  SELECT DISTINCT ON (qm.handoff_id)
    qm.handoff_id,
    qm.queue_message_id,
    qm.queue_name,
    qm.schema_type,
    qm.message_id_external,
    qm.status::text AS queue_status,
    qm.sent_at,
    qm.claimed_at,
    qm.acknowledged_at,
    qm.metadata_json
  FROM paa.queue_messages qm
  JOIN latest_qa_run lqa ON lqa.handoff_id = qm.handoff_id
  ORDER BY qm.handoff_id, qm.updated_at DESC, qm.created_at DESC, qm.queue_message_id DESC
), dev_evidence_agg AS (
  SELECT
    wi.work_item_id,
    COUNT(ev.evidence_id) AS dev_evidence_count,
    STRING_AGG(ev.result::text, ',' ORDER BY ev.result::text) AS dev_evidence_results,
    MAX(ev.captured_at) AS dev_evidence_last_captured_at
  FROM paa.work_items wi
  JOIN latest_dev_run ldev ON ldev.work_item_id = wi.work_item_id
  LEFT JOIN paa.evidence ev ON ev.work_item_id = wi.work_item_id
    AND ev.artifact_location LIKE ('dev-packet:' || ldev.message_id || ':%')
  GROUP BY wi.work_item_id
), qa_evidence_agg AS (
  SELECT
    wi.work_item_id,
    COUNT(ev.evidence_id) AS qa_evidence_count,
    STRING_AGG(ev.result::text, ',' ORDER BY ev.result::text) AS qa_evidence_results,
    MAX(ev.captured_at) AS qa_evidence_last_captured_at
  FROM paa.work_items wi
  JOIN latest_qa_run lqa ON lqa.work_item_id = wi.work_item_id
  LEFT JOIN paa.evidence ev ON ev.work_item_id = wi.work_item_id
    AND ev.artifact_location = ('qa-packet:' || lqa.message_id)
  GROUP BY wi.work_item_id
)
SELECT
  p.slug AS project_slug,
  wi.work_item_id,
  wi.issue_number,
  wi.title AS work_item_title,
  wi.status::text AS work_item_status,
  ldp.design_package_id,
  ldp.package_id_external,
  ldp.design_package_status,
  rb.coder_run_brief_id,
  rb.brief_id_external,
  rb.coder_brief_status,
  rb.component_name,
  rb.component_role,
  rb.system_layer,
  ldev.automation_run_id AS dev_compilation_run_id,
  ldev.automation_run_status AS dev_compilation_status,
  ldev.message_id AS dev_message_id,
  ldq.queue_message_id AS dev_queue_message_id,
  ldq.queue_name AS dev_queue_name,
  ldq.queue_status AS dev_queue_status,
  hdev.handoff_id AS dev_handoff_id,
  hdev.status::text AS dev_handoff_status,
  ldq.sent_at AS dev_sent_at,
  ldq.claimed_at AS dev_claimed_at,
  ldq.acknowledged_at AS dev_acknowledged_at,
  COALESCE(dea.dev_evidence_count, 0) AS dev_evidence_count,
  COALESCE(dea.dev_evidence_results, '') AS dev_evidence_results,
  dea.dev_evidence_last_captured_at,
  lqa.automation_run_id AS qa_compilation_run_id,
  lqa.automation_run_status AS qa_compilation_status,
  lqa.message_id AS qa_message_id,
  lqq.queue_message_id AS qa_queue_message_id,
  lqq.queue_name AS qa_queue_name,
  lqq.queue_status AS qa_queue_status,
  hqa.handoff_id AS qa_handoff_id,
  hqa.status::text AS qa_handoff_status,
  lqq.sent_at AS qa_sent_at,
  lqq.claimed_at AS qa_claimed_at,
  lqq.acknowledged_at AS qa_acknowledged_at,
  COALESCE(qea.qa_evidence_count, 0) AS qa_evidence_count,
  COALESCE(qea.qa_evidence_results, '') AS qa_evidence_results,
  qea.qa_evidence_last_captured_at,
  la.acceptance_event_id,
  la.acceptance_decision,
  la.handoff_id AS acceptance_handoff_id,
  la.merge_commit_sha,
  la.acceptance_notes,
  la.acceptance_created_at,
  CASE
    WHEN la.acceptance_decision = 'accepted'
      AND COALESCE(dea.dev_evidence_count, 0) > 0
      AND COALESCE(qea.qa_evidence_count, 0) > 0
      AND ldev.automation_run_id IS NOT NULL
      AND lqa.automation_run_id IS NOT NULL
      THEN 'accepted_full_chain'
    WHEN la.acceptance_decision = 'proof_only_closed'
      AND COALESCE(dea.dev_evidence_count, 0) > 0
      AND COALESCE(qea.qa_evidence_count, 0) > 0
      AND ldev.automation_run_id IS NOT NULL
      AND lqa.automation_run_id IS NOT NULL
      THEN 'proof_only_closed_full_chain'
    WHEN lqa.automation_run_id IS NOT NULL
      AND COALESCE(qea.qa_evidence_count, 0) > 0
      THEN 'qa_verified_pending_acceptance'
    WHEN ldev.automation_run_id IS NOT NULL
      AND COALESCE(dea.dev_evidence_count, 0) > 0
      THEN 'dev_verified_pending_qa'
    WHEN rb.coder_run_brief_id IS NOT NULL
      THEN 'brief_materialized'
    WHEN ldp.design_package_id IS NOT NULL
      THEN 'design_packaged'
    ELSE 'work_item_only'
  END AS full_chain_state,
  GREATEST(
    COALESCE(la.acceptance_created_at, '-infinity'::timestamptz),
    COALESCE(qea.qa_evidence_last_captured_at, '-infinity'::timestamptz),
    COALESCE(lqq.acknowledged_at, '-infinity'::timestamptz),
    COALESCE(dea.dev_evidence_last_captured_at, '-infinity'::timestamptz),
    COALESCE(ldq.acknowledged_at, '-infinity'::timestamptz),
    COALESCE(ldp.updated_at, '-infinity'::timestamptz),
    COALESCE(wi.updated_at, '-infinity'::timestamptz)
  ) AS last_transition_at
FROM paa.work_items wi
JOIN paa.projects p ON p.project_id = wi.project_id
LEFT JOIN latest_design_package ldp ON ldp.work_item_id = wi.work_item_id
LEFT JOIN resolved_brief rb ON rb.work_item_id = wi.work_item_id
LEFT JOIN latest_dev_run ldev ON ldev.work_item_id = wi.work_item_id
LEFT JOIN latest_dev_queue ldq ON ldq.handoff_id = ldev.handoff_id
LEFT JOIN paa.handoffs hdev ON hdev.handoff_id = ldev.handoff_id
LEFT JOIN dev_evidence_agg dea ON dea.work_item_id = wi.work_item_id
LEFT JOIN latest_qa_run lqa ON lqa.work_item_id = wi.work_item_id
LEFT JOIN latest_qa_queue lqq ON lqq.handoff_id = lqa.handoff_id
LEFT JOIN paa.handoffs hqa ON hqa.handoff_id = lqa.handoff_id
LEFT JOIN qa_evidence_agg qea ON qea.work_item_id = wi.work_item_id
LEFT JOIN latest_acceptance la ON la.work_item_id = wi.work_item_id;

COMMIT;
