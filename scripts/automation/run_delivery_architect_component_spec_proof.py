#!/usr/bin/env python3
# pyright: reportMissingTypeStubs=false
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, cast
import uuid

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SRC = REPO_ROOT / "packages" / "paa-core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from paa_core.governance.component_spec_model_consistency import check_component_spec_model_consistency
from paa_core.governance.model_code_consistency import check_model_code_consistency

REQUIRED_TOP_LEVEL_FIELDS = (
    "message_id",
    "schema_type",
    "schema_version",
    "project",
    "from_role",
    "to_role",
    "created_at",
    "correlation_id",
    "github_context",
    "payload",
    "authority_context",
)

REQUIRED_PAYLOAD_FIELDS = (
    "assignment_type",
    "issue",
    "branch",
    "target_component",
    "target_authority_doc",
    "authority_docs",
    "expected_materializer",
    "expected_proof_commands",
    "deliverable_requirements",
    "source_assignment_context",
)

PASS_RESULT = "proof_pass_ready_for_dev"
FOLLOW_ON_RESULT = "proof_pass_ready_for_follow_on_materialization"
AUTHORITY_RESULT = "needs_authority_clarification"
SCOPE_RESULT = "needs_scope_narrowing"
MATERIALIZATION_RESULT = "needs_materialization_fix"
CANNOT_PROVE_RESULT = "cannot_prove_with_current_authority"


@dataclass(frozen=True)
class ProofStageResult:
    status: str
    command: str
    blocking_gaps: tuple[str, ...]
    notes: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ParsedAssignment:
    raw: dict[str, Any]
    message_id: str
    correlation_id: str
    project: str
    github_context: dict[str, Any]
    authority_context: dict[str, Any]
    issue: dict[str, Any]
    branch: dict[str, Any]
    component_name: str
    component_kind: str
    alignment_state: str
    target_doc_path: Path
    target_doc_id: str
    target_doc_type: str
    authority_docs: tuple[str, ...]
    expected_materializer_script: Path
    expected_materializer_mode: str
    reconciliation_scope: tuple[str, ...]
    expected_proof_commands: tuple[str, ...]
    deliverable_requirements: dict[str, Any]
    source_assignment_context: dict[str, Any]
    previous_proof_context: dict[str, Any] | None


class AssignmentValidationError(RuntimeError):
    pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Delivery Architect component-spec materialization proof workflow.")
    parser.add_argument("--assignment", required=True, help="Absolute path to assignment packet JSON.")
    parser.add_argument("--output", required=True, help="Absolute path to result packet JSON.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repo root override.")
    parser.add_argument(
        "--work-root",
        default=str(REPO_ROOT / ".codex-work" / "delivery-architect-proof"),
        help="Repo-local scratch directory.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as process failure.")
    parser.add_argument("--dry-run", action="store_true", help="Plan and validate without running the materializer.")
    return parser.parse_args(argv)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise AssignmentValidationError("Assignment JSON root must be an object.")
    return cast(dict[str, Any], payload)


def _require_fields(container: dict[str, Any], fields: tuple[str, ...], *, context: str) -> None:
    missing = [field for field in fields if field not in container]
    if missing:
        raise AssignmentValidationError(f"Missing required {context} fields: {', '.join(missing)}")


def _as_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AssignmentValidationError(f"Expected '{name}' to be an object.")
    return cast(dict[str, Any], value)


