-- PAA full-chain proof queries
--
-- These queries show the current live proof state in `paa_dev`.
--
-- Current honest split:
-- - issue #201 proves:
--   design package -> coder brief -> compiled packet run -> queue send -> claim/ack
-- - issue #71 proves:
--   work item -> evidence -> acceptance
--
-- Once a compiled-packet-driven slice completes end to end through QA and Architect,
-- the same shape can be queried for a single work item.

-- 1. Proof transport chain for the proving package / resolver brief.
WITH target_work_item AS (
  SELECT wi.work_item_id, wi.issue_number, wi.title, wi.status
  FROM paa.work_items wi
  JOIN paa.projects p ON p.project_id = wi.project_id
  WHERE p.slug = 'fractal-core-python'
    AND wi.issue_number = 201
), target_package AS (
  SELECT dp.design_package_id, dp.work_item_id, dp.package_id_external, dp.status
  FROM paa.design_packages dp
  JOIN target_work_item twi ON twi.work_item_id = dp.work_item_id
  WHERE dp.package_id_external = 'fcore-stage1-2026-05-02-retirement-subsystem-decomposition'
), target_brief AS (
  SELECT cb.coder_run_brief_id, cb.work_item_id, cb.brief_id_external, cb.status,
         cb.component_assignment_json->>'component_name' AS component_name,
         cb.component_assignment_json->>'component_role' AS component_role,
         cb.component_assignment_json->>'system_layer' AS system_layer
  FROM paa.coder_run_briefs cb
  JOIN target_work_item twi ON twi.work_item_id = cb.work_item_id
  WHERE cb.brief_id_external = 'fcore-coder-2026-05-02-retirement-policy-resolver'
), compiled_packet_run AS (
  SELECT ar.automation_run_id, ar.handoff_id, ar.work_item_id, ar.trigger_type, ar.status,
         ar.artifacts_json->>'message_id' AS message_id,
         ar.artifacts_json->>'package_id_external' AS package_id_external,
         ar.artifacts_json->>'brief_id_external' AS brief_id_external,
         ar.artifacts_json->>'review_output_path' AS review_output_path,
         ar.created_at
  FROM paa.automation_runs ar
  JOIN target_work_item twi ON twi.work_item_id = ar.work_item_id
  WHERE ar.trigger_type = 'packet_compilation:slice_result_packet'
    AND ar.artifacts_json->>'message_id' = 'fcore-py-2026-05-02-issue201-fcore-coder-2026-05-02-retirement-policy-resolver-transport2'
), queued_message AS (
  SELECT qm.queue_message_id, qm.handoff_id, qm.queue_name, qm.status,
         qm.message_id_external, qm.correlation_key,
         qm.sent_at, qm.claimed_at, qm.acknowledged_at,
         qm.metadata_json->>'compiled_packet_automation_run_id' AS compiled_packet_automation_run_id,
         qm.metadata_json->>'compiled_packet_package_id_external' AS compiled_packet_package_id_external,
         qm.metadata_json->>'compiled_packet_brief_id_external' AS compiled_packet_brief_id_external
  FROM paa.queue_messages qm
  JOIN compiled_packet_run cpr ON cpr.message_id = qm.message_id_external
), routed_handoff AS (
  SELECT h.handoff_id, h.work_item_id, h.handoff_type, h.status,
         h.created_at, h.claimed_at, h.acknowledged_at, h.closed_at
  FROM paa.handoffs h
  JOIN queued_message qm ON qm.handoff_id = h.handoff_id
)
SELECT
  twi.issue_number,
  twi.title AS work_item_title,
  twi.status AS work_item_status,
  tp.package_id_external,
  tb.brief_id_external,
  tb.component_name,
  tb.component_role,
  tb.system_layer,
  cpr.automation_run_id AS compiled_packet_run_id,
  cpr.trigger_type AS compiled_packet_trigger_type,
  cpr.status AS compiled_packet_status,
  cpr.message_id,
  qm.queue_message_id,
  qm.queue_name,
  qm.status AS queue_message_status,
  qm.sent_at,
  qm.claimed_at AS queue_claimed_at,
  qm.acknowledged_at AS queue_acknowledged_at,
  qm.compiled_packet_automation_run_id,
  rh.handoff_id,
  rh.handoff_type,
  rh.status AS handoff_status,
  rh.claimed_at AS handoff_claimed_at,
  rh.acknowledged_at AS handoff_acknowledged_at,
  cpr.review_output_path
