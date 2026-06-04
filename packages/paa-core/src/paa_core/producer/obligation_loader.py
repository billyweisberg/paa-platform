"""Materialize verification obligations from stage1 design package artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any

from paa_core.runtime.support.config import ProducerProjectConfig
from paa_core.db import run_psql, sql_literal


OBLIGATION_SPECS = {
    "ruff": {
        "suffix": "lint",
        "verification_type": "tooling",
        "method": "uv run ruff check .",
        "pass_criteria": "command exits successfully",
    },
    "mypy": {
        "suffix": "types",
        "verification_type": "tooling",
        "method": "uv run mypy src",
        "pass_criteria": "command exits successfully",
    },
    "pytest": {
        "suffix": "tests",
        "verification_type": "test",
        "method": "uv run --extra dev pytest -q",
        "pass_criteria": "all tests pass",
    },
    "10,000-step trace": {
        "suffix": "trace",
        "verification_type": "trace",
        "method": "10,000-step trace run",
        "pass_criteria": "49 goals",
    },
    "checkpoint parity": {
        "suffix": "parity",
        "verification_type": "parity",
        "method": "checkpoint parity comparison",
        "pass_criteria": "pass with 0 failed and 0 warnings",
    },
    "benchmark": {
        "suffix": "benchmark",
        "verification_type": "artifact",
        "method": "10,000-step benchmark run",
        "pass_criteria": "49 goals",
    },
    "scope review": {
        "suffix": "scope",
        "verification_type": "qa_review",
    },
}


@dataclass(frozen=True)
class ObligationRow:
    verification_key: str
    verification_type: str
    method: str
    pass_criteria: str
    metadata_json: dict[str, Any]


def _slugify(value: str) -> str:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value)
    text = text.replace("_", "-")
    text = re.sub(r"[^a-zA-Z0-9-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text.lower()


def _derive_issue_slug_from_path(path: Path, issue_number: int) -> str:
    stem = path.stem
    marker = f"issue{issue_number}."
    if marker in stem:
        return _slugify(stem.split(marker, 1)[1])
    return _slugify(stem)


def _derive_scope_label(package: dict[str, Any], issue_slug: str) -> str:
    implementation_target = package.get("implementation_target") or {}
    target_id = implementation_target.get("implementation_target_id")
    if isinstance(target_id, str) and target_id:
        target_slug = target_id.removeprefix("impl-")
        target_slug = re.sub(r"-issue\d+$", "", target_slug)
        if target_slug:
            return target_slug
    return issue_slug


def _find_stage1_package_path(
    *,
    repo_root: Path,
    config: ProducerProjectConfig,
    issue_number: int,
) -> Path:
    candidates = []
    for raw in config.artifact_paths:
        if f"stage1_design_package.issue{issue_number}." not in raw:
            continue
        candidate = (repo_root / raw).resolve()
        if candidate.exists():
            candidates.append(candidate)
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(f"No stage1 design package artifact found for issue #{issue_number}")
    raise RuntimeError(f"Multiple stage1 design package artifacts found for issue #{issue_number}: {candidates}")


def load_stage1_package(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def build_obligation_rows(
    *,
    issue_number: int,
    package: dict[str, Any],
    verification_key_prefix: str | None = None,
    scope_authority_label: str | None = None,
) -> list[ObligationRow]:
    basis = package.get("verification_contract_basis") or {}
    obligations = basis.get("verification_obligations") or []
    if not obligations:
        raise RuntimeError("Stage1 package has no verification_contract_basis.verification_obligations")

    issue_slug = verification_key_prefix or _slugify(
        (package.get("component_model_slice") or {}).get("primary_component", f"issue{issue_number}")
    )
    scope_label = scope_authority_label or _derive_scope_label(package, issue_slug)
    rows: list[ObligationRow] = []
    for obligation_name in obligations:
        spec = OBLIGATION_SPECS.get(obligation_name)
        if spec is None:
            raise RuntimeError(f"Unsupported verification obligation '{obligation_name}'")
        suffix = spec["suffix"]
        verification_type = spec["verification_type"]
        if verification_type == "qa_review":
            method = f"QA scope review against {scope_label} authority"
            pass_criteria = f"slice stays within the {scope_label} authority"
        else:
            method = spec["method"]
            pass_criteria = spec["pass_criteria"]
        rows.append(
            ObligationRow(
                verification_key=f"ver-{issue_slug}-issue{issue_number}-{suffix}",
                verification_type=verification_type,
                method=method,
                pass_criteria=pass_criteria,
                metadata_json={
                    "real_slice": True,
                    "issue_number": issue_number,
                    "source": "paa-producer materialize-verification-obligations",
                    "package_id": package.get("package_id"),
                },
            )
        )
    return rows


def materialize_verification_obligations(
    *,
    repo_root: Path,
    config: ProducerProjectConfig | None,
    issue_number: int,
    package_path: Path | None = None,
    verification_key_prefix: str | None = None,
    scope_authority_label: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    if package_path is not None:
        resolved_package_path = package_path
    else:
        if config is None:
            raise ValueError("config is required when package_path is not provided")
        resolved_package_path = _find_stage1_package_path(
            repo_root=repo_root,
            config=config,
            issue_number=issue_number,
        )
    package = load_stage1_package(resolved_package_path)
    default_issue_slug = _derive_issue_slug_from_path(resolved_package_path, issue_number)
    rows = build_obligation_rows(
        issue_number=issue_number,
        package=package,
        verification_key_prefix=verification_key_prefix or default_issue_slug,
        scope_authority_label=scope_authority_label,
    )

    if not dry_run:
        statements = []
        for row in rows:
            statements.append(
                f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug='fractal-core-python'
), wi AS (
  SELECT wi.work_item_id
  FROM paa.work_items wi
  JOIN project p ON p.project_id = wi.project_id
  WHERE wi.issue_number = {sql_literal(issue_number)}
  LIMIT 1
)
INSERT INTO paa.verification_obligations (
  project_id, work_item_id, verification_key, verification_type, method, pass_criteria, required_for_acceptance, status, metadata_json
)
SELECT
  project.project_id,
  wi.work_item_id,
  {sql_literal(row.verification_key)},
  {sql_literal(row.verification_type)}::paa.verification_type,
  {sql_literal(row.method)},
  {sql_literal(row.pass_criteria)},
  true,
  'required'::paa.verification_status,
  {sql_literal(json.dumps(row.metadata_json))}::jsonb
FROM project, wi
WHERE NOT EXISTS (
  SELECT 1 FROM paa.verification_obligations vo
  WHERE vo.work_item_id = wi.work_item_id
    AND vo.verification_key = {sql_literal(row.verification_key)}
);
""".strip()
            )
        run_psql("BEGIN;\n" + "\n".join(statements) + "\nCOMMIT;\n")

    return {
        "issue_number": issue_number,
        "package_path": str(resolved_package_path),
        "package_id": package.get("package_id"),
        "verification_key_prefix": verification_key_prefix or default_issue_slug,
        "scope_authority_label": scope_authority_label or _derive_scope_label(package, default_issue_slug),
        "obligations": [
            {
                "verification_key": row.verification_key,
                "verification_type": row.verification_type,
                "method": row.method,
                "pass_criteria": row.pass_criteria,
                "metadata_json": row.metadata_json,
            }
            for row in rows
        ],
        "dry_run": dry_run,
    }