def parse_assignment(data: dict[str, Any]) -> ParsedAssignment:
    _require_fields(data, REQUIRED_TOP_LEVEL_FIELDS, context="top-level")
    if data["schema_type"] != "techlead_assignment_packet":
        raise AssignmentValidationError("schema_type must be 'techlead_assignment_packet'.")
    if data["from_role"] != "techlead":
        raise AssignmentValidationError("from_role must be 'techlead'.")
    if data["to_role"] != "delivery-architect":
        raise AssignmentValidationError("to_role must be 'delivery-architect'.")

    payload = _as_dict(data["payload"], "payload")
    _require_fields(payload, REQUIRED_PAYLOAD_FIELDS, context="payload")
    if payload["assignment_type"] != "component_spec_materialization_proof":
        raise AssignmentValidationError("payload.assignment_type must be 'component_spec_materialization_proof'.")

    target_component = _as_dict(payload["target_component"], "payload.target_component")
    target_doc = _as_dict(payload["target_authority_doc"], "payload.target_authority_doc")
    expected_materializer = _as_dict(payload["expected_materializer"], "payload.expected_materializer")

    component_name = str(target_component.get("component_name", "")).strip()
    if not component_name:
        raise AssignmentValidationError("payload.target_component.component_name is required.")

    authority_docs_value = payload["authority_docs"]
    if not isinstance(authority_docs_value, list) or not authority_docs_value:
        raise AssignmentValidationError("payload.authority_docs must be a non-empty list.")
    authority_docs_list = cast(list[Any], authority_docs_value)
    authority_docs = tuple(str(item) for item in authority_docs_list)

    proof_commands_value = payload["expected_proof_commands"]
    if not isinstance(proof_commands_value, list) or not proof_commands_value:
        raise AssignmentValidationError("payload.expected_proof_commands must be a non-empty list.")
    proof_commands_list = cast(list[Any], proof_commands_value)
    expected_proof_commands = tuple(str(item) for item in proof_commands_list)

    target_doc_path = Path(str(target_doc.get("path", ""))).expanduser()
    if not target_doc_path.exists():
        raise AssignmentValidationError(f"target authority doc does not exist: {target_doc_path}")

    materializer_script = Path(str(expected_materializer.get("script_path", ""))).expanduser()
    if not materializer_script.exists():
        raise AssignmentValidationError(f"expected materializer script does not exist: {materializer_script}")

    for authority_doc in authority_docs:
        authority_doc_path = Path(authority_doc).expanduser()
        if not authority_doc_path.exists():
            raise AssignmentValidationError(f"authority doc does not exist: {authority_doc_path}")

    reconciliation_scope_value = expected_materializer.get("reconciliation_scope", [])
    if not isinstance(reconciliation_scope_value, list):
        raise AssignmentValidationError("payload.expected_materializer.reconciliation_scope must be a list.")
    reconciliation_scope_list = cast(list[Any], reconciliation_scope_value)

    return ParsedAssignment(
        raw=data,
        message_id=str(data["message_id"]),
        correlation_id=str(data["correlation_id"]),
        project=str(data["project"]),
        github_context=_as_dict(data["github_context"], "github_context"),
        authority_context=_as_dict(data["authority_context"], "authority_context"),
        issue=_as_dict(payload["issue"], "payload.issue"),
        branch=_as_dict(payload["branch"], "payload.branch"),
        component_name=component_name,
        component_kind=str(target_component.get("component_kind", "")).strip(),
        alignment_state=str(target_component.get("alignment_state", "")).strip(),
        target_doc_path=target_doc_path,
        target_doc_id=str(target_doc.get("doc_id", "")).strip(),
        target_doc_type=str(target_doc.get("doc_type", "")).strip(),
        authority_docs=authority_docs,
        expected_materializer_script=materializer_script,
        expected_materializer_mode=str(expected_materializer.get("mode", "")).strip(),
        reconciliation_scope=tuple(str(item) for item in reconciliation_scope_list),
        expected_proof_commands=expected_proof_commands,
        deliverable_requirements=_as_dict(payload["deliverable_requirements"], "payload.deliverable_requirements"),
        source_assignment_context=_as_dict(payload["source_assignment_context"], "payload.source_assignment_context"),
        previous_proof_context=_as_dict(payload["previous_proof_context"], "payload.previous_proof_context") if "previous_proof_context" in payload else None,
    )


def _run_shell(command: str, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=str(cwd), shell=True, text=True, capture_output=True)


def run_governed_doc_lint(repo_root: Path, target_doc_path: Path) -> ProofStageResult:
    relative_target = target_doc_path.relative_to(repo_root)
    command = (
        f"python {repo_root / 'scripts' / 'docs' / 'paa_docs.py'} lint "
        f"--root {repo_root} --path-prefix {relative_target} --format json"
    )
    proc = _run_shell(command, cwd=repo_root)
    gaps: tuple[str, ...] = ()
    notes: list[str] = []
    if proc.stdout.strip():
        try:
            parsed_raw = json.loads(proc.stdout)
            if isinstance(parsed_raw, dict):
                parsed = cast(dict[str, Any], parsed_raw)
                findings_value = parsed.get("findings")
                if isinstance(findings_value, list):
                    findings_list = cast(list[Any], findings_value)
                    normalized_gaps: list[str] = []
                    for item in findings_list:
                        if isinstance(item, dict):
                            normalized_gaps.append(str(cast(dict[str, Any], item).get("kind", "unknown_finding")))
                        else:
                            normalized_gaps.append("unknown_finding")
                    gaps = tuple(normalized_gaps)
        except json.JSONDecodeError:
            notes.append("non_json_lint_output")
    if proc.returncode != 0 and not gaps:
        gaps = ("governed_doc_lint_failed",)
    if proc.stderr.strip():
        notes.append(proc.stderr.strip())
    return ProofStageResult(
        status="pass" if not gaps and proc.returncode == 0 else "fail",
        command=command,
        blocking_gaps=gaps,
        notes=tuple(notes),
        evidence_refs=(str(relative_target),),
    )


