#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SRC = REPO_ROOT / "packages" / "paa-core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from paa_core.db import run_psql


VIEW_SQL = """
CREATE OR REPLACE VIEW paa.project_delivery_projections AS
WITH plan_base AS (
  SELECT
    ip.implementation_plan_id,
    ip.project_id,
    ip.work_item_id,
    ip.primary_component_id,
    ip.plan_id_external,
    ip.consumer_context_key,
    ip.plan_title,
    ip.plan_kind,
    ip.status::text AS implementation_plan_status,
    ip.authority_state::text AS authority_state,
    ip.created_at,
    ip.updated_at
  FROM paa.implementation_plans ip
  WHERE ip.primary_component_id IS NOT NULL
),
activity_dependency_counts AS (
  SELECT
    ipa.implementation_plan_activity_id,
    COUNT(DISTINCT pred.predecessor_activity_id) AS predecessor_count,
    COUNT(DISTINCT CASE
      WHEN pred_activity.activity_state::text = 'completed' THEN pred.predecessor_activity_id
      ELSE NULL
    END) AS completed_predecessor_count
  FROM paa.implementation_plan_activities ipa
  LEFT JOIN paa.implementation_plan_activity_dependencies pred
    ON pred.successor_activity_id = ipa.implementation_plan_activity_id
  LEFT JOIN paa.implementation_plan_activities pred_activity
    ON pred_activity.implementation_plan_activity_id = pred.predecessor_activity_id
  GROUP BY ipa.implementation_plan_activity_id
),
activity_base AS (
  SELECT
    ipa.implementation_plan_activity_id,
    ipa.implementation_plan_id,
    ipa.component_element_id,
    ipa.component_element_realization_id,
    ipa.activity_key,
    ipa.activity_title,
    ipa.activity_kind::text AS activity_kind,
    ipa.activity_state::text AS activity_state,
    ipa.sequence_order,
    ipa.target_path,
    ipa.target_module,
    ipa.planned_artifact_type_key,
    COALESCE(adc.predecessor_count, 0) AS predecessor_count,
    COALESCE(adc.completed_predecessor_count, 0) AS completed_predecessor_count
  FROM paa.implementation_plan_activities ipa
  LEFT JOIN activity_dependency_counts adc
    ON adc.implementation_plan_activity_id = ipa.implementation_plan_activity_id
),
activity_projection AS (
  SELECT
    pb.implementation_plan_id,
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'implementation_plan_activity_id', ab.implementation_plan_activity_id::text,
          'activity_key', ab.activity_key,
          'activity_title', ab.activity_title,
          'activity_kind', ab.activity_kind,
          'activity_state', ab.activity_state,
          'sequence_order', ab.sequence_order,
          'component_element_id', ab.component_element_id::text,
          'component_element_realization_id', ab.component_element_realization_id::text,
          'target_path', ab.target_path,
          'target_module', ab.target_module,
          'planned_artifact_type_key', ab.planned_artifact_type_key
        )
        ORDER BY ab.sequence_order, ab.activity_key
      ) FILTER (WHERE ab.activity_state = 'active'),
      '[]'::jsonb
    ) AS current_activity_set,
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'implementation_plan_activity_id', ab.implementation_plan_activity_id::text,
          'activity_key', ab.activity_key,
          'activity_title', ab.activity_title,
          'activity_kind', ab.activity_kind,
          'activity_state', ab.activity_state,
          'sequence_order', ab.sequence_order,
          'component_element_id', ab.component_element_id::text,
          'component_element_realization_id', ab.component_element_realization_id::text,
          'target_path', ab.target_path,
          'target_module', ab.target_module,
          'planned_artifact_type_key', ab.planned_artifact_type_key
        )
        ORDER BY ab.sequence_order, ab.activity_key
      ) FILTER (
        WHERE ab.activity_state = 'completed'
      ),
      '[]'::jsonb
    ) AS completed_activity_set,
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'implementation_plan_activity_id', ab.implementation_plan_activity_id::text,
          'activity_key', ab.activity_key,
          'activity_title', ab.activity_title,
          'activity_kind', ab.activity_kind,
          'activity_state', ab.activity_state,
          'sequence_order', ab.sequence_order,
          'component_element_id', ab.component_element_id::text,
          'component_element_realization_id', ab.component_element_realization_id::text,
          'target_path', ab.target_path,
          'target_module', ab.target_module,
          'planned_artifact_type_key', ab.planned_artifact_type_key,
          'blocking_reason', CASE
            WHEN pb.authority_state NOT IN ('approved_plan', 'approved_brief', 'packet_ready_execution_authority')
              THEN 'plan_not_execution_ready'
            WHEN ab.activity_state = 'blocked'
              THEN 'activity_state_blocked'
            WHEN ab.predecessor_count > ab.completed_predecessor_count
              THEN 'predecessor_incomplete'
            ELSE 'blocked'
          END
        )
        ORDER BY ab.sequence_order, ab.activity_key
      ) FILTER (
        WHERE ab.activity_state = 'blocked'
           OR (
             ab.activity_state IN ('planned', 'ready')
             AND (
               pb.authority_state NOT IN ('approved_plan', 'approved_brief', 'packet_ready_execution_authority')
               OR ab.predecessor_count > ab.completed_predecessor_count
             )
           )
      ),
      '[]'::jsonb
    ) AS blocked_activity_set,
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'implementation_plan_activity_id', ab.implementation_plan_activity_id::text,
          'activity_key', ab.activity_key,
          'activity_title', ab.activity_title,
          'activity_kind', ab.activity_kind,
          'activity_state', ab.activity_state,
          'sequence_order', ab.sequence_order,
          'component_element_id', ab.component_element_id::text,
          'component_element_realization_id', ab.component_element_realization_id::text,
          'target_path', ab.target_path,
          'target_module', ab.target_module,
          'planned_artifact_type_key', ab.planned_artifact_type_key
        )
        ORDER BY ab.sequence_order, ab.activity_key
      ) FILTER (
        WHERE ab.activity_state IN ('planned', 'ready')
          AND pb.authority_state IN ('approved_plan', 'approved_brief', 'packet_ready_execution_authority')
          AND ab.predecessor_count = ab.completed_predecessor_count
          AND ab.sequence_order = (
            SELECT MIN(ab2.sequence_order)
            FROM activity_base ab2
            WHERE ab2.implementation_plan_id = pb.implementation_plan_id
              AND ab2.activity_state IN ('planned', 'ready')
              AND ab2.predecessor_count = ab2.completed_predecessor_count
          )
      ),
      '[]'::jsonb
    ) AS next_activity_set,
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'implementation_plan_activity_id', ab.implementation_plan_activity_id::text,
          'activity_key', ab.activity_key,
          'activity_title', ab.activity_title,
          'activity_kind', ab.activity_kind,
          'activity_state', ab.activity_state,
          'sequence_order', ab.sequence_order,
          'component_element_id', ab.component_element_id::text,
          'component_element_realization_id', ab.component_element_realization_id::text,
          'target_path', ab.target_path,
          'target_module', ab.target_module,
          'planned_artifact_type_key', ab.planned_artifact_type_key
        )
        ORDER BY ab.sequence_order, ab.activity_key
      ) FILTER (
        WHERE ab.activity_state NOT IN ('completed', 'skipped', 'superseded')
      ),
      '[]'::jsonb
    ) AS critical_path_activity_set
  FROM plan_base pb
  LEFT JOIN activity_base ab
    ON ab.implementation_plan_id = pb.implementation_plan_id
  GROUP BY pb.implementation_plan_id, pb.authority_state
)
SELECT
  pb.project_id,
  pb.work_item_id,
  pb.implementation_plan_id,
  pb.primary_component_id,
  pb.plan_id_external,
  pb.consumer_context_key,
  pb.plan_title,
  pb.plan_kind,
  pb.implementation_plan_status,
  pb.authority_state,
  ap.current_activity_set,
  ap.next_activity_set,
  ap.completed_activity_set,
  ap.blocked_activity_set,
  ap.critical_path_activity_set,
  jsonb_build_object(
    'required_surface_count', 0,
    'passed_surface_count', 0
  ) AS verification_summary,
  jsonb_build_object(
    'workflow_state_present', EXISTS (
      SELECT 1 FROM paa.workflow_states ws WHERE ws.work_item_id = pb.work_item_id
    )
  ) AS workflow_summary,
  jsonb_build_object(
    'runtime_evidence_present', EXISTS (
      SELECT 1 FROM paa.execution_records er WHERE er.work_item_id = pb.work_item_id
    )
  ) AS runtime_summary,
  CASE
    WHEN pb.authority_state NOT IN ('approved_plan', 'approved_brief', 'packet_ready_execution_authority')
      THEN jsonb_build_array('plan_not_execution_ready')
    ELSE '[]'::jsonb
  END AS warnings_json,
  now() AS generated_at
FROM plan_base pb
JOIN activity_projection ap
  ON ap.implementation_plan_id = pb.implementation_plan_id;
"""


def main() -> int:
    run_psql(VIEW_SQL)
    print("materialized_view\tpaa.project_delivery_projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
