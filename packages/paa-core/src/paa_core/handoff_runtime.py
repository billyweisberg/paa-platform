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

from paa_core import claim_ledger as claim_ledger_helpers
from paa_core import packet_envelope as packet_envelope_helpers
from paa_core import queue_transport as queue_transport_helpers
from paa_core.config import DEFAULT_RUNTIME_QUEUE_EXCHANGE
from paa_core.db import run_psql as shared_run_psql
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.runtime_paths import repo_root_from_cwd, resolved_repo_runtime_queue_topology
from paa_core.runtime_evidence import persist_qa_verification as shared_persist_qa_verification
from paa_core.runtime_evidence import persist_slice_result as shared_persist_slice_result
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
    return claim_ledger_helpers.utc_now()


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
    if schema_type is None:
        return None
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
    try:
        return PostgresRuntimeEventRepository().resolve_work_item_id_for_message(message)
    except Exception as exc:
        print(json.dumps({"warning": f"failed to resolve work item for handoff send: {str(exc)}"}), file=sys.stderr)
        return None


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
    agent_name = packet_compiler_agent_name_for_message(message)
    try:
        record = PostgresRuntimeEventRepository().create_packet_compilation_run_for_message(
            message=message,
            message_file=message_file,
            agent_name=agent_name,
        )
        return record.automation_run_id if record is not None else None
    except Exception as exc:
        print(json.dumps({"warning": f"failed to persist packet compilation for handoff send: {str(exc)}"}), file=sys.stderr)
        return None


def persist_send_event(
    message: dict,
    queue_name: str,
    publish_result: Optional[dict] = None,
    *,
    exchange: Optional[str] = None,
):
    try:
        repo = PostgresRuntimeEventRepository()
        repo.record_queue_send_for_message(
            message=message,
            queue_name=queue_name,
            exchange=exchange or DEFAULT_EXCHANGE,
            publish_result=publish_result,
            packet_compilation_run=repo.find_packet_compilation_run(
                message_id_external=str(message.get("message_id") or ""),
                schema_type=str(message.get("schema_type") or ""),
            ),
        )
    except Exception as exc:
        print(json.dumps({"warning": f"failed to persist handoff send to PAA: {str(exc)}"}), file=sys.stderr)


def lookup_packet_compilation_run(message: dict) -> Optional[dict]:
    message_id = message.get("message_id")
    schema_type = message.get("schema_type")
    if not message_id or not schema_type:
        return None
    try:
        record = PostgresRuntimeEventRepository().find_packet_compilation_run(
            message_id_external=str(message_id),
            schema_type=str(schema_type),
        )
    except Exception as exc:
        print(json.dumps({"warning": f"failed to lookup packet compilation run in PAA: {str(exc)}"}), file=sys.stderr)
        return None
    if record is None:
        return None
    return {
        "automation_run_id": record.automation_run_id,
        "trigger_type": record.trigger_type,
        "summary": record.summary or None,
        "package_id_external": record.artifacts.get("package_id_external"),
        "brief_id_external": record.artifacts.get("brief_id_external"),
    }


def persist_qa_verification(message: dict):
    try:
        return shared_persist_qa_verification(message)
    except Exception as exc:
        print(json.dumps({"warning": f"failed to persist QA evidence to PAA: {str(exc)}"}), file=sys.stderr)


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
    try:
        return shared_persist_slice_result(message)
    except Exception as exc:
        print(json.dumps({"warning": f"failed to persist Dev evidence to PAA: {str(exc)}"}), file=sys.stderr)


def update_queue_message_status(message_id: Optional[str], queue_status: str, handoff_status: str, timestamp_field: str):
    if not message_id:
        return
    try:
        PostgresRuntimeEventRepository().update_queue_message_status_by_external(
            message_id_external=message_id,
            queue_status=queue_status,
            handoff_status=handoff_status,
            timestamp_field=timestamp_field,
        )
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
    return claim_ledger_helpers.state_root_candidates()


def unique_state_root_candidates() -> list[tuple[Path, str]]:
    return claim_ledger_helpers.unique_state_root_candidates()


def path_is_writable_dir(path: Path) -> bool:
    return claim_ledger_helpers.path_is_writable_dir(path)


def resolve_active_state_root() -> tuple[Path, str, list[dict[str, object]]]:
    return claim_ledger_helpers.resolve_active_state_root()


def claims_dir(root: Path) -> Path:
    return claim_ledger_helpers.claims_dir(root)


def ensure_state_dirs() -> tuple[Path, str, list[dict[str, object]]]:
    return claim_ledger_helpers.ensure_state_dirs()


def claim_path(claim_id: str, root: Optional[Path] = None) -> Path:
    return claim_ledger_helpers.claim_path(claim_id, root)


def all_existing_claim_dirs() -> list[Path]:
    return claim_ledger_helpers.all_existing_claim_dirs()


class RabbitMQManagementClient(queue_transport_helpers.RabbitMQManagementClient):
    pass


def load_json(path):
    return claim_ledger_helpers.load_json(path)


def save_json(path, data):
    return claim_ledger_helpers.save_json(path, data)


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
    return packet_envelope_helpers.validate_envelope(message, require_authority=require_authority)


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
    return claim_ledger_helpers.FileQueueClaimLedgerRepository().load_claim(claim_id)


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
        "rabbitmq_version": overview.get("rabbitmq_version") if isinstance(overview, dict) else None,
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
    if not isinstance(queue_data, dict):
        queue_data = {}
    preview = []
    preview_probe_ran = args.preview > 0
    if args.preview > 0:
        _, messages = client.get_messages(args.queue, count=args.preview, ackmode="ack_requeue_true")
        if not isinstance(messages, list):
            messages = []
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
    routed = result.get("routed") if isinstance(result, dict) else False
    if routed:
        persist_packet_compilation_for_send_message(message, message_file=args.message_file)
        persist_send_event(message, args.queue, publish_result=result, exchange=exchange)
        persist_slice_result(message)
        persist_qa_verification(message)
    print(json.dumps({"ok": bool(routed), "queue": args.queue, "message_id": message["message_id"], "schema_type": message["schema_type"]}, indent=2))


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
    routed = result.get("routed") if isinstance(result, dict) else False
    print(json.dumps({"ok": bool(routed), "claim_id": args.claim_id, "status": claim["status"], "queue": claim["queue"], "state_dir": claim.get("state_dir")}, indent=2))


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