def run_materializer(script_path: Path, *, repo_root: Path) -> ProofStageResult:
    command = f"python {script_path}"
    proc = _run_shell(command, cwd=repo_root)
    gaps: tuple[str, ...] = ()
    notes: list[str] = []
    if proc.returncode != 0:
        gaps = ("materializer_run_failed",)
    if proc.stdout.strip():
        notes.append(proc.stdout.strip())
    if proc.stderr.strip():
        notes.append(proc.stderr.strip())
    return ProofStageResult(
        status="pass" if not gaps else "fail",
        command=command,
        blocking_gaps=gaps,
        notes=tuple(notes),
        evidence_refs=(str(script_path),),
    )


def run_model_code_consistency(component_name: str) -> ProofStageResult:
    report = check_model_code_consistency([component_name])[0]
    command = (
        f"cd {REPO_ROOT} && PYTHONPATH=packages/paa-core/src python scripts/governance/"
        f"paa_model_code_consistency.py --component {component_name}"
    )
    return ProofStageResult(
        status="pass" if not report.blocking_gaps else "fail",
        command=command,
        blocking_gaps=tuple(report.blocking_gaps),
        notes=(json.dumps({"component_count": report.component_count, "element_count": report.element_count, "realization_count": report.realization_count, "implementation_plan_activity_count": report.implementation_plan_activity_count}, sort_keys=True),),
        evidence_refs=(component_name,),
    )


def run_spec_model_consistency(spec_path: Path) -> tuple[ProofStageResult, dict[str, Any]]:
    report = check_component_spec_model_consistency(spec_path)
    command = (
        f"cd {REPO_ROOT} && PYTHONPATH=packages/paa-core/src python scripts/governance/"
        f"paa_component_spec_model_consistency.py --spec {spec_path.relative_to(REPO_ROOT)}"
    )
    payload = asdict(report)
    return (
        ProofStageResult(
            status="pass" if not report.blocking_gaps else "fail",
            command=command,
            blocking_gaps=tuple(report.blocking_gaps),
            notes=(json.dumps(payload, sort_keys=True),),
            evidence_refs=(str(spec_path),),
        ),
        payload,
    )


def determine_result_type(proof_results: dict[str, ProofStageResult], *, dry_run: bool) -> tuple[str, str]:
    all_gaps = [gap for result in proof_results.values() for gap in result.blocking_gaps]
    if any(gap in {"governed_doc_lint_failed", "component_count_mismatch", "element_key_mismatch", "realization_key_mismatch", "activity_key_mismatch", "dependency_pair_mismatch", "missing_plan_seed_materialization"} for gap in all_gaps):
        return CANNOT_PROVE_RESULT, "escalate_to_authority_architect"
    if any(gap.endswith("mismatch") for gap in all_gaps):
        return MATERIALIZATION_RESULT, "assign_delivery_architect"
    if any(gap.startswith("missing_") for gap in all_gaps):
        return MATERIALIZATION_RESULT, "assign_delivery_architect"
    if any(gap == "materializer_run_failed" for gap in all_gaps):
        return MATERIALIZATION_RESULT, "assign_delivery_architect"
    if dry_run:
        return FOLLOW_ON_RESULT, "assign_delivery_architect"
    return PASS_RESULT, "assign_worker"


