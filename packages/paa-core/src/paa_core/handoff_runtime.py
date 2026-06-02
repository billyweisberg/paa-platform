#!/usr/bin/env python3
import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from paa_core.config import DEFAULT_RUNTIME_QUEUE_EXCHANGE
from paa_core.db import run_psql as shared_run_psql
from paa_core.runtime_paths import repo_root_from_cwd, resolved_repo_runtime_queue_topology
from paa_core.team_worker_roles import (
    active_team_worker_roles,
    techlead_assignment_route_pairs,
    team_worker_result_route_pairs,
)

DEFAULT_HOST = os.environ.get("FRACTAL_CORE_RABBITMQ_HOST", "127.0.0.1")
DEFAULT_MANAGEMENT_PORT = int(os.environ.get("FRACTAL_CORE_RABBITMQ_MANAGEMENT_PORT", "15672"))
DEFAULT_AMQP_PORT = int(os.environ.get("FRACTAL_CORE_RABBITMQ_AMQP_PORT", "5672"))
DEFAULT_USER = os.environ.get("FRACTAL_CORE_RABBITMQ_USER", "guest")
DEFAULT_PASSWORD = os.environ.get("FRACTAL_CORE_RABBITMQ_PASSWORD", "guest")
DEFAULT_VHOST = os.environ.get("FRACTAL_CORE_RABBITMQ_VHOST", "/")
DEFAULT_EXCHANGE = os.environ.get("FRACTAL_CORE_RABBITMQ_EXCHANGE", DEFAULT_RUNTIME_QUEUE_EXCHANGE)
DEFAULT_QUEUES = ["paa-techlead", "paa-qa", "paa-dev"]
STATE_ENV_VAR = "FRACTAL_CORE_HANDOFF_STATE_DIR"
SUPPORTED_SCHEMA_TYPES = {
    "architect_cycle_packet",
    "qa_verification_packet",
    "slice_result_packet",
    "worker_result_packet",
    "delivery_review_packet",
    "techlead_assignment_packet",
    "techlead_decision_packet",
}
ROUTE_POLICY_BY_SCHEMA = {
    "architect_cycle_packet": {("Architect", "Python Dev")},
    "slice_result_packet": {("Python Dev", "TechLead")},
    "worker_result_packet": set(),
    "qa_verification_packet": {("QA", "TechLead")},
    "delivery_review_packet": {("Delivery Architect", "TechLead")},
    "techlead_assignment_packet": set(),
    "techlead_decision_packet": {
        ("TechLead", "Authority Architect"),
        ("TechLead", "TechLead"),
    },
}

ARCHITECT_REQUIRED = [
    "accepted_pr",
    "closed_issue",
    "next_issue",
    "current_baseline",
    "remaining_gap",
    "next_move",
    "focus",
    "keep_stable",
    "governance_reminder",
]
SLICE_REQUIRED = [
    "issue",
    "branch",
    "pr",
    "workflow_compliance",
    "result_summary",
    "mechanism_changed",
    "validation",
    "artifacts",
    "merge_status",
    "architect_decision_needed",
]
QA_REQUIRED = [
    "issue",
    "pr",
    "verification_status",
    "verification_scope",
    "mechanical_checks",
    "technical_scope_checks",
    "protected_path_checks",
    "artifact_checks",
    "findings",
    "recommended_action",
]
WORKER_RESULT_REQUIRED = [
    "issue",
    "branch",
    "pr",
    "worker_role",
    "worker_family",
    "result_type",
    "workflow_compliance",
    "implementation_summary",
    "validation_summary",
    "artifacts",
    "merge_status",
    "techlead_action_recommended",
    "source_assignment_ref",
    "coder_run_brief_ref",
    "coder_run_brief",
    "coder_brief_resolution",
]
DELIVERY_REVIEW_REQUIRED = [
    "issue",
    "branch",
    "pr",
    "review_type",
    "result_type",
    "scope_recommendation",
    "authority_impact",
    "branch_recommendation",
    "techlead_action_recommended",
    "review_summary",
    "findings",
    "source_assignment_ref",
    "coder_run_brief_ref",
    "coder_run_brief",
    "coder_brief_resolution",
]
TECHLEAD_ASSIGNMENT_REQUIRED = [
    "issue",
    "pr",
    "target_role",
    "assignment_type",
    "source_context_ref",
    "canonical_branch",
    "role_branch",
    "branch_owner_role",
    "lineage_state",
    "lineage_action",
    "source_branch",
    "superseded_branch",
    "worktree_hint",
    "reset_reason",
    "allowed_result_types",
    "assignment_summary",
]
TECHLEAD_DECISION_REQUIRED = [
    "issue",
    "pr",
    "source_packet_ref",
    "decision_type",
    "decision_rationale",
    "target_role",
    "next_assignment_type",
    "canonical_branch",
    "role_branch",
    "branch_owner_role",
    "lineage_state",
    "lineage_action",
    "source_branch",
    "superseded_branch",
    "worktree_hint",
    "reset_reason",
    "work_item_status_update_intent",
]
ENVELOPE_REQUIRED = [
    "message_id",
    "schema_type",
    "schema_version",
    "project",
    "from_role",
    "to_role",
    "created_at",
    "correlation_id",
    "payload",
]
AUTHORITY_CONTEXT_REQUIRED = [
    "manifest_path",
    "authority_version",
    "milestone_id",
    "phase_id",
    "task_id",
]
GITHUB_CONTEXT_REQUIRED = ["repo", "issue_number", "pr_number", "branch", "links"]

