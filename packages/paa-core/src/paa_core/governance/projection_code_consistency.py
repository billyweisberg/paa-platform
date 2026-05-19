"""Projection-to-code consistency checks for governed PAA components."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, cast

from paa_core.db import DBSettings, run_psql, settings_from_profile, sql_literal

from .component_metadata import GovernedComponentMetadata
from .component_registry import COMPONENT_METADATA_BY_NAME


PROJECT_DELIVERY_PROJECTION_SURFACE = "paa.project_delivery_projections"


@dataclass(frozen=True)
class ProjectionCodeConsistencyComponentReport:
    component_name: str
    metadata_found: bool
    metadata_kind: str | None
    projection_surface_present: bool
    projected_row_count: int
    projected_plan_ids: tuple[str, ...]
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


def project_delivery_projection_surface_exists(*, settings: DBSettings | None = None) -> bool:
    sql = """
SELECT to_regclass('paa.project_delivery_projections') IS NOT NULL;
"""
    out = run_psql(sql, settings=settings).strip().lower()
    return out == "t"


def load_projection_truth(
    component_names: Iterable[str],
    *,
    settings: DBSettings | None = None,
) -> dict[str, tuple[int, tuple[str, ...]]]:
    unique_names = tuple(dict.fromkeys(name for name in component_names if name))
    if not unique_names:
        return {}
    if not project_delivery_projection_surface_exists(settings=settings):
        return {name: (0, ()) for name in unique_names}

    names_sql = ", ".join(sql_literal(name) for name in unique_names)
    sql = f"""
WITH requested(name) AS (
  SELECT unnest(ARRAY[{names_sql}]::text[])
)
SELECT row_to_json(t)
FROM (
  SELECT
    req.name AS component_name,
    COUNT(*)::int AS projected_row_count,
    COALESCE(
      ARRAY_REMOVE(ARRAY_AGG(DISTINCT pdp.implementation_plan_id::text), NULL),
      ARRAY[]::text[]
    ) AS projected_plan_ids
  FROM requested req
  LEFT JOIN paa.components c
    ON c.name = req.name
  LEFT JOIN paa.project_delivery_projections pdp
    ON pdp.primary_component_id = c.component_id
  GROUP BY req.name
  ORDER BY req.name
) t;
"""
    rows = _json_rows(sql, settings=settings)
    result: dict[str, tuple[int, tuple[str, ...]]] = {}
    for row in rows:
        component_name = str(row["component_name"])
        result[component_name] = (
            _as_int(row["projected_row_count"]),
            _as_str_tuple(row.get("projected_plan_ids")),
        )
    return result


def evaluate_projection_code_consistency(
    component_names: Iterable[str],
    *,
    projection_surface_present: bool,
    projection_truth: Mapping[str, tuple[int, tuple[str, ...]]] | None = None,
    component_registry: Mapping[str, GovernedComponentMetadata] | None = None,
) -> tuple[ProjectionCodeConsistencyComponentReport, ...]:
    unique_names = tuple(dict.fromkeys(name for name in component_names if name))
    truth = projection_truth or {}
    registry = component_registry if component_registry is not None else COMPONENT_METADATA_BY_NAME
    reports: list[ProjectionCodeConsistencyComponentReport] = []
    for component_name in unique_names:
        metadata = registry.get(component_name)
        projected_row_count, projected_plan_ids = truth.get(component_name, (0, ()))
        gaps: list[str] = []
        if metadata is None:
            gaps.append("missing_code_metadata")
        if not projection_surface_present:
            gaps.append("missing_project_delivery_projection_surface")
        elif projected_row_count == 0:
            gaps.append("missing_component_projection_rows")
        reports.append(
            ProjectionCodeConsistencyComponentReport(
                component_name=component_name,
                metadata_found=metadata is not None,
                metadata_kind=metadata.kind if metadata is not None else None,
                projection_surface_present=projection_surface_present,
                projected_row_count=projected_row_count,
                projected_plan_ids=projected_plan_ids,
                blocking_gaps=tuple(gaps),
            )
        )
    return tuple(reports)


def check_projection_code_consistency(
    component_names: Iterable[str],
    *,
    profile: str | None = None,
    settings: DBSettings | None = None,
    component_registry: Mapping[str, GovernedComponentMetadata] | None = None,
) -> tuple[ProjectionCodeConsistencyComponentReport, ...]:
    resolved_settings = settings if settings is not None else settings_from_profile(profile)
    surface_present = project_delivery_projection_surface_exists(settings=resolved_settings)
    truth = load_projection_truth(component_names, settings=resolved_settings)
    return evaluate_projection_code_consistency(
        component_names,
        projection_surface_present=surface_present,
        projection_truth=truth,
        component_registry=component_registry,
    )


def report_as_jsonable(report: ProjectionCodeConsistencyComponentReport) -> dict[str, object]:
    return asdict(report)


__all__ = [
    "PROJECT_DELIVERY_PROJECTION_SURFACE",
    "ProjectionCodeConsistencyComponentReport",
    "check_projection_code_consistency",
    "evaluate_projection_code_consistency",
    "load_projection_truth",
    "project_delivery_projection_surface_exists",
    "report_as_jsonable",
]
