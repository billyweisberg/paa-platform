"""Producer-side governed review and approval for coder briefs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from paa_core.db import query_rows, run_psql, sql_literal

from paa_core.producer.coder_brief_assembler import assemble_coder_brief
from paa_core.producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


DECISION_TO_TARGET_STATE = {
    'approve': 'approved_brief',
    'reject': 'rejected_authority',
    'reopen-draft': 'draft_brief',
}

DECISION_TO_TRANSITION_KIND = {
    'approve': 'approve_brief',
    'reject': 'reject_brief',
    'reopen-draft': 'reopen_draft',
}

DECISION_ALLOWED_FROM_STATES = {
    'approve': {'draft_brief'},
    'reject': {'draft_brief', 'approved_brief'},
    'reopen-draft': {'rejected_authority'},
}

DECISION_TO_STATUS = {
    'approve': 'approved',
    'reject': 'rejected',
    'reopen-draft': 'draft',
}


@dataclass(frozen=True)
class ReviewCheck:
    check_id: str
    status: str
    severity: str
    message: str
    evidence: dict[str, Any]


@dataclass(frozen=True)
class ReviewCoderBriefResult:
    project_slug: str
    coder_run_brief_id: str
    brief_id: str
    authority_state: str
    status: str
    decision: str
    transition_applied: bool
    target_count: int
    approval_json: dict[str, Any]
    output_path: str | None
    checks: list[dict[str, Any]]


@dataclass(frozen=True)
class BriefContext:
    coder_run_brief_id: str
    project_id: str
    project_slug: str
    work_item_id: str | None
    authority_state: str
    status: str
    brief_id: str
    approval_json: dict[str, Any]
    packet_preparation_json: dict[str, Any]
    readiness_class: str | None
    target_count: int


def _check(*, check_id: str, passed: bool, message: str, evidence: dict[str, Any], severity: str = 'blocker') -> ReviewCheck:
    return ReviewCheck(
        check_id=check_id,
        status='pass' if passed else 'fail',
        severity=severity,
        message=message,
        evidence=evidence,
    )


def _query_single_row(sql: str) -> list[str] | None:
    rows = query_rows(sql)
    return rows[0] if rows else None


def _resolve_brief_context(*, coder_run_brief_id: str | None, design_package_path: Path | None) -> BriefContext:
    resolved_brief_id = coder_run_brief_id
    if resolved_brief_id is None:
        if design_package_path is None:
            raise RuntimeError('review-coder-brief requires --coder-run-brief-id or --design-package')
        assembled = assemble_coder_brief(package_path=design_package_path, persist_db=True)
        resolved_brief_id = assembled.coder_run_brief_id

    sql = f"""
    SELECT
      cb.coder_run_brief_id::text,
      p.project_id::text,
      p.slug,
      cb.work_item_id::text,
      cb.authority_state::text,
      cb.status::text,
      coalesce(cb.brief_id_external, ''),
      cb.approval_json::text,
      cb.packet_preparation_json::text,
      coalesce(cb.generated_from_json->>'readiness_class', cb.brief_json->'execution_readiness'->>'readiness_class', ''),
      (
        SELECT count(*)::text
        FROM paa.coder_brief_realization_targets t
        WHERE t.coder_run_brief_id = cb.coder_run_brief_id
      )
    FROM paa.coder_run_briefs cb
    JOIN paa.projects p ON p.project_id = cb.project_id
    WHERE cb.coder_run_brief_id = {sql_literal(resolved_brief_id)}::uuid
    LIMIT 1;
    """
    row = _query_single_row(sql)
    if row is None:
        raise RuntimeError(f'No coder_run_brief found for {resolved_brief_id}')
    return BriefContext(
        coder_run_brief_id=row[0],
        project_id=row[1],
        project_slug=row[2],
        work_item_id=row[3] or None,
        authority_state=row[4],
        status=row[5],
        brief_id=row[6],
        approval_json=json.loads(row[7] or '{}'),
        packet_preparation_json=json.loads(row[8] or '{}'),
        readiness_class=row[9] or None,
        target_count=int(row[10]),
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


def _review_checks(context: BriefContext, decision: str) -> list[ReviewCheck]:
    checks = [
        _check(
            check_id='decision_supported',
            passed=decision in DECISION_TO_TARGET_STATE,
            message='Requested review decision is supported.' if decision in DECISION_TO_TARGET_STATE else 'Requested review decision is not supported.',
            evidence={'decision': decision},
        ),
        _check(
            check_id='state_transition_allowed',
            passed=context.authority_state in DECISION_ALLOWED_FROM_STATES.get(decision, set()),
            message='Current authority state may transition under this decision.' if context.authority_state in DECISION_ALLOWED_FROM_STATES.get(decision, set()) else 'Current authority state does not permit this decision.',
            evidence={
                'current_state': context.authority_state,
                'allowed_from_states': sorted(DECISION_ALLOWED_FROM_STATES.get(decision, set())),
            },
        ),
    ]
    if decision == 'approve':
        checks.extend([
            _check(
                check_id='readiness_class_derivation_ready',
                passed=context.readiness_class == 'derivation_ready',
                message='Brief readiness class is derivation_ready.' if context.readiness_class == 'derivation_ready' else 'Brief readiness class is not derivation_ready.',
                evidence={'readiness_class': context.readiness_class},
            ),
            _check(
                check_id='targets_materialized',
                passed=context.target_count > 0,
                message='Brief realization targets are materialized.' if context.target_count > 0 else 'Brief has no materialized realization targets.',
                evidence={'target_count': context.target_count},
            ),
        ])
    return checks


def _noop_checks(context: BriefContext, decision: str) -> list[ReviewCheck]:
    checks = [
        _check(
            check_id='decision_supported',
            passed=decision in DECISION_TO_TARGET_STATE,
            message='Requested review decision is supported.' if decision in DECISION_TO_TARGET_STATE else 'Requested review decision is not supported.',
            evidence={'decision': decision},
        ),
        _check(
            check_id='already_in_target_state',
            passed=True,
            message='Brief is already in the requested authority state; no transition was applied.',
            evidence={
                'current_state': context.authority_state,
                'decision': decision,
            },
            severity='warning',
        ),
    ]
    if decision == 'approve':
        checks.extend([
            _check(
                check_id='readiness_class_derivation_ready',
                passed=context.readiness_class == 'derivation_ready',
                message='Brief readiness class is derivation_ready.' if context.readiness_class == 'derivation_ready' else 'Brief readiness class is not derivation_ready.',
                evidence={'readiness_class': context.readiness_class},
            ),
            _check(
                check_id='targets_materialized',
                passed=context.target_count > 0,
                message='Brief realization targets are materialized.' if context.target_count > 0 else 'Brief has no materialized realization targets.',
                evidence={'target_count': context.target_count},
            ),
        ])
    return checks


def _update_brief_authority(*, context: BriefContext, decision: str, actor_role_id: str, actor_name: str, notes: str | None, review_summary: str | None, evidence: dict[str, Any]) -> None:
    target_state = DECISION_TO_TARGET_STATE[decision]
    target_status = DECISION_TO_STATUS[decision]
    transition_kind = DECISION_TO_TRANSITION_KIND[decision]
    approval_payload = {
        **(context.approval_json or {}),
        'current_state': target_state,
        'decision': decision,
        'review_summary': review_summary,
        'review_notes': notes,
        'reviewed_by_role': actor_name,
        'target_count': context.target_count,
        'approval_required': target_state != 'rejected_authority',
    }
    approved_at_sql = 'now()' if decision == 'approve' else 'NULL'
    sql = f"""
    BEGIN;

    UPDATE paa.coder_run_briefs
    SET
      authority_state = {sql_literal(target_state)}::paa.coder_brief_authority_state,
      authority_state_updated_at = now(),
      status = {sql_literal(target_status)}::paa.coder_brief_status,
      approved_at = CASE
        WHEN {sql_literal(decision)} = 'approve' THEN now()
        WHEN {sql_literal(decision)} = 'reopen-draft' THEN NULL
        ELSE approved_at
      END,
      approval_json = {sql_literal(json.dumps(approval_payload, sort_keys=True))}::jsonb,
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
      {sql_literal(target_state)}::paa.coder_brief_authority_state,
      {sql_literal(transition_kind)}::paa.coder_brief_authority_transition_kind,
      {sql_literal(actor_role_id)}::uuid,
      {sql_literal(actor_name)},
      {sql_literal(notes)},
      {sql_literal(json.dumps(evidence, sort_keys=True))}::jsonb
    );

    COMMIT;
    """
    run_psql(sql)


def review_coder_brief(
    *,
    coder_run_brief_id: str | None = None,
    design_package_path: Path | None = None,
    decision: str,
    notes: str | None = None,
    review_summary: str | None = None,
    output_path: Path | None = None,
) -> ReviewCoderBriefResult:
    resolved_design_package = design_package_path.expanduser().resolve() if design_package_path else None
    if resolved_design_package is not None:
        validate_stage1_design_package(resolved_design_package, _resolve_stage1_schema_path())
    context = _resolve_brief_context(coder_run_brief_id=coder_run_brief_id, design_package_path=resolved_design_package)
    target_state = DECISION_TO_TARGET_STATE[decision]
    if context.authority_state == target_state:
        checks = _noop_checks(context, decision)
        result = ReviewCoderBriefResult(
            project_slug=context.project_slug,
            coder_run_brief_id=context.coder_run_brief_id,
            brief_id=context.brief_id,
            authority_state=context.authority_state,
            status=context.status,
            decision=decision,
            transition_applied=False,
            target_count=context.target_count,
            approval_json=context.approval_json,
            output_path=str(output_path.expanduser().resolve()) if output_path else None,
            checks=[asdict(check) for check in checks],
        )
        if output_path is not None:
            output_path.expanduser().resolve().write_text(json.dumps(asdict(result), indent=2) + '\n')
        return result

    checks = _review_checks(context, decision)
    blockers = [check for check in checks if check.status == 'fail' and check.severity == 'blocker']
    if blockers:
        raise RuntimeError('; '.join(check.message for check in blockers))

    actor_role_id, actor_name = _architect_role(context.project_slug)
    evidence = {
        'decision': decision,
        'review_summary': review_summary,
        'target_count': context.target_count,
        'readiness_class': context.readiness_class,
        'checks': [asdict(check) for check in checks],
    }
    _update_brief_authority(
        context=context,
        decision=decision,
        actor_role_id=actor_role_id,
        actor_name=actor_name,
        notes=notes,
        review_summary=review_summary,
        evidence=evidence,
    )
    refreshed = _resolve_brief_context(coder_run_brief_id=context.coder_run_brief_id, design_package_path=None)
    result = ReviewCoderBriefResult(
        project_slug=refreshed.project_slug,
        coder_run_brief_id=refreshed.coder_run_brief_id,
        brief_id=refreshed.brief_id,
        authority_state=refreshed.authority_state,
        status=refreshed.status,
        decision=decision,
        transition_applied=True,
        target_count=refreshed.target_count,
        approval_json=refreshed.approval_json,
        output_path=str(output_path.expanduser().resolve()) if output_path else None,
        checks=[asdict(check) for check in checks],
    )
    if output_path is not None:
        output_path.expanduser().resolve().write_text(json.dumps(asdict(result), indent=2) + '\n')
    return result
