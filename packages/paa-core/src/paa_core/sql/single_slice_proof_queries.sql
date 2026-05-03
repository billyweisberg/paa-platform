-- PAA single-slice full-chain proof queries
--
-- This file proves the full modern chain on one work item:
-- issue #201, the retirement subsystem decomposition proof slice.

-- 1. Full one-row chain for issue #201.
WITH target_work_item AS (
  SELECT wi.work_item_id, wi.issue_number, wi.title, wi.status
  FROM paa.work_items wi
  JOIN paa.projects p ON p.project_id = wi.project_id
  WHERE p.slug = 'fractal-core-python'
    AND wi.issue_number = 201
), target_package AS (
  SELECT dp.design_package_id, dp.package_id_external, dp.status, dp.work_item_id
  FROM paa.design_packages dp
  JOIN target_work_item twi ON twi.work_item_id = dp.work_item_id
  WHERE dp.package_id_external = 'fcore-stage1-2026-05-02-retirement-subsystem-decomposition'
), target_brief AS (
  SELECT cb.coder_run_brief_id, cb.brief_id_external, cb.status,
         cb.component_assignment_json->>'component_name' AS component_name,
         cb.component_assignment_json->>'component_role' AS component_role,
         cb.component_assignment_json->>'system_layer' AS system_layer,
         cb.work_item_id
  FROM paa.coder_run_briefs cb
  JOIN target_work_item twi ON twi.work_item_id = cb.work_item_id
  WHERE cb.brief_id_external = 'fcore-coder-2026-05-02-retirement-policy-resolver'
), dev_compiled_run AS (
  SELECT ar.automation_run_id, ar.handoff_id, ar.status, ar.trigger_type,
         ar.artifacts_json->>'message_id' AS message_id,
         ar.artifacts_json->>'review_output_path' AS review_output_path,
         ar.created_at
  FROM paa.automation_runs ar
  JOIN target_work_item twi ON twi.work_item_id = ar.work_item_id
  WHERE ar.trigger_type = 'packet_compilation:slice_result_packet'
    AND ar.artifacts_json->>'message_id' = 'fcore-py-2026-05-02-issue201-fcore-coder-2026-05-02-retirement-policy-resolver-fullproof2'
), dev_queue AS (
  SELECT qm.queue_message_id, qm.handoff_id, qm.queue_name, qm.status,
         qm.sent_at, qm.claimed_at, qm.acknowledged_at
  FROM paa.queue_messages qm
  JOIN dev_compiled_run dcr ON dcr.message_id = qm.message_id_external
), dev_handoff AS (
  SELECT h.handoff_id, h.status, h.claimed_at, h.acknowledged_at
  FROM paa.handoffs h
  JOIN dev_queue dq ON dq.handoff_id = h.handoff_id
), dev_evidence AS (
  SELECT
    ev.work_item_id,
    COUNT(*) AS dev_evidence_count,
    STRING_AGG(ev.artifact_location, ' | ' ORDER BY ev.artifact_location) AS dev_artifacts
  FROM paa.evidence ev
  JOIN target_work_item twi ON twi.work_item_id = ev.work_item_id
  WHERE ev.artifact_location LIKE 'dev-packet:fcore-py-2026-05-02-issue201-fcore-coder-2026-05-02-retirement-policy-resolver-fullproof2:%'
  GROUP BY ev.work_item_id
), qa_compiled_run AS (
  SELECT ar.automation_run_id, ar.handoff_id, ar.status, ar.trigger_type,
         ar.artifacts_json->>'message_id' AS message_id,
         ar.artifacts_json->>'review_output_path' AS review_output_path,
         ar.created_at
  FROM paa.automation_runs ar
  JOIN target_work_item twi ON twi.work_item_id = ar.work_item_id
  WHERE ar.trigger_type = 'packet_compilation:qa_verification_packet'
    AND ar.artifacts_json->>'message_id' = 'fcore-qa-2026-05-02-issue201-fcore-coder-2026-05-02-retirement-policy-resolver-fullproof2'
), qa_queue AS (
  SELECT qm.queue_message_id, qm.handoff_id, qm.queue_name, qm.status,
         qm.sent_at, qm.claimed_at, qm.acknowledged_at
  FROM paa.queue_messages qm
  JOIN qa_compiled_run qcr ON qcr.message_id = qm.message_id_external
), qa_handoff AS (
  SELECT h.handoff_id, h.status, h.claimed_at, h.acknowledged_at
  FROM paa.handoffs h
  JOIN qa_queue qq ON qq.handoff_id = h.handoff_id
), qa_evidence AS (
  SELECT ev.evidence_id, ev.result, ev.artifact_location, ev.summary, ev.work_item_id
  FROM paa.evidence ev
  JOIN target_work_item twi ON twi.work_item_id = ev.work_item_id
  WHERE ev.artifact_location = 'qa-packet:fcore-qa-2026-05-02-issue201-fcore-coder-2026-05-02-retirement-policy-resolver-fullproof2'
), architect_acceptance AS (
  SELECT ae.acceptance_event_id, ae.decision, ae.handoff_id, ae.notes, ae.created_at, ae.work_item_id
  FROM paa.acceptance_events ae
  JOIN target_work_item twi ON twi.work_item_id = ae.work_item_id
  WHERE ae.notes = 'Architect accepted the second full compiled-packet proving slice after QA pass, with linked proof handoff and evidence.'
)
SELECT
  twi.issue_number,
  twi.title AS work_item_title,
  twi.status AS work_item_status,
  tp.package_id_external,
  tp.status AS design_package_status,
  tb.brief_id_external,
  tb.status AS coder_brief_status,
  tb.component_name,
  tb.component_role,
  tb.system_layer,
  dcr.automation_run_id AS dev_compiled_run_id,
  dcr.message_id AS dev_message_id,
  dq.queue_name AS dev_queue_name,
  dq.status AS dev_queue_status,
  dh.status AS dev_handoff_status,
  de.dev_evidence_count,
  de.dev_artifacts,
  qcr.automation_run_id AS qa_compiled_run_id,
  qcr.message_id AS qa_message_id,
  qq.queue_name AS qa_queue_name,
  qq.status AS qa_queue_status,
  qh.status AS qa_handoff_status,
  qe.result AS qa_evidence_result,
  qe.artifact_location AS qa_artifact_location,
  aa.acceptance_event_id,
  aa.decision AS architect_decision,
  aa.handoff_id AS architect_linked_handoff_id,
  aa.notes AS architect_notes
