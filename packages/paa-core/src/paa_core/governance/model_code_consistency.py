"""Model-to-code consistency checks for governed PAA components."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, cast

from paa_core.db import DBSettings, run_psql, settings_from_profile, sql_literal

from .component_metadata import GovernedComponentMetadata
from .component_registry import COMPONENT_METADATA_BY_NAME


@dataclass(frozen=True)
class ModelComponentTruthSnapshot:
    component_name: str
    component_count: int
    component_ids: tuple[str, ...]
    project_ids: tuple[str, ...]
    element_count: int
    realization_count: int
    implementation_plan_activity_count: int


@dataclass(frozen=True)
class ModelCodeConsistencyComponentReport:
    component_name: str
    metadata_found: bool
    metadata_kind: str | None
    metadata_alignment: str | None
    component_count: int
    component_ids: tuple[str, ...]
    project_ids: tuple[str, ...]
    element_count: int
    realization_count: int
    implementation_plan_activity_count: int
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


def _as_str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        items = cast(list[object], value)
        return tuple("" if item is None else str(item) for item in items)
    raise TypeError(f"Expected list-compatible value, got {type(value).__name__}")


def load_model_component_truth(
    component_names: Iterable[str],
    *,
    settings: DBSettings | None = None,
) -> dict[str, ModelComponentTruthSnapshot]:
    unique_names = tuple(dict.fromkeys(name for name in component_names if name))
    if not unique_names:
        return {}
    names_sql = ", ".join(sql_literal(name) for name in unique_names)
    sql = f"""
