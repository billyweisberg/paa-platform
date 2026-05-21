"""Compare extracted component-spec structure against reconciled model truth."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Any, cast

from paa_core.db import DBSettings, run_psql, settings_from_profile, sql_literal

from .component_spec_materialization import (
    ComponentSpecMaterializationSeed,
    extract_component_spec_materialization_seed,
)


@dataclass(frozen=True)
class ComponentSpecModelConsistencyReport:
    source_path: str
    component_name: str
    expected_component_count: int
    model_component_count: int
    expected_element_count: int
    model_element_count: int
    expected_realization_count: int
    model_realization_count: int
    expected_activity_count: int
    model_activity_count: int
    expected_dependency_count: int
    model_dependency_count: int
    expected_element_keys: tuple[str, ...]
    model_element_keys: tuple[str, ...]
    expected_realization_keys: tuple[str, ...]
    model_realization_keys: tuple[str, ...]
    expected_activity_keys: tuple[str, ...]
    model_activity_keys: tuple[str, ...]
    expected_dependency_pairs: tuple[str, ...]
    model_dependency_pairs: tuple[str, ...]
    plan_name: str
    plan_present: bool
    blocking_gaps: tuple[str, ...]


@dataclass(frozen=True)
class _ModelComponentDetail:
    component_count: int
    element_count: int
    realization_count: int
    activity_count: int
    dependency_count: int
    plan_present: bool
    model_element_keys: tuple[str, ...]
    model_realization_keys: tuple[str, ...]
    model_activity_keys: tuple[str, ...]
    model_dependency_pairs: tuple[str, ...]


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
        return tuple(str(item) for item in items)
    raise TypeError(f"Expected list-compatible value, got {type(value).__name__}")


def _load_model_detail(
    component_name: str,
    plan_name: str,
    *,
    settings: DBSettings | None = None,
) -> _ModelComponentDetail:
    sql = f"""