PAYLOAD_REQUIRED_BY_SCHEMA = {
    "architect_cycle_packet": ARCHITECT_REQUIRED,
    "slice_result_packet": SLICE_REQUIRED,
    "worker_result_packet": WORKER_RESULT_REQUIRED,
    "qa_verification_packet": QA_REQUIRED,
    "delivery_review_packet": DELIVERY_REVIEW_REQUIRED,
    "techlead_assignment_packet": TECHLEAD_ASSIGNMENT_REQUIRED,
    "techlead_decision_packet": TECHLEAD_DECISION_REQUIRED,
}


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sql_literal(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def run_psql(sql: str) -> str:
    return shared_run_psql(sql)


def normalize_role_name(raw_role: Optional[str]) -> Optional[str]:
    if raw_role is None:
        return None
    mapping = {
        "Python Team": "Python Dev",
        "python-team": "Python Dev",
        "Python Dev": "Python Dev",
        "QA": "QA",
        "qa": "QA",
        "Architect": "Architect",
        "architect": "Architect",
        "Authority Architect": "Authority Architect",
        "authority-architect": "Authority Architect",
        "Delivery Architect": "Delivery Architect",
        "delivery-architect": "Delivery Architect",
        "Frontend Dev": "Frontend Dev",
        "frontend-dev": "Frontend Dev",
        "Backend Dev": "Backend Dev",
        "backend-dev": "Backend Dev",
        "Infra Dev": "Infra Dev",
        "infra-dev": "Infra Dev",
        "Docs Dev": "Docs Dev",
        "docs-dev": "Docs Dev",
        "TechLead": "TechLead",
        "techlead": "TechLead",
    }
    for role in active_team_worker_roles():
        mapping[role.key] = role.display_name
        mapping[role.display_name] = role.display_name
    return mapping.get(raw_role, raw_role)


def route_policy_for_schema(schema_type: Optional[str]) -> set[tuple[str, str]] | None:
    if schema_type == "worker_result_packet":
        return team_worker_result_route_pairs()
    if schema_type == "techlead_assignment_packet":
        return techlead_assignment_route_pairs()
    return ROUTE_POLICY_BY_SCHEMA.get(schema_type)


def role_name_for_db(raw_role: Optional[str]) -> Optional[str]:
    normalized = normalize_role_name(raw_role)
    if normalized in {"Python Dev", "Frontend Dev", "Backend Dev", "Infra Dev", "Docs Dev"}:
        return "Dev"
    if normalized == "Delivery Architect":
        return "Architect"
    if normalized == "Authority Architect":
        return "Architect"
    return normalized


def project_slug_from_message(message: dict) -> str:
    project = message.get("project")
    if project in {"fractal-core-python", "fractal-core"}:
        return "fractal-core-python"
    if project == "fractal-core-python":
        return project
    return str(project or "fractal-core-python")


def issue_number_from_message(message: dict) -> Optional[int]:
    github_context = message.get("github_context") or {}
    issue_number = github_context.get("issue_number")
    try:
        return int(issue_number) if issue_number is not None else None
    except Exception:
        return None


def resolve_work_item_id_from_message(message: dict) -> Optional[str]:
    project_slug = project_slug_from_message(message)
    issue_number = issue_number_from_message(message)
    payload = message.get("payload") or {}
    coder_brief_resolution = payload.get("coder_brief_resolution") or {}
    package_id_external = coder_brief_resolution.get("package_id_external")
    brief_id_external = coder_brief_resolution.get("brief_id_external")
    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1
    ), issue_match AS (
      SELECT wi.work_item_id
      FROM paa.work_items wi
      JOIN project p ON p.project_id = wi.project_id
      WHERE wi.issue_number = {sql_literal(issue_number)}
      LIMIT 1
    ), package_match AS (
      SELECT dp.work_item_id
      FROM paa.design_packages dp
      JOIN project p ON p.project_id = dp.project_id
      WHERE dp.package_id_external = {sql_literal(package_id_external)}
        AND dp.work_item_id IS NOT NULL
      LIMIT 1
    ), brief_match AS (
      SELECT cb.work_item_id
      FROM paa.coder_run_briefs cb
      JOIN project p ON p.project_id = cb.project_id
      WHERE cb.brief_id_external = {sql_literal(brief_id_external)}
        AND cb.work_item_id IS NOT NULL
      LIMIT 1
    )
    SELECT coalesce(
      (SELECT work_item_id::text FROM issue_match),
      (SELECT work_item_id::text FROM package_match),
      (SELECT work_item_id::text FROM brief_match)
    );
    """
    try:
        out = run_psql(sql).strip()
    except Exception as exc:
        print(json.dumps({"warning": f"failed to resolve work item for handoff send: {str(exc)}"}), file=sys.stderr)
        return None
    return out or None


def packet_compiler_agent_name_for_message(message: dict) -> str:
    normalized_from_role = role_name_for_db(message.get("from_role"))
    if normalized_from_role == "Dev":
        return "Dev Agent"
    if normalized_from_role == "QA":
        return "QA Agent"
    if normalized_from_role == "TechLead":
        return "TechLead Agent"
    if normalized_from_role == "Architect":
        return "Architect Agent"
    return "TechLead Agent"


def persist_packet_compilation_for_send_message(message: dict, *, message_file: str) -> Optional[str]:
    existing = lookup_packet_compilation_run(message)
    if existing:
        return existing.get("automation_run_id")

    project_slug = project_slug_from_message(message)
    work_item_id = resolve_work_item_id_from_message(message)
    schema_type = str(message.get("schema_type") or "")
    if not schema_type:
        return None

    issue_number = issue_number_from_message(message)
    created_at = message.get("created_at") or utc_now()
    agent_name = packet_compiler_agent_name_for_message(message)
    artifacts = {
        "packet_schema_type": schema_type,
        "message_id": message.get("message_id"),
        "correlation_id": message.get("correlation_id"),
        "output_path": str(Path(message_file).expanduser().resolve()),
        "packet_output_path": str(Path(message_file).expanduser().resolve()),
        "review_output_path": None,
        "source_input_path": str(Path(message_file).expanduser().resolve()),
        "source_packet_path": str(Path(message_file).expanduser().resolve()),
        "packet_json": message,
        "persistence_version": "1.0.0",
    }
    summary = (
        f"Compiled {schema_type} for issue #{issue_number}"
        if issue_number is not None
        else f"Compiled {schema_type}"
    )
    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1
    ), agent AS (
      SELECT a.agent_id
      FROM paa.agents a
      JOIN project p ON p.project_id = a.project_id
      WHERE a.name = {sql_literal(agent_name)}
      LIMIT 1
    )
    INSERT INTO paa.automation_runs (
      agent_id,
      work_item_id,
      trigger_type,
      status,
      started_at,
      finished_at,
      summary,
      artifacts_json
    )
    SELECT
      agent.agent_id,
      {sql_literal(work_item_id)}::uuid,
      {sql_literal(f'packet_compilation:{schema_type}')},
      'completed'::paa.automation_run_status,
      {sql_literal(created_at)}::timestamptz,
      {sql_literal(created_at)}::timestamptz,
      {sql_literal(summary)},
      {sql_literal(json.dumps(artifacts))}::jsonb
    FROM agent;
    """
    try:
        run_psql(sql)
    except Exception as exc:
        print(json.dumps({"warning": f"failed to persist packet compilation for handoff send: {str(exc)}"}), file=sys.stderr)
        return None

    created = lookup_packet_compilation_run(message)
    return created.get("automation_run_id") if created else None