WITH requested(name) AS (
  SELECT unnest(ARRAY[{names_sql}]::text[])
),
component_rows AS (
  SELECT
    req.name AS component_name,
    c.component_id::text AS component_id,
    c.project_id::text AS project_id
  FROM requested req
  LEFT JOIN paa.components c
    ON c.name = req.name
),
element_rows AS (
  SELECT
    cr.component_name,
    ce.component_element_id::text AS component_element_id
  FROM component_rows cr
  LEFT JOIN paa.component_elements ce
    ON ce.component_id::uuid = cr.component_id::uuid
),
realization_rows AS (
  SELECT
    cr.component_name,
    cer.component_element_realization_id::text AS component_element_realization_id
  FROM component_rows cr
  LEFT JOIN paa.component_element_realizations cer
    ON cer.component_id::uuid = cr.component_id::uuid
),
activity_rows AS (
  SELECT DISTINCT
    cr.component_name,
    ipa.implementation_plan_activity_id::text AS implementation_plan_activity_id
  FROM component_rows cr
  LEFT JOIN paa.component_elements ce
    ON ce.component_id::uuid = cr.component_id::uuid
  LEFT JOIN paa.component_element_realizations cer
    ON cer.component_id::uuid = cr.component_id::uuid
  LEFT JOIN paa.implementation_plan_activities ipa
    ON ipa.component_element_id = ce.component_element_id
    OR ipa.component_element_realization_id = cer.component_element_realization_id
)
SELECT row_to_json(t)
FROM (
  SELECT
    req.name AS component_name,
    COUNT(DISTINCT cr.component_id) AS component_count,
    COALESCE(
      ARRAY_REMOVE(ARRAY_AGG(DISTINCT cr.component_id), NULL),
      ARRAY[]::text[]
    ) AS component_ids,
    COALESCE(
      ARRAY_REMOVE(ARRAY_AGG(DISTINCT cr.project_id), NULL),
      ARRAY[]::text[]
    ) AS project_ids,
    COUNT(DISTINCT er.component_element_id) AS element_count,
    COUNT(DISTINCT rr.component_element_realization_id) AS realization_count,
    COUNT(DISTINCT ar.implementation_plan_activity_id) AS implementation_plan_activity_count
  FROM requested req
  LEFT JOIN component_rows cr
    ON cr.component_name = req.name
  LEFT JOIN element_rows er
    ON er.component_name = req.name
  LEFT JOIN realization_rows rr
    ON rr.component_name = req.name
  LEFT JOIN activity_rows ar
    ON ar.component_name = req.name
  GROUP BY req.name
  ORDER BY req.name
) t;
"""
    rows = _json_rows(sql, settings=settings)
    snapshots: dict[str, ModelComponentTruthSnapshot] = {}
    for row in rows:
        component_name = str(row["component_name"])
        snapshots[component_name] = ModelComponentTruthSnapshot(
            component_name=component_name,
            component_count=_as_int(row["component_count"]),
            component_ids=_as_str_tuple(row.get("component_ids")),
            project_ids=_as_str_tuple(row.get("project_ids")),
            element_count=_as_int(row["element_count"]),
            realization_count=_as_int(row["realization_count"]),
            implementation_plan_activity_count=_as_int(row["implementation_plan_activity_count"]),
        )
    return snapshots


def evaluate_model_code_consistency(
    component_names: Iterable[str],
    *,
    component_registry: Mapping[str, GovernedComponentMetadata] | None = None,
    model_truth: Mapping[str, ModelComponentTruthSnapshot] | None = None,
) -> tuple[ModelCodeConsistencyComponentReport, ...]:
    unique_names = tuple(dict.fromkeys(name for name in component_names if name))
    registry = component_registry if component_registry is not None else COMPONENT_METADATA_BY_NAME
    snapshots = model_truth or {}
    reports: list[ModelCodeConsistencyComponentReport] = []
    for component_name in unique_names:
        metadata = registry.get(component_name)
        snapshot = snapshots.get(
            component_name,
            ModelComponentTruthSnapshot(
                component_name=component_name,
                component_count=0,
                component_ids=(),
                project_ids=(),
                element_count=0,
                realization_count=0,
                implementation_plan_activity_count=0,
            ),
        )
        gaps: list[str] = []
        if metadata is None:
            gaps.append("missing_code_metadata")
        if snapshot.component_count == 0:
            gaps.append("missing_model_component")
        elif snapshot.component_count > 1:
            gaps.append("ambiguous_model_component")
        if snapshot.element_count == 0:
            gaps.append("missing_component_elements")
        if snapshot.realization_count == 0:
            gaps.append("missing_component_realizations")
        if snapshot.implementation_plan_activity_count == 0:
            gaps.append("missing_implementation_plan_activities")
        reports.append(
            ModelCodeConsistencyComponentReport(
                component_name=component_name,
                metadata_found=metadata is not None,
                metadata_kind=metadata.kind if metadata is not None else None,
                metadata_alignment=metadata.alignment if metadata is not None else None,
                component_count=snapshot.component_count,
                component_ids=snapshot.component_ids,
                project_ids=snapshot.project_ids,
                element_count=snapshot.element_count,
                realization_count=snapshot.realization_count,
                implementation_plan_activity_count=snapshot.implementation_plan_activity_count,
                blocking_gaps=tuple(gaps),
            )
        )
    return tuple(reports)


def check_model_code_consistency(
    component_names: Iterable[str],
    *,
    profile: str | None = None,
    settings: DBSettings | None = None,
    component_registry: Mapping[str, GovernedComponentMetadata] | None = None,
) -> tuple[ModelCodeConsistencyComponentReport, ...]:
    resolved_settings = settings if settings is not None else settings_from_profile(profile)
    snapshots = load_model_component_truth(component_names, settings=resolved_settings)
    return evaluate_model_code_consistency(
        component_names,
        component_registry=component_registry,
        model_truth=snapshots,
    )


def report_as_jsonable(report: ModelCodeConsistencyComponentReport) -> dict[str, object]:
    return asdict(report)


__all__ = [
    "ModelCodeConsistencyComponentReport",
    "ModelComponentTruthSnapshot",
    "check_model_code_consistency",
    "evaluate_model_code_consistency",
    "load_model_component_truth",
    "report_as_jsonable",
]