WITH target_component AS (
  SELECT c.component_id, c.name
  FROM paa.components c
  WHERE c.name = {sql_literal(component_name)}
),
target_plan AS (
  SELECT ip.implementation_plan_id
  FROM paa.implementation_plans ip
  JOIN target_component tc ON tc.component_id = ip.primary_component_id
  WHERE ip.plan_id_external = {sql_literal(plan_name)}
),
element_keys AS (
  SELECT DISTINCT ce.element_key
  FROM paa.component_elements ce
  JOIN target_component tc ON tc.component_id = ce.component_id
),
realization_keys AS (
  SELECT DISTINCT cer.realization_key
  FROM paa.component_element_realizations cer
  JOIN target_component tc ON tc.component_id = cer.component_id
),
activity_keys AS (
  SELECT DISTINCT ipa.activity_key
  FROM paa.implementation_plan_activities ipa
  JOIN target_plan tp ON tp.implementation_plan_id = ipa.implementation_plan_id
),
dependency_pairs AS (
  SELECT DISTINCT pred.activity_key || '->' || succ.activity_key AS dependency_pair
  FROM paa.implementation_plan_activity_dependencies ipad
  JOIN target_plan tp ON tp.implementation_plan_id = ipad.implementation_plan_id
  JOIN paa.implementation_plan_activities pred ON pred.implementation_plan_activity_id = ipad.predecessor_activity_id
  JOIN paa.implementation_plan_activities succ ON succ.implementation_plan_activity_id = ipad.successor_activity_id
)
SELECT row_to_json(t)
FROM (
  SELECT
    (SELECT COUNT(*) FROM target_component) AS component_count,
    (SELECT COUNT(*) FROM element_keys) AS element_count,
    (SELECT COUNT(*) FROM realization_keys) AS realization_count,
    (SELECT COUNT(*) FROM activity_keys) AS activity_count,
    (SELECT COUNT(*) FROM dependency_pairs) AS dependency_count,
    EXISTS (SELECT 1 FROM target_plan) AS plan_present,
    COALESCE((SELECT array_agg(element_key ORDER BY element_key) FROM element_keys), ARRAY[]::text[]) AS model_element_keys,
    COALESCE((SELECT array_agg(realization_key ORDER BY realization_key) FROM realization_keys), ARRAY[]::text[]) AS model_realization_keys,
    COALESCE((SELECT array_agg(activity_key ORDER BY activity_key) FROM activity_keys), ARRAY[]::text[]) AS model_activity_keys,
    COALESCE((SELECT array_agg(dependency_pair ORDER BY dependency_pair) FROM dependency_pairs), ARRAY[]::text[]) AS model_dependency_pairs
) t;
"""
    rows = _json_rows(sql, settings=settings)
    if not rows:
        return _ModelComponentDetail(0, 0, 0, 0, 0, False, (), (), (), ())
    row = rows[0]
    return _ModelComponentDetail(
        component_count=_as_int(row["component_count"]),
        element_count=_as_int(row["element_count"]),
        realization_count=_as_int(row["realization_count"]),
        activity_count=_as_int(row["activity_count"]),
        dependency_count=_as_int(row["dependency_count"]),
        plan_present=bool(row["plan_present"]),
        model_element_keys=_as_str_tuple(row.get("model_element_keys")),
        model_realization_keys=_as_str_tuple(row.get("model_realization_keys")),
        model_activity_keys=_as_str_tuple(row.get("model_activity_keys")),
        model_dependency_pairs=_as_str_tuple(row.get("model_dependency_pairs")),
    )


def evaluate_component_spec_model_consistency(
    seed: ComponentSpecMaterializationSeed,
    *,
    settings: DBSettings | None = None,
) -> ComponentSpecModelConsistencyReport:
    detail = _load_model_detail(
        seed.component_identity.component_name,
        seed.plan_seed.plan_name,
        settings=settings,
    )

    expected_element_keys = tuple(sorted(element.element_name for element in seed.component_elements))
    expected_realization_keys = tuple(sorted(realization.realization_key for realization in seed.realizations))
    expected_activity_keys = tuple(sorted(activity.activity_key for activity in seed.activity_seeds))
    expected_dependency_pairs = tuple(
        sorted(f"{dependency.depends_on_activity_key}->{dependency.activity_key}" for dependency in seed.activity_dependencies)
    )

    gaps: list[str] = []
    if detail.component_count != 1:
        gaps.append("component_count_mismatch")
    if detail.element_count != len(seed.component_elements):
        gaps.append("element_count_mismatch")
    if detail.realization_count != len(seed.realizations):
        gaps.append("realization_count_mismatch")
    if detail.activity_count != len(seed.activity_seeds):
        gaps.append("activity_count_mismatch")
    if detail.dependency_count != len(seed.activity_dependencies):
        gaps.append("dependency_count_mismatch")
    if not detail.plan_present:
        gaps.append("missing_plan_seed_materialization")
    if detail.model_element_keys != expected_element_keys:
        gaps.append("element_key_mismatch")
    if detail.model_realization_keys != expected_realization_keys:
        gaps.append("realization_key_mismatch")
    if detail.model_activity_keys != expected_activity_keys:
        gaps.append("activity_key_mismatch")
    if detail.model_dependency_pairs != expected_dependency_pairs:
        gaps.append("dependency_pair_mismatch")

    return ComponentSpecModelConsistencyReport(
        source_path=seed.source_path,
        component_name=seed.component_identity.component_name,
        expected_component_count=1,
        model_component_count=detail.component_count,
        expected_element_count=len(seed.component_elements),
        model_element_count=detail.element_count,
        expected_realization_count=len(seed.realizations),
        model_realization_count=detail.realization_count,
        expected_activity_count=len(seed.activity_seeds),
        model_activity_count=detail.activity_count,
        expected_dependency_count=len(seed.activity_dependencies),
        model_dependency_count=detail.dependency_count,
        expected_element_keys=expected_element_keys,
        model_element_keys=detail.model_element_keys,
        expected_realization_keys=expected_realization_keys,
        model_realization_keys=detail.model_realization_keys,
        expected_activity_keys=expected_activity_keys,
        model_activity_keys=detail.model_activity_keys,
        expected_dependency_pairs=expected_dependency_pairs,
        model_dependency_pairs=detail.model_dependency_pairs,
        plan_name=seed.plan_seed.plan_name,
        plan_present=detail.plan_present,
        blocking_gaps=tuple(gaps),
    )


def check_component_spec_model_consistency(
    spec_path: str | Path,
    *,
    profile: str | None = None,
    settings: DBSettings | None = None,
) -> ComponentSpecModelConsistencyReport:
    resolved_settings = settings if settings is not None else settings_from_profile(profile)
    seed = extract_component_spec_materialization_seed(spec_path)
    return evaluate_component_spec_model_consistency(seed, settings=resolved_settings)


def report_as_jsonable(report: ComponentSpecModelConsistencyReport) -> dict[str, Any]:
    return asdict(report)


__all__ = [
    "ComponentSpecModelConsistencyReport",
    "check_component_spec_model_consistency",
    "evaluate_component_spec_model_consistency",
    "report_as_jsonable",
]