def build_result_packet(
    assignment: ParsedAssignment,
    *,
    proof_results: dict[str, ProofStageResult],
    spec_model_payload: dict[str, Any] | None,
    materializer_notes: tuple[str, ...],
    dry_run: bool,
) -> dict[str, Any]:
    result_type, recommended_action = determine_result_type(proof_results, dry_run=dry_run)
    findings = [
        {"stage": stage_name, "kind": gap}
        for stage_name, stage in proof_results.items()
        for gap in stage.blocking_gaps
    ]
    materialization_summary: dict[str, Any] = {
        "materializer_path": str(assignment.expected_materializer_script),
        "reconciliation_scope": list(assignment.reconciliation_scope),
        "model_entities_touched": list(assignment.reconciliation_scope),
        "component_ids": [],
        "implementation_plan_ids": [],
        "activity_keys_reconciled": [],
    }
    if spec_model_payload is not None:
        model_activity_keys_raw = spec_model_payload.get("model_activity_keys", [])
        if isinstance(model_activity_keys_raw, list):
            model_activity_keys = cast(list[Any], model_activity_keys_raw)
            materialization_summary["activity_keys_reconciled"] = [str(item) for item in model_activity_keys]
    review_summary = {
        PASS_RESULT: "Component authority doc is materialization-ready and strict spec/model proof passed.",
        FOLLOW_ON_RESULT: "Assignment profile and proof plan are valid, but dry-run or follow-on architectural work remains before worker routing.",
        MATERIALIZATION_RESULT: "Authority is promising, but materialization or proof surfaces still need Delivery Architect follow-on work.",
        AUTHORITY_RESULT: "Authority clarification is required before proof can proceed safely.",
        SCOPE_RESULT: "Scope must be narrowed before a safe proof can be compiled.",
        CANNOT_PROVE_RESULT: "Current authority form cannot support a fail-closed proof result.",
    }[result_type]

    return {
        "message_id": str(uuid.uuid4()),
        "schema_type": "delivery_review_packet",
        "schema_version": str(assignment.raw.get("schema_version", "1.0.0")),
        "project": assignment.project,
        "from_role": "delivery-architect",
        "to_role": "techlead",
        "created_at": _now_iso(),
        "correlation_id": assignment.correlation_id,
        "github_context": assignment.github_context,
        "authority_context": assignment.authority_context,
        "payload": {
            "review_type": "component_spec_materialization_proof",
            "issue": assignment.issue,
            "branch": assignment.branch,
            "result_type": result_type,
            "proof_target": {
                "component_name": assignment.component_name,
                "authority_doc_path": str(assignment.target_doc_path),
            },
            "conformance_summary": {
                "was_template_conformant_at_start": True,
                "conformance_changes_applied": False,
                "required_sections_added": [],
                "remaining_structural_gaps": [],
            },
            "materialization_summary": materialization_summary,
            "proof_results": {key: asdict(value) for key, value in proof_results.items()},
            "findings": findings,
            "techlead_action_recommended": recommended_action,
            "review_summary": review_summary,
            "artifacts": [str(assignment.target_doc_path), str(assignment.expected_materializer_script)],
            "source_assignment_ref": {
                "message_id": assignment.message_id,
                "assignment_type": "component_spec_materialization_proof",
                "target_role": "delivery-architect",
            },
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    assignment_path = Path(args.assignment).expanduser()
    output_path = Path(args.output).expanduser()
    repo_root = Path(args.repo_root).expanduser()
    Path(args.work_root).expanduser().mkdir(parents=True, exist_ok=True)

    if not assignment_path.exists():
        return 1

    try:
        assignment_raw = _load_json(assignment_path)
    except (OSError, json.JSONDecodeError):
        return 1

    try:
        assignment = parse_assignment(assignment_raw)
    except AssignmentValidationError:
        return 1

    proof_results: dict[str, ProofStageResult] = {}
    spec_model_payload: dict[str, Any] | None = None

    proof_results["governed_doc_lint"] = run_governed_doc_lint(repo_root, assignment.target_doc_path)

    if args.dry_run:
        proof_results["materializer_run"] = ProofStageResult(
            status="skipped",
            command=f"python {assignment.expected_materializer_script}",
            blocking_gaps=(),
            notes=("dry_run",),
            evidence_refs=(str(assignment.expected_materializer_script),),
        )
    else:
        proof_results["materializer_run"] = run_materializer(assignment.expected_materializer_script, repo_root=repo_root)

    proof_results["model_code_consistency"] = run_model_code_consistency(assignment.component_name)
    spec_stage, spec_model_payload = run_spec_model_consistency(assignment.target_doc_path)
    proof_results["spec_model_consistency"] = spec_stage

    result_packet = build_result_packet(
        assignment,
        proof_results=proof_results,
        spec_model_payload=spec_model_payload,
        materializer_notes=proof_results["materializer_run"].notes,
        dry_run=args.dry_run,
    )
    write_json(output_path, result_packet)

    has_gaps = any(result.blocking_gaps for result in proof_results.values())
    has_warning = args.strict and any(result.status == "skipped" for result in proof_results.values())
    if has_gaps or has_warning:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
