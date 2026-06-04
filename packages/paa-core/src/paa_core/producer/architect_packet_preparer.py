"""Producer-side packet readiness and architect packet preparation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import copy
import json
from pathlib import Path
from typing import Any

from paa_core.db import query_rows, run_psql, sql_literal
from paa_core.producer.authority_support import persist_packet_compilation
from paa_core.producer.authority_packet_support import (
    derive_focus,
    derive_governance_reminders,
    derive_keep_stable,
    derive_next_move,
    derive_remaining_gap,
    unique_preserving_order,
    write_review_markdown,
)
from paa_core.producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - dependency guard
    Draft202012Validator = None

DEFAULT_ARCHITECT_PACKET_SCHEMA_PATH = Path(
    '/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/architect_cycle_packet.schema.json'
)
DEFAULT_CODER_BRIEF_SCHEMA_PATH = Path(
    '/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/derivation/coder_run_brief.schema.json'
)


@dataclass(frozen=True)
class PacketPreparationCheck:
    check_id: str
    status: str
    severity: str
    message: str
    evidence: dict[str, Any]


@dataclass(frozen=True)
class PacketBriefContext:
    coder_run_brief_id: str
    project_id: str
    project_slug: str
    work_item_id: str | None
    authority_state: str
    status: str
    brief_id_external: str
    brief_json: dict[str, Any]
    approval_json: dict[str, Any]
    packet_preparation_json: dict[str, Any]
    generated_from_json: dict[str, Any]
    metadata_json: dict[str, Any]
    readiness_class: str | None
    target_count: int
    component_name: str


@dataclass(frozen=True)
class PreparedArchitectPacketResult:
    project_slug: str
    package_id_external: str
    coder_run_brief_id: str
    brief_id_external: str
    authority_state: str
    status: str
    transition_applied: bool
    packet_output_path: str
    brief_output_path: str
    review_output_path: str | None
    packet_schema_path: str
    brief_schema_path: str
    message_id: str
    target_count: int
    packet_preparation_json: dict[str, Any]
    checks: list[dict[str, Any]]


@dataclass(frozen=True)
class PacketPreparationOptions:
    manifest_path: Path
    package_path: Path
    packet_output_path: Path
    brief_output_path: Path
    repo: str
    branch: str
    accepted_pr_number: int
    accepted_pr_url: str
    closed_issue_number: int
    closed_issue_url: str
    next_issue_number: int
    next_issue_url: str
    baseline_file: Path
    review_output_path: Path | None = None
    schema_path: Path | None = None
    project_slug: str | None = None
    packet_project: str | None = None
    remaining_gap: str | None = None
    next_move: tuple[str, ...] = ()
    focus: tuple[str, ...] = ()
    keep_stable: tuple[str, ...] = ()
    governance_reminder: tuple[str, ...] = ()
    pr_starter_branch: str | None = None
    pr_starter_title: str | None = None
    pr_starter_body_linkage: str | None = None
    message_id: str | None = None
    correlation_id: str | None = None
    created_at: str | None = None
    persist_db: bool = True


def _require_jsonschema() -> None:
    if Draft202012Validator is None:
        raise RuntimeError('jsonschema is required for prepare-architect-packet; install jsonschema in the producer environment')


def _check(*, check_id: str, passed: bool, message: str, evidence: dict[str, Any], severity: str = 'blocker') -> PacketPreparationCheck:
    return PacketPreparationCheck(
        check_id=check_id,
        status='pass' if passed else 'fail',
        severity=severity,
        message=message,
        evidence=evidence,
    )


def _unique_json_like(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for item in items:
        marker = json.dumps(item, sort_keys=True, default=str)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out


def _query_single_row(sql: str) -> list[str] | None:
    rows = query_rows(sql)
    return rows[0] if rows else None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _resolve_packet_schema_path(explicit: Path | None = None) -> Path:
    candidates = [explicit, DEFAULT_ARCHITECT_PACKET_SCHEMA_PATH]
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = candidate.expanduser().resolve()
        if resolved.exists():
            return resolved
    raise FileNotFoundError('No architect_cycle_packet schema found.')


def _resolve_coder_brief_schema_path() -> Path:
    resolved = DEFAULT_CODER_BRIEF_SCHEMA_PATH.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError('No coder_run_brief schema found.')
    return resolved


def _validate_packet(packet: dict[str, Any], schema_path: Path) -> None:
    _require_jsonschema()
    validator_cls = Draft202012Validator
    if validator_cls is None:  # pragma: no cover - narrowed by _require_jsonschema
        raise RuntimeError('jsonschema validator unavailable')
    validator_cls(_load_json(schema_path)).validate(packet)


def _resolve_brief_context(*, project_slug: str, package_id_external: str) -> PacketBriefContext:
    sql = f"""
    SELECT
      cb.coder_run_brief_id::text,
      p.project_id::text,
      p.slug,
      cb.work_item_id::text,
      cb.authority_state::text,
      cb.status::text,
      coalesce(cb.brief_id_external, ''),
      cb.brief_json::text,
      cb.approval_json::text,
      cb.packet_preparation_json::text,
      cb.generated_from_json::text,
      cb.metadata_json::text,
      coalesce(cb.generated_from_json->>'readiness_class', cb.brief_json->'execution_readiness'->>'readiness_class', ''),
      (
        SELECT count(*)::text
        FROM paa.coder_brief_realization_targets t
        WHERE t.coder_run_brief_id = cb.coder_run_brief_id
      )
    FROM paa.coder_run_briefs cb
    JOIN paa.projects p ON p.project_id = cb.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND cb.generated_from_json->>'design_package_id_external' = {sql_literal(package_id_external)}
    ORDER BY cb.created_at DESC
    LIMIT 1;
    """
    row = _query_single_row(sql)
    if row is None:
        raise RuntimeError(f'No coder brief found for {project_slug}:{package_id_external}')
    brief_json = json.loads(row[7])
    return PacketBriefContext(
        coder_run_brief_id=row[0],
        project_id=row[1],
        project_slug=row[2],
        work_item_id=row[3] or None,
        authority_state=row[4],
        status=row[5],
        brief_id_external=row[6],
        brief_json=brief_json,
        approval_json=json.loads(row[8] or '{}'),
        packet_preparation_json=json.loads(row[9] or '{}'),
        generated_from_json=json.loads(row[10] or '{}'),
        metadata_json=json.loads(row[11] or '{}'),
        readiness_class=row[12] or None,
        target_count=int(row[13]),
        component_name=(brief_json.get('component_assignment') or {}).get('component_name') or 'component',
    )


def _architect_role(project_slug: str) -> tuple[str, str]:
    row = _query_single_row(
        f"""
        SELECT r.role_id::text, r.name
        FROM paa.roles r
        JOIN paa.projects p ON p.project_id = r.project_id
        WHERE p.slug = {sql_literal(project_slug)}
          AND r.name = 'Architect'
        LIMIT 1;
        """
    )
    if row is None:
        raise RuntimeError(f'No Architect role found for project {project_slug!r}')
    return row[0], row[1]


def _packet_checks(context: PacketBriefContext, options: PacketPreparationOptions, package: dict[str, Any]) -> list[PacketPreparationCheck]:
    checks = [
        _check(
            check_id='brief_approved',
            passed=context.authority_state in {'approved_brief', 'packet_ready_execution_authority'},
            message='Brief is approved or already packet-ready.' if context.authority_state in {'approved_brief', 'packet_ready_execution_authority'} else 'Brief is not approved for packet preparation.',
            evidence={'authority_state': context.authority_state},
        ),
        _check(
            check_id='targets_materialized',
            passed=context.target_count > 0,
            message='Brief realization targets are materialized.' if context.target_count > 0 else 'Brief has no realization targets.',
            evidence={'target_count': context.target_count},
        ),
        _check(
            check_id='baseline_file_present',
            passed=options.baseline_file.exists(),
            message='Baseline summary file is present.' if options.baseline_file.exists() else 'Baseline summary file is missing.',
            evidence={'baseline_file': str(options.baseline_file)},
        ),
        _check(
            check_id='manifest_file_present',
            passed=options.manifest_path.exists(),
            message='Manifest/authority path is present.' if options.manifest_path.exists() else 'Manifest/authority path is missing.',
            evidence={'manifest_path': str(options.manifest_path)},
        ),
        _check(
            check_id='package_authority_context_complete',
            passed=all((package.get('authority_context') or {}).get(key) for key in ('authority_version', 'milestone_id', 'phase_id', 'task_id')),
            message='Package authority context is complete.' if all((package.get('authority_context') or {}).get(key) for key in ('authority_version', 'milestone_id', 'phase_id', 'task_id')) else 'Package authority context is incomplete for architect packet preparation.',
            evidence={'authority_context': package.get('authority_context') or {}},
        ),
        _check(
            check_id='brief_output_path_declared',
            passed=bool(str(options.brief_output_path)),
            message='Packet-ready brief output path is declared.',
            evidence={'brief_output_path': str(options.brief_output_path)},
        ),
        _check(
            check_id='packet_output_path_declared',
            passed=bool(str(options.packet_output_path)),
            message='Architect packet output path is declared.',
            evidence={'packet_output_path': str(options.packet_output_path)},
        ),
    ]
    return checks


def _derive_packet_ready_brief_json(context: PacketBriefContext, options: PacketPreparationOptions) -> dict[str, Any]:
    brief = copy.deepcopy(context.brief_json)
    execution_readiness = dict(brief.get('execution_readiness') or {})
    dependency_readiness = list(execution_readiness.get('dependency_readiness') or [])
    dependency_readiness.extend([
        'brief approved',
        'packet preparation checks passed',
    ])
    execution_readiness.update({
        'readiness_class': 'execution_ready',
        'dependency_readiness': _unique_json_like(dependency_readiness),
        'blocking_causes': [],
        'recommended_next_owner': 'Python Team',
        'readiness_snapshot_source': f"packet-preparation-{datetime.now(timezone.utc).date().isoformat()}",
    })
    brief['execution_readiness'] = execution_readiness

    authority_context = dict(brief.get('authority_context') or {})
    authority_context.update({
        'issue_number': options.next_issue_number,
        'pr_number': options.accepted_pr_number,
    })
    brief['authority_context'] = authority_context
    return brief


def _write_packet_ready_brief(brief_json: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(brief_json, indent=2) + '\n')


def _build_authority_context(package: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    auth = package['authority_context']
    return {
        'manifest_path': str(manifest_path),
        'authority_version': auth['authority_version'],
        'milestone_id': auth['milestone_id'],
        'phase_id': auth['phase_id'],
        'task_id': auth['task_id'],
        'issue_number': auth.get('issue_number'),
        'task_title': auth.get('task_title'),
    }


def _build_packet(*, context: PacketBriefContext, package: dict[str, Any], options: PacketPreparationOptions, brief_output_path: Path, brief_schema_path: Path, packet_schema_path: Path, packet_ready_brief_json: dict[str, Any], effective_authority_state: str) -> dict[str, Any]:
    baseline = _load_json(options.baseline_file)
    created_at = options.created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    selected = {
        'brief_id_external': context.brief_id_external,
        'brief_json': packet_ready_brief_json,
        'readiness_state': (packet_ready_brief_json.get('execution_readiness') or {}).get('readiness_class') or context.readiness_class,
        'parallel_group_id': None,
    }
    payload = {
        'message_id': options.message_id or f"paa-arch-{datetime.now(timezone.utc).date().isoformat()}-issue{options.next_issue_number}-{package['authority_context']['task_id']}",
        'schema_type': 'architect_cycle_packet',
        'schema_version': '1.0.0',
        'project': options.packet_project or context.project_slug,
        'from_role': 'architect',
        'to_role': 'python-team',
        'created_at': created_at,
        'correlation_id': options.correlation_id or f"issue-{options.next_issue_number}",
        'github_context': {
            'repo': options.repo,
            'issue_number': options.next_issue_number,
            'pr_number': options.accepted_pr_number,
            'branch': options.branch,
            'links': [options.accepted_pr_url, options.closed_issue_url, options.next_issue_url],
        },
        'payload': {
            'accepted_pr': {
                'number': options.accepted_pr_number,
                'url': options.accepted_pr_url,
            },
            'closed_issue': {
                'number': options.closed_issue_number,
                'url': options.closed_issue_url,
            },
            'next_issue': {
                'number': options.next_issue_number,
                'url': options.next_issue_url,
            },
            'current_baseline': baseline,
            'remaining_gap': options.remaining_gap or derive_remaining_gap(None, package),
            'next_move': unique_preserving_order(list(options.next_move) + derive_next_move(selected, options.next_issue_number)),
            'focus': unique_preserving_order(list(options.focus) + derive_focus(selected, package)),
            'keep_stable': unique_preserving_order(list(options.keep_stable) + derive_keep_stable(package)),
            'governance_reminder': unique_preserving_order(list(options.governance_reminder) + derive_governance_reminders()),
            'coder_run_brief_ref': {
                'path': str(brief_output_path),
                'schema_path': str(brief_schema_path),
                'brief_id': packet_ready_brief_json['brief_id'],
            },
            'coder_run_brief': packet_ready_brief_json,
            'coder_brief_resolution': {
                'package_id_external': package['package_id'],
                'brief_id_external': context.brief_id_external,
                'readiness_state': selected['readiness_state'],
                'parallel_group_id': None,
                'authority_state': effective_authority_state,
            },
            'pr_starter': {
                'branch': options.pr_starter_branch,
                'title': options.pr_starter_title,
                'body_linkage': options.pr_starter_body_linkage,
            } if any([options.pr_starter_branch, options.pr_starter_title, options.pr_starter_body_linkage]) else None,
        },
        'authority_context': _build_authority_context(package, options.manifest_path),
    }
    _validate_packet(payload, packet_schema_path)
    return payload


def _persist_packet_ready_transition(*, context: PacketBriefContext, packet_ready_brief_json: dict[str, Any], actor_role_id: str, actor_name: str, packet_output_path: Path, review_output_path: Path | None, brief_output_path: Path, message_id: str, evidence: dict[str, Any]) -> None:
    packet_prep = {
        'current_state': 'packet_ready_execution_authority',
        'packet_ready': True,
        'message_id': message_id,
        'packet_output_path': str(packet_output_path),
        'review_output_path': str(review_output_path) if review_output_path else None,
        'brief_output_path': str(brief_output_path),
        'prepared_by_role': actor_name,
    }
    sql = f"""
    BEGIN;

    UPDATE paa.coder_run_briefs
    SET
      authority_state = 'packet_ready_execution_authority'::paa.coder_brief_authority_state,
      authority_state_updated_at = now(),
      status = 'active'::paa.coder_brief_status,
      packet_ready_at = now(),
      brief_json = {sql_literal(json.dumps(packet_ready_brief_json, sort_keys=True))}::jsonb,
      generated_from_json = coalesce(generated_from_json, '{{}}'::jsonb) || '{{"readiness_class":"execution_ready"}}'::jsonb,
      packet_preparation_json = {sql_literal(json.dumps(packet_prep, sort_keys=True))}::jsonb,
      updated_at = now()
    WHERE coder_run_brief_id = {sql_literal(context.coder_run_brief_id)}::uuid;

    INSERT INTO paa.coder_brief_authority_events (
      project_id,
      work_item_id,
      coder_run_brief_id,
      from_state,
      to_state,
      transition_kind,
      actor_role_id,
      actor_name,
      notes,
      evidence_json
    )
    VALUES (
      {sql_literal(context.project_id)}::uuid,
      {('NULL' if context.work_item_id is None else sql_literal(context.work_item_id) + '::uuid')},
      {sql_literal(context.coder_run_brief_id)}::uuid,
      {sql_literal(context.authority_state)}::paa.coder_brief_authority_state,
      'packet_ready_execution_authority'::paa.coder_brief_authority_state,
      'mark_packet_ready'::paa.coder_brief_authority_transition_kind,
      {sql_literal(actor_role_id)}::uuid,
      {sql_literal(actor_name)},
      'Packet prepared through producer-side packet readiness flow.',
      {sql_literal(json.dumps(evidence, sort_keys=True))}::jsonb
    );

    COMMIT;
    """
    run_psql(sql)


def _refresh_packet_ready_metadata(*, coder_run_brief_id: str, packet_ready_brief_json: dict[str, Any], packet_output_path: Path, review_output_path: Path | None, brief_output_path: Path, message_id: str) -> None:
    packet_prep = {
        'current_state': 'packet_ready_execution_authority',
        'packet_ready': True,
        'message_id': message_id,
        'packet_output_path': str(packet_output_path),
        'review_output_path': str(review_output_path) if review_output_path else None,
        'brief_output_path': str(brief_output_path),
    }
    sql = f"""
    UPDATE paa.coder_run_briefs
    SET
      brief_json = {sql_literal(json.dumps(packet_ready_brief_json, sort_keys=True))}::jsonb,
      generated_from_json = coalesce(generated_from_json, '{{}}'::jsonb) || '{{"readiness_class":"execution_ready"}}'::jsonb,
      packet_preparation_json = {sql_literal(json.dumps(packet_prep, sort_keys=True))}::jsonb,
      updated_at = now()
    WHERE coder_run_brief_id = {sql_literal(coder_run_brief_id)}::uuid;
    """
    run_psql(sql)


def prepare_architect_packet(*, options: PacketPreparationOptions) -> PreparedArchitectPacketResult:
    package = validate_stage1_design_package(options.package_path, _resolve_stage1_schema_path())
    project_slug = options.project_slug or (package.get('authority_context') or {}).get('project_slug') or (package.get('authority_context') or {}).get('project_id')
    if not project_slug:
        raise RuntimeError('Packet preparation requires a resolvable project_slug from options or package authority_context.')
    context = _resolve_brief_context(project_slug=project_slug, package_id_external=package['package_id'])
    checks = _packet_checks(context, options, package)
    blockers = [check for check in checks if check.status == 'fail' and check.severity == 'blocker']
    if blockers:
        raise RuntimeError('; '.join(check.message for check in blockers))

    packet_schema_path = _resolve_packet_schema_path(options.schema_path)
    brief_schema_path = _resolve_coder_brief_schema_path()
    brief_output_path = options.brief_output_path.expanduser().resolve()
    packet_output_path = options.packet_output_path.expanduser().resolve()
    review_output_path = options.review_output_path.expanduser().resolve() if options.review_output_path else None

    packet_ready_brief_json = _derive_packet_ready_brief_json(context, options)
    _write_packet_ready_brief(packet_ready_brief_json, brief_output_path)
    packet = _build_packet(
        context=context,
        package=package,
        options=options,
        brief_output_path=brief_output_path,
        brief_schema_path=brief_schema_path,
        packet_schema_path=packet_schema_path,
        packet_ready_brief_json=packet_ready_brief_json,
        effective_authority_state='packet_ready_execution_authority',
    )
    packet_output_path.parent.mkdir(parents=True, exist_ok=True)
    packet_output_path.write_text(json.dumps(packet, indent=2) + '\n')
    review_markdown = None
    if review_output_path is not None:
        review_output_path.parent.mkdir(parents=True, exist_ok=True)
        write_review_markdown(review_output_path, packet)
        review_markdown = review_output_path.read_text()

    automation_run_id = None
    if options.persist_db:
        automation_run_id = persist_packet_compilation(
            project_slug=project_slug,
            packet=packet,
            package_id_external=package['package_id'],
            brief_id_external=context.brief_id_external,
            review_markdown=review_markdown,
            output_path=str(packet_output_path),
            review_output_path=str(review_output_path) if review_output_path else None,
            source_input_path=str(options.baseline_file),
        )

    transition_applied = False
    if context.authority_state != 'packet_ready_execution_authority':
        actor_role_id, actor_name = _architect_role(project_slug)
        evidence = {
            'packet_output_path': str(packet_output_path),
            'review_output_path': str(review_output_path) if review_output_path else None,
            'brief_output_path': str(brief_output_path),
            'message_id': packet['message_id'],
            'automation_run_id': automation_run_id,
            'checks': [asdict(check) for check in checks],
        }
        _persist_packet_ready_transition(
            context=context,
            packet_ready_brief_json=packet_ready_brief_json,
            actor_role_id=actor_role_id,
            actor_name=actor_name,
            packet_output_path=packet_output_path,
            review_output_path=review_output_path,
            brief_output_path=brief_output_path,
            message_id=packet['message_id'],
            evidence=evidence,
        )
        transition_applied = True
        context = _resolve_brief_context(project_slug=project_slug, package_id_external=package['package_id'])
    elif options.persist_db:
        _refresh_packet_ready_metadata(
            coder_run_brief_id=context.coder_run_brief_id,
            packet_ready_brief_json=packet_ready_brief_json,
            packet_output_path=packet_output_path,
            review_output_path=review_output_path,
            brief_output_path=brief_output_path,
            message_id=packet['message_id'],
        )
        context = _resolve_brief_context(project_slug=project_slug, package_id_external=package['package_id'])

    packet_prep_json = {
        **context.packet_preparation_json,
        'packet_output_path': str(packet_output_path),
        'review_output_path': str(review_output_path) if review_output_path else None,
        'brief_output_path': str(brief_output_path),
        'message_id': packet['message_id'],
        'automation_run_id': automation_run_id or None,
    }
    return PreparedArchitectPacketResult(
        project_slug=project_slug,
        package_id_external=package['package_id'],
        coder_run_brief_id=context.coder_run_brief_id,
        brief_id_external=context.brief_id_external,
        authority_state=context.authority_state,
        status=context.status,
        transition_applied=transition_applied,
        packet_output_path=str(packet_output_path),
        brief_output_path=str(brief_output_path),
        review_output_path=str(review_output_path) if review_output_path else None,
        packet_schema_path=str(packet_schema_path),
        brief_schema_path=str(brief_schema_path),
        message_id=packet['message_id'],
        target_count=context.target_count,
        packet_preparation_json=packet_prep_json,
        checks=[asdict(check) for check in checks],
    )