FROM target_work_item twi
LEFT JOIN target_package tp ON tp.work_item_id = twi.work_item_id
LEFT JOIN target_brief tb ON tb.work_item_id = twi.work_item_id
LEFT JOIN compiled_packet_run cpr ON cpr.work_item_id = twi.work_item_id
LEFT JOIN queued_message qm ON qm.handoff_id = cpr.handoff_id
LEFT JOIN routed_handoff rh ON rh.handoff_id = cpr.handoff_id;


-- 2. Evidence and acceptance chain for an accepted real slice.
WITH accepted_work_item AS (
  SELECT wi.work_item_id, wi.issue_number, wi.title, wi.status
  FROM paa.work_items wi
  JOIN paa.projects p ON p.project_id = wi.project_id
  WHERE p.slug = 'fractal-core-python'
    AND wi.issue_number = 71
), evidence_rollup AS (
  SELECT
    ev.work_item_id,
    COUNT(*) AS evidence_count,
    STRING_AGG(DISTINCT ev.result::text, ', ' ORDER BY ev.result::text) AS evidence_results,
    STRING_AGG(DISTINCT ev.artifact_location, ' | ' ORDER BY ev.artifact_location) AS artifact_locations
  FROM paa.evidence ev
  JOIN accepted_work_item awi ON awi.work_item_id = ev.work_item_id
  GROUP BY ev.work_item_id
), acceptance_rollup AS (
  SELECT
    ae.work_item_id,
    COUNT(*) AS acceptance_event_count,
    STRING_AGG(ae.decision::text, ' -> ' ORDER BY ae.created_at) AS acceptance_decision_path,
    STRING_AGG(COALESCE(ae.notes, '(no notes)'), ' || ' ORDER BY ae.created_at) AS acceptance_notes
  FROM paa.acceptance_events ae
  JOIN accepted_work_item awi ON awi.work_item_id = ae.work_item_id
  GROUP BY ae.work_item_id
)
SELECT
  awi.issue_number,
  awi.title AS work_item_title,
  awi.status AS work_item_status,
  er.evidence_count,
  er.evidence_results,
  er.artifact_locations,
  ar.acceptance_event_count,
  ar.acceptance_decision_path,
  ar.acceptance_notes
FROM accepted_work_item awi
LEFT JOIN evidence_rollup er ON er.work_item_id = awi.work_item_id
LEFT JOIN acceptance_rollup ar ON ar.work_item_id = awi.work_item_id;


-- 3. Portfolio proof summary: which work item currently proves which segment.
WITH package_chain AS (
  SELECT
    wi.issue_number,
    'design_package_to_transport' AS proof_segment,
    dp.package_id_external,
    cb.brief_id_external,
    ar.automation_run_id::text AS proof_ref_1,
    qm.queue_message_id::text AS proof_ref_2,
    h.handoff_id::text AS proof_ref_3,
    CONCAT('queue_status=', qm.status, ', handoff_status=', h.status) AS summary
  FROM paa.work_items wi
  JOIN paa.design_packages dp ON dp.work_item_id = wi.work_item_id
  JOIN paa.coder_run_briefs cb ON cb.work_item_id = wi.work_item_id
  JOIN paa.automation_runs ar ON ar.work_item_id = wi.work_item_id
  JOIN paa.queue_messages qm ON qm.message_id_external = ar.artifacts_json->>'message_id'
  JOIN paa.handoffs h ON h.handoff_id = qm.handoff_id
  WHERE wi.issue_number = 201
    AND cb.brief_id_external = 'fcore-coder-2026-05-02-retirement-policy-resolver'
    AND ar.trigger_type = 'packet_compilation:slice_result_packet'
    AND ar.artifacts_json->>'message_id' = 'fcore-py-2026-05-02-issue201-fcore-coder-2026-05-02-retirement-policy-resolver-transport2'
), evidence_acceptance_chain AS (
  SELECT
    wi.issue_number,
    'evidence_to_acceptance' AS proof_segment,
    NULL::text AS package_id_external,
    NULL::text AS brief_id_external,
    MIN(ev.evidence_id::text) AS proof_ref_1,
    MIN(ae.acceptance_event_id::text) AS proof_ref_2,
    NULL::text AS proof_ref_3,
    CONCAT('evidence=', COUNT(DISTINCT ev.evidence_id), ', acceptance_events=', COUNT(DISTINCT ae.acceptance_event_id)) AS summary
  FROM paa.work_items wi
  JOIN paa.evidence ev ON ev.work_item_id = wi.work_item_id
  JOIN paa.acceptance_events ae ON ae.work_item_id = wi.work_item_id
  WHERE wi.issue_number = 71
  GROUP BY wi.issue_number
)
SELECT * FROM package_chain
UNION ALL
SELECT * FROM evidence_acceptance_chain
ORDER BY issue_number, proof_segment;
