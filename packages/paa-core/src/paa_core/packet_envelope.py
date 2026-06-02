"""Packet envelope IO and validation helpers for the PAA runtime."""

from __future__ import annotations

from typing import Optional

from paa_core.team_worker_roles import (
    active_team_worker_roles,
    techlead_assignment_route_pairs,
    team_worker_result_route_pairs,
)

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


def validate_envelope(message, require_authority: bool = True):
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


__all__ = [
    'SUPPORTED_SCHEMA_TYPES',
    'normalize_role_name',
    'route_policy_for_schema',
    'validate_envelope',
]
