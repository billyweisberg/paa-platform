"""Runtime evidence persistence helpers for packet-driven PAA hosts."""

from __future__ import annotations

import json
from typing import Optional

from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository


def project_slug_from_message(message: dict) -> str:
    project = message.get("project")
    if project in {"fractal-core-python", "fractal-core"}:
        return "fractal-core-python"
    return str(project or "fractal-core-python")


def issue_number_from_message(message: dict) -> Optional[int]:
    github_context = message.get("github_context") or {}
    issue_number = github_context.get("issue_number")
    try:
        return int(issue_number) if issue_number is not None else None
    except Exception:
        return None


def slice_result_verification_key(command: str) -> Optional[str]:
    lowered = (command or "").lower()
    if "ruff check" in lowered:
        return "lint"
    if "mypy" in lowered:
        return "types"
    if "pytest" in lowered:
        return "tests"
    if "baby7-cli trace" in lowered:
        return "trace"
    if "baby7-cli parity" in lowered:
        return "parity"
    if "baby7-cli benchmark" in lowered:
        return "benchmark"
    return None


def evidence_result_from_text(result_text: str) -> str:
    lowered = (result_text or "").lower()
    if "pass" in lowered:
        return "pass"
    if "warn" in lowered:
        return "warning"
    return "fail"


def persist_qa_verification(message: dict):
    if message.get("schema_type") != "qa_verification_packet":
        return
    project_slug = project_slug_from_message(message)
    issue_number = issue_number_from_message(message)
    github_context = message.get("github_context") or {}
    payload = message.get("payload") or {}
    verification_status = payload.get("verification_status")
    if issue_number is None or verification_status is None:
        return

    if verification_status == "pass":
        evidence_result = "pass"
    elif verification_status == "needs_human_review":
        evidence_result = "warning"
    else:
        evidence_result = "fail"

    findings = payload.get("findings") or []
    finding_summary = findings[0] if findings else f"QA verdict {verification_status} for issue #{issue_number}."
    summary = f"QA packet {message.get('message_id')} reported {verification_status}: {finding_summary}"
    artifact_location = f"qa-packet:{message.get('message_id')}"
    metadata = {
        "packet_id": message.get("message_id"),
        "schema_type": message.get("schema_type"),
        "verification_status": verification_status,
        "github_context": github_context,
        "technical_scope_checks": payload.get("technical_scope_checks"),
        "protected_path_checks": payload.get("protected_path_checks"),
        "artifact_checks": payload.get("artifact_checks"),
        "recommended_action": payload.get("recommended_action"),
        "findings": findings,
    }
    repo = PostgresRuntimeEventRepository()
    resolved = repo.resolve_verification_obligation(
        project_slug=project_slug,
        issue_number=issue_number,
        verification_type='qa_review',
    )
    if resolved is None:
        return
    _verification_key, verification_id = resolved
    repo.record_evidence_if_missing(
        project_slug=project_slug,
        issue_number=issue_number,
        verification_id=verification_id,
        agent_name='QA Agent',
        result=evidence_result,
        summary=summary,
        artifact_location=artifact_location,
        metadata=metadata,
        captured_at=message.get("created_at"),
    )

    decision = None
    decision_notes = None
    if verification_status == "needs_human_review":
        decision = "needs_human_review"
        decision_notes = f"QA escalated packet {message.get('message_id')} for issue #{issue_number}: {finding_summary}"
    elif verification_status == "fail":
        decision = "blocked"
        decision_notes = f"QA blocked packet {message.get('message_id')} for issue #{issue_number}: {finding_summary}"
    if decision is None:
        return
    repo.record_acceptance_event_if_missing(
        project_slug=project_slug,
        issue_number=issue_number,
        agent_name='QA Agent',
        role_name='QA',
        decision=decision,
        notes=decision_notes,
        metadata={
            "packet_id": message.get("message_id"),
            "verification_status": verification_status,
            "pr_number": github_context.get("pr_number"),
            "branch": github_context.get("branch"),
            "recommended_action": payload.get("recommended_action"),
        },
        created_at=message.get("created_at"),
    )


def persist_slice_result(message: dict):
    schema_type = message.get("schema_type")
    if schema_type not in {"slice_result_packet", "worker_result_packet"}:
        return
    project_slug = project_slug_from_message(message)
    issue_number = issue_number_from_message(message)
    payload = message.get("payload") or {}
    validation = payload.get("validation") or {}
    local_checks = validation.get("local") or []
    if issue_number is None:
        return
    normalized_checks = []
    if schema_type == "worker_result_packet":
        validation_summary = payload.get("validation_summary") or []
        if isinstance(validation_summary, list):
            for entry in validation_summary:
                if not isinstance(entry, str):
                    continue
                lowered = entry.lower()
                inferred_result = entry if any(token in lowered for token in ("pass", "warn", "fail")) else "pass"
                normalized_checks.append({"command": entry, "result": inferred_result})
    elif isinstance(local_checks, list) and local_checks:
        normalized_checks = local_checks
    else:
        commands = validation.get("commands") or []
        command_map = {}
        if isinstance(commands, list):
            for command in commands:
                if not isinstance(command, str):
                    continue
                suffix = slice_result_verification_key(command)
                if suffix and suffix not in command_map:
                    command_map[suffix] = command
        field_to_suffix = {
            "ruff": "lint",
            "mypy": "types",
            "pytest": "tests",
            "trace": "trace",
            "parity": "parity",
            "benchmark": "benchmark",
        }
        for field, suffix in field_to_suffix.items():
            result_text = validation.get(field)
            if result_text is None:
                continue
            normalized_checks.append({"command": command_map.get(suffix, field), "result": result_text})
    if not normalized_checks:
        return

    github_context = message.get("github_context") or {}
    github_validation = validation.get("github") or {}
    repo = PostgresRuntimeEventRepository()
    for check in normalized_checks:
        command = check.get("command") or ""
        result_text = check.get("result") or ""
        suffix = slice_result_verification_key(command)
        if suffix is None:
            continue
        resolved = repo.resolve_verification_obligation(
            project_slug=project_slug,
            issue_number=issue_number,
            verification_key_suffix=suffix,
        )
        if not resolved:
            continue
        verification_key, verification_id = resolved
        summary = f"Dev packet {message.get('message_id')} recorded {suffix}: {result_text}"
        artifact_location = f"dev-packet:{message.get('message_id')}:{verification_key}"
        repo.record_evidence_if_missing(
            project_slug=project_slug,
            issue_number=issue_number,
            verification_id=verification_id,
            agent_name='Dev Agent',
            result=evidence_result_from_text(result_text),
            summary=summary,
            artifact_location=artifact_location,
            metadata={
                "packet_id": message.get("message_id"),
                "schema_type": schema_type,
                "command": command,
                "result_text": result_text,
                "github_context": github_context,
                "github_validation": github_validation,
                "result_summary": payload.get("result_summary") or payload.get("implementation_summary"),
                "packet_artifacts": payload.get("artifacts"),
            },
            captured_at=message.get("created_at"),
        )


__all__ = [
    'evidence_result_from_text',
    'issue_number_from_message',
    'persist_qa_verification',
    'persist_slice_result',
    'project_slug_from_message',
    'slice_result_verification_key',
]
