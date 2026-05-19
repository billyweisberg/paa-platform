"""Runtime-evidence to model consistency checks for governed PAA components."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from paa_core.db import DBSettings, run_psql, settings_from_profile, sql_literal

from .component_metadata import GovernedComponentMetadata
from .component_registry import COMPONENT_METADATA_BY_NAME


@dataclass(frozen=True)
class RuntimeEvidenceConsistencyComponentReport:
    component_name: str
    metadata_found: bool
    metadata_kind: str | None
    implementation_plan_id: str | None
    work_item_id: str | None
    workflow_state_count: int
    workflow_transition_count: int
    handoff_count: int
    automation_run_count: int
    execution_record_count: int
    blocking_gaps: tuple[str, ...]


def _json_rows(sql: str, *, settings: DBSettings | None = None) -> list[dict[str, object]]:
    output = run_psql(sql, settings=settings)
    rows: list[dict[str, object]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, str)):
        return int(value)
    raise TypeError(f"Expected int-compatible value, got {type(value).__name__}")


def _as_str_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def load_runtime_evidence_truth(
    component_names: Iterable[str],
    *,
    settings: DBSettings | None = None,
) -> dict[str, RuntimeEvidenceConsistencyComponentReport]:
    unique_names = tuple(dict.fromkeys(name for name in component_names if name))
    if not unique_names:
        return {}
    names_sql = ", ".join(sql_literal(name) for name in unique_names)
    sql = f"""