FROM target_work_item twi
LEFT JOIN target_package tp ON tp.work_item_id = twi.work_item_id
LEFT JOIN target_brief tb ON tb.work_item_id = twi.work_item_id
LEFT JOIN dev_compiled_run dcr ON TRUE
LEFT JOIN dev_queue dq ON dq.handoff_id = dcr.handoff_id
LEFT JOIN dev_handoff dh ON dh.handoff_id = dcr.handoff_id
LEFT JOIN dev_evidence de ON de.work_item_id = twi.work_item_id
LEFT JOIN qa_compiled_run qcr ON TRUE
LEFT JOIN qa_queue qq ON qq.handoff_id = qcr.handoff_id
LEFT JOIN qa_handoff qh ON qh.handoff_id = qcr.handoff_id
LEFT JOIN qa_evidence qe ON qe.work_item_id = twi.work_item_id
LEFT JOIN architect_acceptance aa ON aa.work_item_id = twi.work_item_id;


-- 2. Compact lifecycle summary for issue #201.
WITH twi AS (
  SELECT wi.work_item_id, wi.issue_number, wi.title, wi.status
  FROM paa.work_items wi
  WHERE wi.issue_number = 201
), summary AS (
  SELECT
    wi.issue_number,
    COUNT(DISTINCT dp.design_package_id) AS design_packages,
    COUNT(DISTINCT cb.coder_run_brief_id) AS coder_briefs,
    COUNT(DISTINCT ar.automation_run_id) FILTER (WHERE ar.trigger_type LIKE 'packet_compilation:%') AS compiled_packet_runs,
    COUNT(DISTINCT qm.queue_message_id) AS queue_messages,
    COUNT(DISTINCT h.handoff_id) AS handoffs,
    COUNT(DISTINCT ev.evidence_id) AS evidence_rows,
    COUNT(DISTINCT ae.acceptance_event_id) AS acceptance_events
  FROM twi wi
  LEFT JOIN paa.design_packages dp ON dp.work_item_id = wi.work_item_id
  LEFT JOIN paa.coder_run_briefs cb ON cb.work_item_id = wi.work_item_id
  LEFT JOIN paa.automation_runs ar ON ar.work_item_id = wi.work_item_id
  LEFT JOIN paa.queue_messages qm ON qm.message_id_external = ar.artifacts_json->>'message_id'
  LEFT JOIN paa.handoffs h ON h.handoff_id = qm.handoff_id
  LEFT JOIN paa.evidence ev ON ev.work_item_id = wi.work_item_id
  LEFT JOIN paa.acceptance_events ae ON ae.work_item_id = wi.work_item_id
  GROUP BY wi.issue_number
)
SELECT * FROM summary;