def persist_send_event(
    message: dict,
    queue_name: str,
    publish_result: Optional[dict] = None,
    *,
    exchange: Optional[str] = None,
):
    project_slug = project_slug_from_message(message)
    from_role = role_name_for_db(message.get("from_role"))
    to_role = role_name_for_db(message.get("to_role"))
    resolved_work_item_id = resolve_work_item_id_from_message(message)
    payload_json = json.dumps(message)
    packet_compilation = lookup_packet_compilation_run(message)
    metadata = {
        "queue_name": queue_name,
        "exchange": exchange or DEFAULT_EXCHANGE,
        "publish_result": publish_result or {},
    }
    if packet_compilation:
        metadata["compiled_packet_automation_run_id"] = packet_compilation.get("automation_run_id")
        metadata["compiled_packet_trigger_type"] = packet_compilation.get("trigger_type")
        metadata["compiled_packet_summary"] = packet_compilation.get("summary")
        metadata["compiled_packet_package_id_external"] = packet_compilation.get("package_id_external")
        metadata["compiled_packet_brief_id_external"] = packet_compilation.get("brief_id_external")
    metadata_json = json.dumps(metadata)
    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
    ), from_role AS (
      SELECT role_id FROM paa.roles r JOIN project p ON p.project_id = r.project_id
      WHERE r.name = {sql_literal(from_role)}
    ), to_role AS (
      SELECT role_id FROM paa.roles r JOIN project p ON p.project_id = r.project_id
      WHERE r.name = {sql_literal(to_role)}
    ), existing AS (
      SELECT qm.queue_message_id
      FROM paa.queue_messages qm
      WHERE qm.message_id_external = {sql_literal(message.get("message_id"))}
      LIMIT 1
    ), packet_compilation_run AS (
      SELECT {sql_literal(packet_compilation.get("automation_run_id") if packet_compilation else None)}::uuid AS automation_run_id
    ), inserted_handoff AS (
      INSERT INTO paa.handoffs (
        project_id,
        work_item_id,
        from_role_id,
        to_role_id,
        handoff_type,
        status,
        created_at,
        notes
      )
      SELECT
        project.project_id,
        {sql_literal(resolved_work_item_id)}::uuid,
        (SELECT role_id FROM from_role),
        (SELECT role_id FROM to_role),
        {sql_literal(message.get("schema_type"))},
        'pending'::paa.handoff_status,
        {sql_literal(message.get("created_at"))}::timestamptz,
        {sql_literal(f"correlation_id={message.get('correlation_id')}")}
      FROM project
      WHERE NOT EXISTS (SELECT 1 FROM existing)
      RETURNING handoff_id
    ), linked_compilation_run AS (
      UPDATE paa.automation_runs ar
      SET handoff_id = inserted_handoff.handoff_id,
          updated_at = now()
      FROM inserted_handoff, packet_compilation_run
      WHERE ar.automation_run_id = packet_compilation_run.automation_run_id
      RETURNING ar.automation_run_id
    )
    INSERT INTO paa.queue_messages (
      handoff_id,
      queue_name,
      schema_type,
      message_id_external,
      correlation_key,
      payload_json,
      status,
      sent_at,
      metadata_json
    )
    SELECT
      inserted_handoff.handoff_id,
      {sql_literal(queue_name)},
      {sql_literal(message.get("schema_type"))},
      {sql_literal(message.get("message_id"))},
      {sql_literal(message.get("correlation_id"))},
      {sql_literal(payload_json)}::jsonb,
      'sent'::paa.queue_message_status,
      {sql_literal(utc_now())}::timestamptz,
      {sql_literal(metadata_json)}::jsonb
    FROM inserted_handoff
    WHERE NOT EXISTS (SELECT 1 FROM existing)
    RETURNING queue_message_id;
    """
    try:
        run_psql(sql)
    except Exception as exc:
        print(json.dumps({"warning": f"failed to persist handoff send to PAA: {str(exc)}"}), file=sys.stderr)


def lookup_packet_compilation_run(message: dict) -> Optional[dict]:
    message_id = message.get("message_id")
    schema_type = message.get("schema_type")
    if not message_id or not schema_type:
        return None
    trigger_type = f"packet_compilation:{schema_type}"
    sql = f"""
    SELECT
      ar.automation_run_id,
      ar.trigger_type,
      ar.summary,
      ar.artifacts_json->>'package_id_external',
      ar.artifacts_json->>'brief_id_external'
    FROM paa.automation_runs ar
    WHERE ar.trigger_type = {sql_literal(trigger_type)}
      AND ar.artifacts_json->>'message_id' = {sql_literal(message_id)}
    ORDER BY ar.created_at DESC
    LIMIT 1;
    """
    try:
        out = run_psql(sql).strip()
    except Exception as exc:
        print(json.dumps({"warning": f"failed to lookup packet compilation run in PAA: {str(exc)}"}), file=sys.stderr)
        return None
    if not out:
        return None
    fields = out.split("\t")
    if len(fields) < 5:
        fields.extend([""] * (5 - len(fields)))
    automation_run_id, resolved_trigger_type, summary, package_id_external, brief_id_external = fields[:5]
    return {
        "automation_run_id": automation_run_id,
        "trigger_type": resolved_trigger_type,
        "summary": summary or None,
        "package_id_external": package_id_external or None,
        "brief_id_external": brief_id_external or None,
    }


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
    metadata_json = json.dumps({
        "packet_id": message.get("message_id"),
        "schema_type": message.get("schema_type"),
        "verification_status": verification_status,
        "github_context": github_context,
        "technical_scope_checks": payload.get("technical_scope_checks"),
        "protected_path_checks": payload.get("protected_path_checks"),
        "artifact_checks": payload.get("artifact_checks"),
        "recommended_action": payload.get("recommended_action"),
        "findings": findings,
    })
    decision = None
    decision_notes = None
    if verification_status == "needs_human_review":
        decision = "needs_human_review"
        decision_notes = f"QA escalated packet {message.get('message_id')} for issue #{issue_number}: {finding_summary}"
    elif verification_status == "fail":
        decision = "blocked"
        decision_notes = f"QA blocked packet {message.get('message_id')} for issue #{issue_number}: {finding_summary}"

    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
    ), work_item AS (
      SELECT wi.work_item_id
      FROM paa.work_items wi
      JOIN project p ON p.project_id = wi.project_id
      WHERE wi.issue_number = {sql_literal(issue_number)}
      LIMIT 1
    ), qa_agent AS (
      SELECT a.agent_id
      FROM paa.agents a
      JOIN project p ON p.project_id = a.project_id
      WHERE a.name = 'Fractal Core QA Automation'
      LIMIT 1
    ), qa_role AS (
      SELECT r.role_id
      FROM paa.roles r
      JOIN project p ON p.project_id = r.project_id
      WHERE r.name = 'QA'
      LIMIT 1
    ), verification AS (
      SELECT vo.verification_id
      FROM paa.verification_obligations vo
      JOIN work_item wi ON wi.work_item_id = vo.work_item_id
      WHERE vo.verification_type = 'qa_review'::paa.verification_type
      ORDER BY vo.verification_key
      LIMIT 1
    ), inserted_evidence AS (
      INSERT INTO paa.evidence (
        project_id,
        work_item_id,
        verification_id,
        captured_by_agent_id,
        result,
        summary,
        artifact_location,
        metadata_json,
        captured_at
      )
      SELECT
        project.project_id,
        work_item.work_item_id,
        verification.verification_id,
        qa_agent.agent_id,
        {sql_literal(evidence_result)}::paa.evidence_result,
        {sql_literal(summary)},
        {sql_literal(artifact_location)},
        {sql_literal(metadata_json)}::jsonb,
        {sql_literal(message.get("created_at"))}::timestamptz
      FROM project, work_item, verification, qa_agent
      WHERE NOT EXISTS (
        SELECT 1 FROM paa.evidence ev
        WHERE ev.work_item_id = work_item.work_item_id
          AND ev.artifact_location = {sql_literal(artifact_location)}
      )
      RETURNING evidence_id
    )
    SELECT 1;
    """
    try:
        run_psql(sql)
    except Exception as exc:
        print(json.dumps({"warning": f"failed to persist QA evidence to PAA: {str(exc)}"}), file=sys.stderr)
        return

    if decision is None:
        return

    decision_meta = json.dumps({
        "packet_id": message.get("message_id"),
        "verification_status": verification_status,
        "pr_number": github_context.get("pr_number"),
        "branch": github_context.get("branch"),
        "recommended_action": payload.get("recommended_action"),
    })
    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
    ), work_item AS (
      SELECT wi.work_item_id
      FROM paa.work_items wi
      JOIN project p ON p.project_id = wi.project_id
      WHERE wi.issue_number = {sql_literal(issue_number)}
      LIMIT 1
    ), qa_agent AS (
      SELECT a.agent_id
      FROM paa.agents a
      JOIN project p ON p.project_id = a.project_id
      WHERE a.name = 'Fractal Core QA Automation'
      LIMIT 1
    ), qa_role AS (
      SELECT r.role_id
      FROM paa.roles r
      JOIN project p ON p.project_id = r.project_id
      WHERE r.name = 'QA'
      LIMIT 1
    )
    INSERT INTO paa.acceptance_events (
      project_id,
      work_item_id,
      accepted_by_agent_id,
      accepted_by_role_id,
      decision,
      notes,
      metadata_json,
      created_at
    )
    SELECT
      project.project_id,
      work_item.work_item_id,
      qa_agent.agent_id,
      qa_role.role_id,
      {sql_literal(decision)}::paa.acceptance_decision,
      {sql_literal(decision_notes)},
      {sql_literal(decision_meta)}::jsonb,
      {sql_literal(message.get("created_at"))}::timestamptz
    FROM project, work_item, qa_agent, qa_role
    WHERE NOT EXISTS (
      SELECT 1 FROM paa.acceptance_events ae
      WHERE ae.work_item_id = work_item.work_item_id
        AND ae.notes = {sql_literal(decision_notes)}
    );
    """
    try:
        run_psql(sql)
    except Exception as exc:
        print(json.dumps({"warning": f"failed to persist QA escalation event to PAA: {str(exc)}"}), file=sys.stderr)


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
                normalized_checks.append({
                    "command": entry,
                    "result": inferred_result,
                })
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
            normalized_checks.append({
                "command": command_map.get(suffix, field),
                "result": result_text,
            })
    if not normalized_checks:
        return

    github_context = message.get("github_context") or {}
    github_validation = validation.get("github") or {}
    for check in normalized_checks:
        command = check.get("command") or ""
        result_text = check.get("result") or ""
        suffix = slice_result_verification_key(command)
        if suffix is None:
            continue
        lookup_sql = f"""
        WITH project AS (
          SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
        ), work_item AS (
          SELECT wi.work_item_id
          FROM paa.work_items wi
          JOIN project p ON p.project_id = wi.project_id
          WHERE wi.issue_number = {sql_literal(issue_number)}
          LIMIT 1
        )
        SELECT vo.verification_key, vo.verification_id
        FROM paa.verification_obligations vo
        JOIN work_item wi ON wi.work_item_id = vo.work_item_id
        WHERE vo.verification_key LIKE {sql_literal(f'%{suffix}')}
        LIMIT 1;
        """
        try:
            resolved = run_psql(lookup_sql).strip()
        except Exception as exc:
            print(json.dumps({"warning": f"failed to resolve Dev verification key in PAA for suffix {suffix}: {str(exc)}"}), file=sys.stderr)
            continue
        if not resolved:
            continue
        verification_key, verification_id = resolved.split("\t", 1)
        summary = f"Dev packet {message.get('message_id')} recorded {suffix}: {result_text}"
        artifact_location = f"dev-packet:{message.get('message_id')}:{verification_key}"
        metadata_json = json.dumps({
            "packet_id": message.get("message_id"),
            "schema_type": schema_type,
            "command": command,
            "result_text": result_text,
            "github_context": github_context,
            "github_validation": github_validation,
            "result_summary": payload.get("result_summary") or payload.get("implementation_summary"),
            "packet_artifacts": payload.get("artifacts"),
        })
        sql = f"""
        WITH project AS (
          SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
        ), work_item AS (
          SELECT wi.work_item_id
          FROM paa.work_items wi
          JOIN project p ON p.project_id = wi.project_id
          WHERE wi.issue_number = {sql_literal(issue_number)}
          LIMIT 1
        ), dev_agent AS (
          SELECT a.agent_id
          FROM paa.agents a
          JOIN project p ON p.project_id = a.project_id
          WHERE a.name = 'Python Team Automation'
          LIMIT 1
        )
        INSERT INTO paa.evidence (
          project_id,
          work_item_id,
          verification_id,
          captured_by_agent_id,
          result,
          summary,
          artifact_location,
          metadata_json,
          captured_at
        )
        SELECT
          project.project_id,
          work_item.work_item_id,
          {sql_literal(verification_id)},
          dev_agent.agent_id,
          {sql_literal(evidence_result_from_text(result_text))}::paa.evidence_result,
          {sql_literal(summary)},
          {sql_literal(artifact_location)},
          {sql_literal(metadata_json)}::jsonb,
          {sql_literal(message.get("created_at"))}::timestamptz
        FROM project, work_item, dev_agent
        WHERE NOT EXISTS (
          SELECT 1 FROM paa.evidence ev
          WHERE ev.work_item_id = work_item.work_item_id
            AND ev.artifact_location = {sql_literal(artifact_location)}
        );
        """
        try:
            run_psql(sql)
        except Exception as exc:
            print(json.dumps({"warning": f"failed to persist Dev evidence to PAA for {verification_key}: {str(exc)}"}), file=sys.stderr)


def update_queue_message_status(message_id: Optional[str], queue_status: str, handoff_status: str, timestamp_field: str):
    if not message_id:
        return
    timestamp = utc_now()
    sql = f"""
    WITH target AS (
      SELECT qm.queue_message_id, qm.handoff_id
      FROM paa.queue_messages qm
      WHERE qm.message_id_external = {sql_literal(message_id)}
      LIMIT 1
    ), updated_message AS (
      UPDATE paa.queue_messages qm
      SET status = {sql_literal(queue_status)}::paa.queue_message_status,
          {timestamp_field} = {sql_literal(timestamp)}::timestamptz,
          updated_at = now()
      FROM target
      WHERE qm.queue_message_id = target.queue_message_id
      RETURNING qm.handoff_id
    )
    UPDATE paa.handoffs h
    SET status = {sql_literal(handoff_status)}::paa.handoff_status,
        claimed_at = CASE WHEN {sql_literal(handoff_status)} = 'claimed' THEN {sql_literal(timestamp)}::timestamptz ELSE h.claimed_at END,
        acknowledged_at = CASE WHEN {sql_literal(handoff_status)} = 'completed' THEN {sql_literal(timestamp)}::timestamptz ELSE h.acknowledged_at END,
        closed_at = CASE WHEN {sql_literal(handoff_status)} = 'completed' THEN {sql_literal(timestamp)}::timestamptz ELSE h.closed_at END
      FROM updated_message
      WHERE h.handoff_id = updated_message.handoff_id;
    """
    try:
        run_psql(sql)
    except Exception as exc:
        print(json.dumps({"warning": f"failed to update handoff status in PAA: {str(exc)}"}), file=sys.stderr)


def get_git_root() -> Optional[Path]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return None
    path = result.stdout.strip()
    return Path(path) if path else None


def state_root_candidates() -> list[tuple[Path, str]]:
    explicit = os.environ.get(STATE_ENV_VAR)
    if explicit:
        return [(Path(explicit).expanduser(), f"env:{STATE_ENV_VAR}")]

    candidates: list[tuple[Path, str]] = []
    home_root = Path.home() / ".codex/state/fractal-core-handoff"
    repo_root = get_git_root() or Path.cwd()
    runtime_root = repo_root / ".project/data/paa/queue-state/fractal-core-handoff"
    candidates.append((runtime_root, "repo-runtime"))
    candidates.append((home_root, "home"))

    git_root = get_git_root()
    if git_root:
        candidates.append((git_root / ".codex-state/fractal-core-handoff", "git-root"))

    cwd_root = Path.cwd() / ".codex-state/fractal-core-handoff"
    if all(cwd_root != path for path, _ in candidates):
        candidates.append((cwd_root, "cwd"))

    return candidates


def unique_state_root_candidates() -> list[tuple[Path, str]]:
    seen: set[Path] = set()
    ordered: list[tuple[Path, str]] = []
    for path, source in state_root_candidates():
        resolved = path.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append((resolved, source))
    return ordered


def path_is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".writable-{uuid.uuid4().hex}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except Exception:
        return False


def resolve_active_state_root() -> tuple[Path, str, list[dict[str, object]]]:
    candidates = unique_state_root_candidates()
    candidate_info = []
    explicit = bool(os.environ.get(STATE_ENV_VAR))
    for path, source in candidates:
        writable = path_is_writable_dir(path)
        candidate_info.append({"path": str(path), "source": source, "writable": writable})
        if writable:
            return path, source, candidate_info
    if explicit:
        raise RuntimeError(
            f"Configured state dir via {STATE_ENV_VAR} is not writable: {candidates[0][0]}"
        )
    raise RuntimeError(
        "No writable claim-ledger state directory found. Candidates: "
        + ", ".join(f"{info['source']}={info['path']} writable={info['writable']}" for info in candidate_info)
    )


def claims_dir(root: Path) -> Path:
    return root / "claims"


def ensure_state_dirs() -> tuple[Path, str, list[dict[str, object]]]:
    root, source, candidate_info = resolve_active_state_root()
    claims_dir(root).mkdir(parents=True, exist_ok=True)
    return root, source, candidate_info


def claim_path(claim_id: str, root: Optional[Path] = None) -> Path:
    if root is None:
        root, _, _ = ensure_state_dirs()
    return claims_dir(root) / f"{claim_id}.json"


def all_existing_claim_dirs() -> list[Path]:
    dirs: list[Path] = []
    seen: set[Path] = set()
    for root, _ in unique_state_root_candidates():
        cdir = claims_dir(root)
        if cdir.exists() and cdir not in seen:
            seen.add(cdir)
            dirs.append(cdir)
    return dirs


class RabbitMQManagementClient:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_MANAGEMENT_PORT, user=DEFAULT_USER, password=DEFAULT_PASSWORD, vhost=DEFAULT_VHOST):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.base = f"http://{host}:{port}/api"
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.auth_header = f"Basic {token}"

    def _request(self, method, path, payload=None):
        data = None
        headers = {"Authorization": self.auth_header}
        if payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode() if resp.length != 0 else ""
                return resp.status, json.loads(body) if body else None
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"RabbitMQ API {method} {path} failed: {e.code} {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"RabbitMQ API connection failed: {e}") from e

    def overview(self):
        return self._request("GET", "/overview")

    def queue(self, name):
        vhost = urllib.parse.quote(self.vhost, safe="")
        qname = urllib.parse.quote(name, safe="")
        return self._request("GET", f"/queues/{vhost}/{qname}")

    def declare_exchange(self, name, exchange_type="direct", durable=True):
        vhost = urllib.parse.quote(self.vhost, safe="")
        ename = urllib.parse.quote(name, safe="")
        return self._request("PUT", f"/exchanges/{vhost}/{ename}", {"type": exchange_type, "durable": durable, "auto_delete": False, "internal": False, "arguments": {}})

    def declare_queue(self, name, durable=True):
        vhost = urllib.parse.quote(self.vhost, safe="")
        qname = urllib.parse.quote(name, safe="")
        return self._request("PUT", f"/queues/{vhost}/{qname}", {"durable": durable, "auto_delete": False, "arguments": {}})

    def bind_queue(self, exchange, queue, routing_key):
        vhost = urllib.parse.quote(self.vhost, safe="")
        ename = urllib.parse.quote(exchange, safe="")
        qname = urllib.parse.quote(queue, safe="")
        return self._request("POST", f"/bindings/{vhost}/e/{ename}/q/{qname}", {"routing_key": routing_key, "arguments": {}})

    def publish(self, exchange, routing_key, payload):
        vhost = urllib.parse.quote(self.vhost, safe="")
        ename = urllib.parse.quote(exchange, safe="")
        body = {
            "properties": {"delivery_mode": 2},
            "routing_key": routing_key,
            "payload": json.dumps(payload),
            "payload_encoding": "string",
        }
        return self._request("POST", f"/exchanges/{vhost}/{ename}/publish", body)

    def get_messages(self, queue, count=1, ackmode="ack_requeue_true", truncate=50000):
        vhost = urllib.parse.quote(self.vhost, safe="")
        qname = urllib.parse.quote(queue, safe="")
        body = {
            "count": count,
            "ackmode": ackmode,
            "encoding": "auto",
            "truncate": truncate,
        }
        return self._request("POST", f"/queues/{vhost}/{qname}/get", body)

    def purge_queue(self, queue):
        vhost = urllib.parse.quote(self.vhost, safe="")
        qname = urllib.parse.quote(queue, safe="")
        return self._request("DELETE", f"/queues/{vhost}/{qname}/contents")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def reconcile_ready_count(raw_ready: Optional[int], preview: list[dict], preview_probe_ran: bool) -> tuple[int, Optional[dict]]:
    raw_value = 0 if raw_ready is None else int(raw_ready)
    observed_minimum = len(preview)
    if not preview_probe_ran:
        return raw_value, None
    if observed_minimum == 0 and raw_value != 0:
        return 0, {
            "raw_messages_ready": raw_value,
            "observed_preview_count": observed_minimum,
            "reason": "preview_empty_but_broker_ready_nonzero",
        }
    if observed_minimum > raw_value:
        return observed_minimum, {
            "raw_messages_ready": raw_value,
            "observed_preview_count": observed_minimum,
            "reason": "preview_count_exceeded_broker_ready",
        }
    return raw_value, None


def validate_envelope(message, require_authority=True):
    errors = []
    for field in ENVELOPE_REQUIRED:
        if field not in message:
            errors.append(f"missing top-level field: {field}")
    if "github_context" not in message:
        errors.append("missing top-level field: github_context")
    if require_authority and "authority_context" not in message:
        errors.append("missing top-level field: authority_context")
    if errors:
        return errors
    if message.get("schema_type") not in SUPPORTED_SCHEMA_TYPES:
        errors.append(f"unsupported schema_type: {message.get('schema_type')}")
    ac = message.get("authority_context")
    if require_authority:
        if not isinstance(ac, dict):
            errors.append("authority_context must be an object")
        else:
            for field in AUTHORITY_CONTEXT_REQUIRED:
                if field not in ac:
                    errors.append(f"missing authority_context field: {field}")
    gc = message.get("github_context")
    if not isinstance(gc, dict):
        errors.append("github_context must be an object")
    else:
        for field in GITHUB_CONTEXT_REQUIRED:
            if field not in gc:
                errors.append(f"missing github_context field: {field}")
    payload = message.get("payload")
    if not isinstance(payload, dict):
        errors.append("payload must be an object")
    else:
        required = PAYLOAD_REQUIRED_BY_SCHEMA.get(message.get("schema_type"), [])
        for field in required:
            if field not in payload:
                errors.append(f"missing payload field: {field}")
    expected_route = route_policy_for_schema(message.get("schema_type"))
    if expected_route:
        actual_from_role = normalize_role_name(message.get("from_role"))
        actual_to_role = normalize_role_name(message.get("to_role"))
        if (actual_from_role, actual_to_role) not in expected_route:
            route_options = ", ".join(f"{fr} -> {to}" for fr, to in sorted(expected_route))
            errors.append(
                "invalid route for "
                f"{message.get('schema_type')}: expected one of [{route_options}], "
                f"got {actual_from_role} -> {actual_to_role}"
            )
    return errors


def list_claims(queue=None, status=None):
    claims = []
    for cdir in all_existing_claim_dirs():
        for path in sorted(cdir.glob("*.json")):
            try:
                data = load_json(path)
            except Exception:
                continue
            if queue and data.get("queue") != queue:
                continue
            if status and data.get("status") != status:
                continue
            data.setdefault("state_dir", str(cdir.parent))
            claims.append(data)
    return claims


def load_claim(claim_id):
    for cdir in all_existing_claim_dirs():
        path = cdir / f"{claim_id}.json"
        if path.exists():
            return path, load_json(path)
    raise RuntimeError(f"claim not found: {claim_id}")


def cmd_state_info(_args):
    root, source, candidate_info = ensure_state_dirs()
    print(json.dumps({
        "active_state_dir": str(root),
        "active_state_source": source,
        "claim_dir": str(claims_dir(root)),
        "candidates": candidate_info,
    }, indent=2))


def _resolved_repo_root(args) -> Path:
    repo_root = getattr(args, 'repo_root', None)
    if repo_root:
        return Path(str(repo_root)).expanduser().resolve()
    return repo_root_from_cwd()


def _resolved_runtime_exchange(args) -> str:
    if getattr(args, 'exchange', DEFAULT_EXCHANGE) != DEFAULT_EXCHANGE:
        return args.exchange
    topology = resolved_repo_runtime_queue_topology(_resolved_repo_root(args))
    return topology.queue_exchange or DEFAULT_EXCHANGE


def _resolved_runtime_queues(args) -> list[str]:
    if list(getattr(args, 'queues', DEFAULT_QUEUES)) != list(DEFAULT_QUEUES):
        return list(args.queues)
    topology = resolved_repo_runtime_queue_topology(_resolved_repo_root(args))
    return list(topology.queue_names.values())


def cmd_ensure_topology(args):
    root, source, candidate_info = ensure_state_dirs()
    client = RabbitMQManagementClient(user=args.user, password=args.password, host=args.host, port=args.port, vhost=args.vhost)
    status, overview = client.overview()
    exchange = _resolved_runtime_exchange(args)
    queues = _resolved_runtime_queues(args)
    client.declare_exchange(exchange)
    for queue in queues:
        client.declare_queue(queue)
        client.bind_queue(exchange, queue, queue)
    result = {
        "ok": True,
        "management_status": status,
        "rabbitmq_version": overview.get("rabbitmq_version"),
        "exchange": exchange,
        "queues": queues,
        "state_dir": str(root),
        "state_dir_source": source,
        "state_dir_candidates": candidate_info,
        "amqp_port": DEFAULT_AMQP_PORT,
    }
    print(json.dumps(result, indent=2))


def cmd_check(args):
    root, source, _ = ensure_state_dirs()
    client = RabbitMQManagementClient(user=args.user, password=args.password, host=args.host, port=args.port, vhost=args.vhost)
    _, queue_data = client.queue(args.queue)
    preview = []
    preview_probe_ran = args.preview > 0
    if args.preview > 0:
        _, messages = client.get_messages(args.queue, count=args.preview, ackmode="ack_requeue_true")
        for msg in messages:
            payload = msg.get("payload")
            try:
                parsed = json.loads(payload) if isinstance(payload, str) else payload
            except Exception:
                parsed = {"raw_payload": payload}
            preview.append({
                "message_count": msg.get("message_count"),
                "redelivered": msg.get("redelivered"),
                "payload_preview": {
                    "message_id": parsed.get("message_id"),
                    "schema_type": parsed.get("schema_type"),
                    "created_at": parsed.get("created_at"),
                    "correlation_id": parsed.get("correlation_id"),
                    "from_role": parsed.get("from_role"),
                    "to_role": parsed.get("to_role"),
                    "github_context": parsed.get("github_context"),
                    "payload": parsed.get("payload"),
                },
            })
    messages_ready, reconciliation = reconcile_ready_count(
        queue_data.get("messages_ready"),
        preview,
        preview_probe_ran,
    )
    result = {
        "queue": args.queue,
        "messages_ready": messages_ready,
        "messages_ready_raw": queue_data.get("messages_ready"),
        "messages_unacknowledged": queue_data.get("messages_unacknowledged"),
        "consumers": queue_data.get("consumers"),
        "active_state_dir": str(root),
        "active_state_source": source,
        "preview": preview,
    }
    if reconciliation:
        result["reconciliation"] = reconciliation
    print(json.dumps(result, indent=2))


def cmd_purge(args):
    client = RabbitMQManagementClient(user=args.user, password=args.password, host=args.host, port=args.port, vhost=args.vhost)
    queues = [args.queue] if args.queue else _resolved_runtime_queues(args)
    purged = []
    for queue in queues:
        client.purge_queue(queue)
        purged.append(queue)
    print(json.dumps({
        "ok": True,
        "purged_queues": purged,
        "queue_count": len(purged),
    }, indent=2))


def cmd_validate(args):
    message = load_json(args.message_file)
    errors = validate_envelope(message, require_authority=True)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        sys.exit(1)
    print(json.dumps({"ok": True, "schema_type": message["schema_type"], "message_id": message["message_id"]}, indent=2))


def cmd_send(args):
    message = load_json(args.message_file)
    errors = validate_envelope(message, require_authority=True)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        sys.exit(1)
    client = RabbitMQManagementClient(user=args.user, password=args.password, host=args.host, port=args.port, vhost=args.vhost)
    exchange = _resolved_runtime_exchange(args)
    _, result = client.publish(exchange, args.queue, message)
    if result.get("routed"):
        persist_packet_compilation_for_send_message(message, message_file=args.message_file)
        persist_send_event(message, args.queue, publish_result=result, exchange=exchange)
        persist_slice_result(message)
        persist_qa_verification(message)
    print(json.dumps({"ok": bool(result.get("routed")), "queue": args.queue, "message_id": message["message_id"], "schema_type": message["schema_type"]}, indent=2))


def cmd_claim_next(args):
    root, source, _ = ensure_state_dirs()
    client = RabbitMQManagementClient(user=args.user, password=args.password, host=args.host, port=args.port, vhost=args.vhost)
    _, messages = client.get_messages(args.queue, count=1, ackmode="ack_requeue_false")
    if not messages:
        print(json.dumps({"ok": True, "queue": args.queue, "claimed": False}, indent=2))
        return
    msg = messages[0]
    payload = msg.get("payload")
    parsed = json.loads(payload) if isinstance(payload, str) else payload
    if not isinstance(parsed, dict):
        parsed = {}
        errors = ["queue message payload must decode to an object envelope"]
    else:
        errors = validate_envelope(parsed, require_authority=False)
    if errors:
        claim_id = str(uuid.uuid4())
        record = {
            "claim_id": claim_id,
            "queue": args.queue,
            "claimed_at": utc_now(),
            "claimed_by": args.claimed_by,
            "status": "invalid",
            "state_dir": str(root),
            "state_dir_source": source,
            "validation_errors": errors,
            "original_envelope": parsed,
        }
        save_json(claim_path(claim_id, root), record)
        print(json.dumps({"ok": False, "claimed": True, "claim_id": claim_id, "errors": errors, "state_dir": str(root)}, indent=2))
        sys.exit(1)
    claim_id = str(uuid.uuid4())
    record = {
        "claim_id": claim_id,
        "queue": args.queue,
        "claimed_at": utc_now(),
        "claimed_by": args.claimed_by,
        "status": "claimed",
        "state_dir": str(root),
        "state_dir_source": source,
        "original_envelope": parsed,
    }
    save_json(claim_path(claim_id, root), record)
    update_queue_message_status(parsed.get("message_id"), "claimed", "claimed", "claimed_at")
    print(json.dumps({
        "ok": True,
        "claimed": True,
        "claim_id": claim_id,
        "queue": args.queue,
        "message_id": parsed.get("message_id"),
        "schema_type": parsed.get("schema_type"),
        "correlation_id": parsed.get("correlation_id"),
        "state_dir": str(root),
        "state_dir_source": source,
    }, indent=2))


def cmd_list_claims(args):
    claims = list_claims(queue=args.queue, status=args.status)
    summary = []
    for claim in claims:
        env = claim.get("original_envelope", {})
        summary.append({
            "claim_id": claim.get("claim_id"),
            "queue": claim.get("queue"),
            "status": claim.get("status"),
            "claimed_at": claim.get("claimed_at"),
            "claimed_by": claim.get("claimed_by"),
            "state_dir": claim.get("state_dir"),
            "message_id": env.get("message_id"),
            "schema_type": env.get("schema_type"),
            "correlation_id": env.get("correlation_id"),
        })
    print(json.dumps({"claims": summary}, indent=2))


def cmd_ack(args):
    path, claim = load_claim(args.claim_id)
    claim["status"] = "done"
    claim["acked_at"] = utc_now()
    save_json(path, claim)
    update_queue_message_status((claim.get("original_envelope") or {}).get("message_id"), "acknowledged", "completed", "acknowledged_at")
    print(json.dumps({"ok": True, "claim_id": args.claim_id, "status": claim["status"], "state_dir": claim.get("state_dir")}, indent=2))


def cmd_requeue(args):
    path, claim = load_claim(args.claim_id)
    env = claim.get("original_envelope")
    client = RabbitMQManagementClient(user=args.user, password=args.password, host=args.host, port=args.port, vhost=args.vhost)
    exchange = _resolved_runtime_exchange(args)
    _, result = client.publish(exchange, claim["queue"], env)
    claim["status"] = "requeued"
    claim["requeued_at"] = utc_now()
    claim["requeue_result"] = deepcopy(result)
    save_json(path, claim)
    update_queue_message_status((claim.get("original_envelope") or {}).get("message_id"), "requeued", "requeued", "updated_at")
    print(json.dumps({"ok": bool(result.get("routed")), "claim_id": args.claim_id, "status": claim["status"], "queue": claim["queue"], "state_dir": claim.get("state_dir")}, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description="Fractal Core RabbitMQ handoff runtime")
    parser.set_defaults(func=None)
    parser.add_argument("--repo-root")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_MANAGEMENT_PORT)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--vhost", default=DEFAULT_VHOST)
    parser.add_argument("--exchange", default=DEFAULT_EXCHANGE)
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("state-info")
    p.set_defaults(func=cmd_state_info)

    p = sub.add_parser("ensure-topology")
    p.add_argument("--queues", nargs="+", default=DEFAULT_QUEUES)
    p.set_defaults(func=cmd_ensure_topology)

    p = sub.add_parser("check")
    p.add_argument("--queue", required=True)
    p.add_argument("--preview", type=int, default=1)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("purge")
    p.add_argument("--queue")
    p.set_defaults(func=cmd_purge)

    p = sub.add_parser("validate")
    p.add_argument("--message-file", required=True)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("send")
    p.add_argument("--queue", required=True)
    p.add_argument("--message-file", required=True)
    p.set_defaults(func=cmd_send)

    p = sub.add_parser("claim-next")
    p.add_argument("--queue", required=True)
    p.add_argument("--claimed-by", required=True)
    p.set_defaults(func=cmd_claim_next)

    p = sub.add_parser("list-claims")
    p.add_argument("--queue")
    p.add_argument("--status")
    p.set_defaults(func=cmd_list_claims)

    p = sub.add_parser("ack")
    p.add_argument("--claim-id", required=True)
    p.set_defaults(func=cmd_ack)

    p = sub.add_parser("requeue")
    p.add_argument("--claim-id", required=True)
    p.set_defaults(func=cmd_requeue)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.func:
        parser.print_help()
        sys.exit(2)
    args.func(args)


if __name__ == "__main__":
    main()