WITH requested(name) AS (
  SELECT unnest(ARRAY[{names_sql}]::text[])
),
component_plan AS (
  SELECT
    req.name AS component_name,
    ip.implementation_plan_id::text AS implementation_plan_id,
    ip.work_item_id::text AS work_item_id
  FROM requested req
  LEFT JOIN paa.components c
    ON c.name = req.name
  LEFT JOIN paa.implementation_plans ip
    ON ip.primary_component_id = c.component_id
),
evidence_counts AS (
  SELECT
    cp.component_name,
    cp.implementation_plan_id,
    cp.work_item_id,
    COUNT(DISTINCT ws.workflow_state_id) AS workflow_state_count,
    COUNT(DISTINCT wt.workflow_transition_id) AS workflow_transition_count,
    COUNT(DISTINCT h.handoff_id) AS handoff_count,
    COUNT(DISTINCT ar.automation_run_id) AS automation_run_count,
    COUNT(DISTINCT er.execution_record_id) AS execution_record_count
  FROM component_plan cp
  LEFT JOIN paa.workflow_states ws
    ON ws.work_item_id::text = cp.work_item_id
  LEFT JOIN paa.workflow_transitions wt
    ON wt.work_item_id::text = cp.work_item_id
  LEFT JOIN paa.handoffs h
    ON h.work_item_id::text = cp.work_item_id
  LEFT JOIN paa.automation_runs ar
    ON ar.work_item_id::text = cp.work_item_id
  LEFT JOIN paa.execution_records er
    ON er.work_item_id::text = cp.work_item_id
  GROUP BY cp.component_name, cp.implementation_plan_id, cp.work_item_id
)
SELECT row_to_json(t)
FROM (
  SELECT
    req.name AS component_name,
    ec.implementation_plan_id,
    ec.work_item_id,
    COALESCE(ec.workflow_state_count, 0) AS workflow_state_count,
    COALESCE(ec.workflow_transition_count, 0) AS workflow_transition_count,
    COALESCE(ec.handoff_count, 0) AS handoff_count,
    COALESCE(ec.automation_run_count, 0) AS automation_run_count,
    COALESCE(ec.execution_record_count, 0) AS execution_record_count
  FROM requested req
  LEFT JOIN evidence_counts ec
    ON ec.component_name = req.name
  ORDER BY req.name
) t;
"""
    rows = _json_rows(sql, settings=settings)
    result: dict[str, RuntimeEvidenceConsistencyComponentReport] = {}
    for row in rows:
        component_name = str(row["component_name"])
        result[component_name] = RuntimeEvidenceConsistencyComponentReport(
            component_name=component_name,
            metadata_found=False,
            metadata_kind=None,
            implementation_plan_id=_as_str_or_none(row.get("implementation_plan_id")),
            work_item_id=_as_str_or_none(row.get("work_item_id")),
            workflow_state_count=_as_int(row["workflow_state_count"]),
            workflow_transition_count=_as_int(row["workflow_transition_count"]),
            handoff_count=_as_int(row["handoff_count"]),
            automation_run_count=_as_int(row["automation_run_count"]),
            execution_record_count=_as_int(row["execution_record_count"]),
            blocking_gaps=(),
        )
    return result


def evaluate_runtime_evidence_model_consistency(
    component_names: Iterable[str],
    *,
    runtime_truth: Mapping[str, RuntimeEvidenceConsistencyComponentReport] | None = None,
    component_registry: Mapping[str, GovernedComponentMetadata] | None = None,
) -> tuple[RuntimeEvidenceConsistencyComponentReport, ...]:
    unique_names = tuple(dict.fromkeys(name for name in component_names if name))
    truth = runtime_truth or {}
    registry = component_registry if component_registry is not None else COMPONENT_METADATA_BY_NAME
    reports: list[RuntimeEvidenceConsistencyComponentReport] = []
    for component_name in unique_names:
        metadata = registry.get(component_name)
        snapshot = truth.get(
            component_name,
            RuntimeEvidenceConsistencyComponentReport(
                component_name=component_name,
                metadata_found=False,
                metadata_kind=None,
                implementation_plan_id=None,
                work_item_id=None,
                workflow_state_count=0,
                workflow_transition_count=0,
                handoff_count=0,
                automation_run_count=0,
                execution_record_count=0,
                blocking_gaps=(),
            ),
        )
        gaps: list[str] = []
        if metadata is None:
            gaps.append("missing_code_metadata")
        if snapshot.implementation_plan_id is None:
            gaps.append("missing_component_plan_link")
        if snapshot.work_item_id is None:
            gaps.append("missing_component_work_item_link")
        if snapshot.workflow_state_count == 0:
            gaps.append("missing_workflow_state_evidence")
        if snapshot.workflow_transition_count == 0:
            gaps.append("missing_workflow_transition_evidence")
        if snapshot.handoff_count == 0:
            gaps.append("missing_handoff_evidence")
        if snapshot.automation_run_count == 0:
            gaps.append("missing_automation_run_evidence")
        if snapshot.execution_record_count == 0:
            gaps.append("missing_execution_record_evidence")
        reports.append(
            RuntimeEvidenceConsistencyComponentReport(
                component_name=component_name,
                metadata_found=metadata is not None,
                metadata_kind=metadata.kind if metadata is not None else None,
                implementation_plan_id=snapshot.implementation_plan_id,
                work_item_id=snapshot.work_item_id,
                workflow_state_count=snapshot.workflow_state_count,
                workflow_transition_count=snapshot.workflow_transition_count,
                handoff_count=snapshot.handoff_count,
                automation_run_count=snapshot.automation_run_count,
                execution_record_count=snapshot.execution_record_count,
                blocking_gaps=tuple(gaps),
            )
        )
    return tuple(reports)


def check_runtime_evidence_model_consistency(
    component_names: Iterable[str],
    *,
    profile: str | None = None,
    settings: DBSettings | None = None,
    component_registry: Mapping[str, GovernedComponentMetadata] | None = None,
) -> tuple[RuntimeEvidenceConsistencyComponentReport, ...]:
    resolved_settings = settings if settings is not None else settings_from_profile(profile)
    truth = load_runtime_evidence_truth(component_names, settings=resolved_settings)
    return evaluate_runtime_evidence_model_consistency(
        component_names,
        runtime_truth=truth,
        component_registry=component_registry,
    )


def report_as_jsonable(report: RuntimeEvidenceConsistencyComponentReport) -> dict[str, object]:
    return asdict(report)


__all__ = [
    "RuntimeEvidenceConsistencyComponentReport",
    "check_runtime_evidence_model_consistency",
    "evaluate_runtime_evidence_model_consistency",
    "load_runtime_evidence_truth",
    "report_as_jsonable",
]
