"""Core workflow framing and escalation synthesis for TechLead runtime state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from paa_core.packet_envelope import normalize_role_name
from paa_core.services.techlead_acceptance_decision import (
    DefaultTechLeadAcceptanceDecisionService,
)
from paa_core.services.techlead_worker_review_routing import (
    DefaultTechLeadWorkerReviewRoutingService,
)


@dataclass(frozen=True)
class RuntimeWorkflowDerivation:
    workflow_stage: str
    owner_role: str
    escalations: list[dict[str, Any]]
    recommended_actions: list[dict[str, Any]]
    unattended_safe: bool


class DefaultRuntimeWorkflowService:
    def __init__(
        self,
        *,
        packet_preview_loader: Callable[..., dict[str, Any] | None],
        newest_packet: Callable[..., dict[str, Any] | None],
        latest_issue_comment: Callable[[dict[str, Any], str], dict[str, Any] | None],
        latest_comment_with_prefixes: Callable[[list[dict[str, Any]], list[str]], dict[str, Any] | None],
        comments_with_prefixes: Callable[[list[dict[str, Any]], list[str]], list[dict[str, Any]]],
        latest_comment_before: Callable[[list[dict[str, Any]], str | None], dict[str, Any] | None],
        comment_is_newer: Callable[[dict[str, Any] | None, str | None], bool],
        qa_packet_superseded: Callable[[dict[str, Any] | None, dict[str, Any] | None], bool],
        action_type_for_role: Callable[[str], str],
        techlead_queue_name: Callable[[], str],
        dev_queue_name: Callable[[], str],
        build_acceptance_decision_request: Callable[..., Any],
        build_worker_review_routing_request: Callable[..., Any],
        resolve_worker_review_stage: Callable[..., str],
        workflow_lifecycle_worker_result_evaluation: Callable[..., Any],
        acceptance_decision_service_factory: Callable[[], Any] | None = None,
        worker_review_routing_service_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._packet_preview_loader = packet_preview_loader
        self._newest_packet = newest_packet
        self._latest_issue_comment = latest_issue_comment
        self._latest_comment_with_prefixes = latest_comment_with_prefixes
        self._comments_with_prefixes = comments_with_prefixes
        self._latest_comment_before = latest_comment_before
        self._comment_is_newer = comment_is_newer
        self._qa_packet_superseded = qa_packet_superseded
        self._action_type_for_role = action_type_for_role
        self._techlead_queue_name = techlead_queue_name
        self._dev_queue_name = dev_queue_name
        self._build_acceptance_decision_request = build_acceptance_decision_request
        self._build_worker_review_routing_request = build_worker_review_routing_request
        self._resolve_worker_review_stage = resolve_worker_review_stage
        self._workflow_lifecycle_worker_result_evaluation = workflow_lifecycle_worker_result_evaluation
        self._acceptance_decision_service_factory = (
            acceptance_decision_service_factory or DefaultTechLeadAcceptanceDecisionService
        )
        self._worker_review_routing_service_factory = (
            worker_review_routing_service_factory or DefaultTechLeadWorkerReviewRoutingService
        )

    def derive_workflow(
        self,
        current_task: dict[str, Any] | None,
        issue: dict[str, Any],
        pr: dict[str, Any] | None,
        qa_packet: dict[str, Any] | None,
        queues: dict[str, Any],
    ) -> RuntimeWorkflowDerivation:
        stage = 'blocked'
        owner = 'Unknown'
        escalations: list[dict[str, Any]] = []
        recommended: list[dict[str, Any]] = []
        unattended_safe = True
        issue_number = current_task['issue_number'] if current_task else None
        pending_dev_packet = self._packet_preview_loader(
            queues,
            issue_number,
            schema_type='slice_result_packet',
            to_role='techlead',
        ) if issue_number else None
        pending_worker_packet = self._packet_preview_loader(
            queues,
            issue_number,
            schema_type='worker_result_packet',
            to_role='techlead',
        ) if issue_number else None
        pending_qa_queue_packet = self._packet_preview_loader(
            queues,
            issue_number,
            schema_type='qa_verification_packet',
            to_role='techlead',
        ) if issue_number else None
        pending_delivery_review_packet = self._packet_preview_loader(
            queues,
            issue_number,
            schema_type='delivery_review_packet',
            to_role='techlead',
        ) if issue_number else None
        pending_assignment_packet = self._packet_preview_loader(
            queues,
            issue_number,
            schema_type='techlead_assignment_packet',
        ) if issue_number else None
        pending_decision_packet = self._packet_preview_loader(
            queues,
            issue_number,
            schema_type='techlead_decision_packet',
        ) if issue_number else None

        issue_comments = issue.get('comments') or []
        pr_comments = (pr or {}).get('comments') or []
        latest_python_handoff = self._latest_issue_comment(issue, 'Python Team handoff:')
        latest_python_update = self._latest_comment_with_prefixes(
            issue_comments,
            [
                'Python Team update after Architect scope rejection:',
                'Python Team correction after Architect scope rejection',
            ],
        )
        latest_qa_handoff = self._latest_issue_comment(issue, 'QA processed')
        latest_qa_review = self._latest_issue_comment(issue, 'QA review status:')
        latest_architect_rejection = self._latest_comment_with_prefixes(
            pr_comments,
            [
                'Architect review:',
                'Architect review on ',
            ],
        )
        architect_rejection_comments = self._comments_with_prefixes(
            pr_comments,
            [
                'Architect review:',
                'Architect review on ',
            ],
        )
        escalation_superseded = self._qa_packet_superseded(qa_packet, pending_dev_packet)
        if qa_packet and not escalation_superseded:
            if self._comment_is_newer(latest_python_handoff, qa_packet.get('created_at')) or self._comment_is_newer(
                latest_python_update,
                qa_packet.get('created_at'),
            ):
                escalation_superseded = True

        architect_rejected_after_qa = (
            qa_packet
            and latest_architect_rejection
            and self._comment_is_newer(latest_architect_rejection, qa_packet.get('created_at'))
            and not escalation_superseded
        )
        architect_rejection_before_rework = self._latest_comment_before(
            architect_rejection_comments,
            (latest_python_update or {}).get('createdAt'),
        )
        reset_required_after_failed_rework = (
            architect_rejection_before_rework
            and latest_python_update
            and latest_qa_review
            and self._comment_is_newer(latest_qa_review, (latest_python_update or {}).get('createdAt'))
            and 'needs_human_review' in ((latest_qa_review or {}).get('body') or '')
        )

        latest_techlead_packet = self._newest_packet(
            pending_decision_packet,
            pending_assignment_packet,
            pending_delivery_review_packet,
            pending_qa_queue_packet,
            pending_worker_packet,
            pending_dev_packet,
        )

        if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'techlead_decision_packet':
            payload = latest_techlead_packet.get('payload') or {}
            target_role = payload.get('target_role') or 'TechLead'
            stage = 'techlead_decision_recorded'
            owner = 'TechLead'
            unattended_safe = False
            escalations.append({
                'event_type': 'techlead_decision_recorded',
                'severity': 'medium',
                'work_item_ref': self._work_item_ref(current_task),
                'summary': 'TechLead has already recorded the next routing or merge decision for the active slice.',
                'details': {
                    'message_id': latest_techlead_packet.get('message_id'),
                    'queue_name': latest_techlead_packet.get('queue_name'),
                    'decision_type': payload.get('decision_type'),
                    'target_role': target_role,
                    'next_assignment_type': payload.get('next_assignment_type'),
                    'source_packet_ref': payload.get('source_packet_ref'),
                },
                'recommended_route': target_role,
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': self._action_type_for_role(target_role),
                'reason': 'TechLead has already recorded the next workflow decision; follow that decision rather than re-deriving the route from older packets.',
                'target_role': target_role,
                'blocking': True,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'techlead_assignment_packet':
            payload = latest_techlead_packet.get('payload') or {}
            target_role = payload.get('target_role') or 'TechLead'
            stage = 'techlead_assignment_issued'
            owner = target_role
            unattended_safe = False
            escalations.append({
                'event_type': 'techlead_assignment_issued',
                'severity': 'medium',
                'work_item_ref': self._work_item_ref(current_task),
                'summary': 'TechLead has issued the next assignment packet for the active slice.',
                'details': {
                    'message_id': latest_techlead_packet.get('message_id'),
                    'queue_name': latest_techlead_packet.get('queue_name'),
                    'assignment_type': payload.get('assignment_type'),
                    'target_role': target_role,
                    'canonical_branch': payload.get('canonical_branch'),
                    'role_branch': payload.get('role_branch'),
                    'allowed_result_types': payload.get('allowed_result_types'),
                },
                'recommended_route': target_role,
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': self._action_type_for_role(target_role),
                'reason': 'TechLead has already issued a concrete assignment packet; the next step is for the target role to claim and execute it.',
                'target_role': target_role,
                'blocking': True,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'qa_verification_packet':
            stage = 'techlead_qa_review_pending'
            owner = 'TechLead'
            unattended_safe = False
            acceptance_decision_result = None
            try:
                acceptance_decision_service = self._acceptance_decision_service_factory()
                acceptance_decision_request = self._build_acceptance_decision_request(
                    current_task=current_task,
                    pr=pr,
                    qa_packet=qa_packet,
                    source_packet=latest_techlead_packet,
                    workflow_stage=stage,
                )
                acceptance_decision_result = acceptance_decision_service.derive_acceptance_decision(
                    acceptance_decision_request
                )
            except Exception:
                acceptance_decision_result = None
            details = {
                'message_id': latest_techlead_packet.get('message_id'),
                'schema_type': latest_techlead_packet.get('schema_type'),
                'queue_name': latest_techlead_packet.get('queue_name'),
            }
            if qa_packet:
                details['verification_status'] = qa_packet.get('verification_status')
            if acceptance_decision_result is not None:
                details.update({
                    'acceptance_decision_supported': acceptance_decision_result.summary.decision_supported,
                    'acceptance_next_decision': acceptance_decision_result.summary.recommended_next_decision,
                    'acceptance_allowed': acceptance_decision_result.summary.acceptance_allowed,
                    'closeout_allowed': acceptance_decision_result.summary.closeout_allowed,
                    'acceptance_blocking_reasons': list(acceptance_decision_result.summary.blocking_reasons),
                    'acceptance_reason': acceptance_decision_result.reason,
                })
            escalations.append({
                'event_type': 'qa_packet_waiting_for_techlead',
                'severity': 'high',
                'work_item_ref': self._work_item_ref(current_task),
                'summary': (
                    acceptance_decision_result.summary.decision_summary
                    if acceptance_decision_result is not None and acceptance_decision_result.summary.decision_summary
                    else 'TechLead has a waiting QA verification result packet to review.'
                ),
                'details': details,
                'recommended_route': 'TechLead',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_techlead',
                'reason': (
                    acceptance_decision_result.summary.decision_summary
                    if acceptance_decision_result is not None and acceptance_decision_result.summary.decision_summary
                    else 'A QA verification packet addressed to TechLead is waiting for a merge, rework, or escalation decision.'
                ),
                'target_role': 'TechLead',
                'blocking': True,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'delivery_review_packet':
            stage = 'techlead_delivery_review_pending'
            owner = 'TechLead'
            unattended_safe = False
            delivery_payload = latest_techlead_packet.get('payload') or {}
            escalations.append({
                'event_type': 'delivery_review_waiting_for_techlead',
                'severity': 'medium',
                'work_item_ref': self._work_item_ref(current_task),
                'summary': 'TechLead has a waiting Delivery Architect review packet to review.',
                'details': {
                    'message_id': latest_techlead_packet.get('message_id'),
                    'schema_type': latest_techlead_packet.get('schema_type'),
                    'queue_name': latest_techlead_packet.get('queue_name'),
                    'review_type': delivery_payload.get('review_type'),
                    'result_type': delivery_payload.get('result_type'),
                    'techlead_action_recommended': delivery_payload.get('techlead_action_recommended'),
                },
                'recommended_route': 'TechLead',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_techlead',
                'reason': 'A Delivery Architect review packet addressed to TechLead is waiting for the next routing decision.',
                'target_role': 'TechLead',
                'blocking': True,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'worker_result_packet':
            worker_payload = latest_techlead_packet.get('payload') or {}
            worker_role = worker_payload.get('worker_role')
            if not worker_role:
                worker_role = normalize_role_name(latest_techlead_packet.get('from_role')) or 'Worker'
            lifecycle_result = None
            try:
                lifecycle_result = self._workflow_lifecycle_worker_result_evaluation(
                    current_task=current_task,
                    packet=latest_techlead_packet,
                )
            except Exception:
                lifecycle_result = None
            lifecycle_target_stage = None
            if lifecycle_result is not None:
                lifecycle_target_stage = (
                    (lifecycle_result.decision_summary.metadata or {}).get('resolved_to_stage')
                    or 'techlead_worker_review_pending'
                )
            review_routing_result = None
            derived_review_stage = self._resolve_worker_review_stage(
                worker_role=worker_role,
                lifecycle_target_stage=lifecycle_target_stage,
            )
            try:
                review_routing_service = self._worker_review_routing_service_factory()
                review_routing_request = self._build_worker_review_routing_request(
                    current_task=current_task,
                    pr=pr,
                    worker_role=worker_role,
                    worker_result_packet=latest_techlead_packet,
                    lifecycle_target_stage=lifecycle_target_stage,
                    workflow_lifecycle_result=lifecycle_result,
                )
                review_routing_result = review_routing_service.derive_worker_review_routing(
                    review_routing_request
                )
            except Exception:
                review_routing_result = None
            routed_workflow_stage = (
                getattr(review_routing_result, 'workflow_stage', None)
                if review_routing_result is not None
                else None
            )
            stage = routed_workflow_stage or derived_review_stage
            if review_routing_result is not None and review_routing_result.summary.review_summary:
                summary = review_routing_result.summary.review_summary
            elif worker_role in {'Dev', 'Python Dev'}:
                summary = 'TechLead has a waiting Dev worker result packet to review before QA is assigned.'
            else:
                summary = f'TechLead has a waiting {worker_role} result packet to review.'
            if worker_role in {'Dev', 'Python Dev'}:
                reason = 'A Dev worker result packet addressed to TechLead is waiting for the next routing decision.'
            else:
                reason = 'A worker result packet addressed to TechLead is waiting for the next routing decision.'
            owner = 'TechLead'
            unattended_safe = False
            details = {
                'message_id': latest_techlead_packet.get('message_id'),
                'schema_type': latest_techlead_packet.get('schema_type'),
                'queue_name': latest_techlead_packet.get('queue_name'),
                'worker_role': worker_role,
                'worker_family': worker_payload.get('worker_family'),
                'result_type': worker_payload.get('result_type'),
                'techlead_action_recommended': worker_payload.get('techlead_action_recommended'),
            }
            if review_routing_result is not None:
                details.update({
                    'review_routing_decision_supported': review_routing_result.summary.decision_supported,
                    'review_routing_next_decision': review_routing_result.summary.recommended_next_decision,
                    'review_routing_target_role': review_routing_result.summary.recommended_target_role,
                    'review_routing_qa_allowed': review_routing_result.summary.qa_assignment_allowed,
                    'review_routing_blocking_reasons': list(review_routing_result.summary.blocking_reasons),
                    'review_routing_reason': review_routing_result.reason,
                })
            if lifecycle_result is not None:
                details.update({
                    'workflow_transition_allowed': lifecycle_result.decision_summary.transition_allowed,
                    'workflow_blocking_reasons': list(lifecycle_result.decision_summary.blocking_reasons),
                    'workflow_notes': list(lifecycle_result.decision_summary.notes),
                    'workflow_recommended_next_action': lifecycle_result.recommended_next_action,
                    'workflow_target_stage': lifecycle_target_stage,
                })
            escalations.append({
                'event_type': 'worker_packet_waiting_for_techlead',
                'severity': 'medium',
                'work_item_ref': self._work_item_ref(current_task),
                'summary': summary,
                'details': details,
                'recommended_route': 'TechLead',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': self._action_type_for_role(
                    review_routing_result.summary.recommended_target_role
                    if review_routing_result is not None and review_routing_result.summary.recommended_target_role
                    else 'TechLead'
                ),
                'reason': (
                    review_routing_result.summary.review_summary
                    if review_routing_result is not None and review_routing_result.summary.review_summary
                    else reason
                ),
                'target_role': (
                    review_routing_result.summary.recommended_target_role
                    if review_routing_result is not None and review_routing_result.summary.recommended_target_role
                    else 'TechLead'
                ),
                'blocking': True,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'slice_result_packet':
            stage = 'techlead_dev_review_pending'
            owner = 'TechLead'
            unattended_safe = False
            escalations.append({
                'event_type': 'dev_packet_waiting_for_techlead',
                'severity': 'medium',
                'work_item_ref': self._work_item_ref(current_task),
                'summary': 'TechLead has a waiting Dev result packet to review before QA is assigned.',
                'details': {
                    'message_id': latest_techlead_packet.get('message_id'),
                    'schema_type': latest_techlead_packet.get('schema_type'),
                    'queue_name': latest_techlead_packet.get('queue_name'),
                },
                'recommended_route': 'TechLead',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_techlead',
                'reason': 'A Dev result packet addressed to TechLead is waiting for the next routing decision.',
                'target_role': 'TechLead',
                'blocking': True,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        architecture_queue = queues.get(self._techlead_queue_name()) or queues.get('fractal-core-architecture') or {}
        if architecture_queue.get('messages_ready', 0) > 0:
            stage = 'ready_for_acceptance'
            owner = 'Architect'
            unattended_safe = False
            preview = architecture_queue.get('preview') or []
            packet = preview[0]['payload_preview'] if preview else {}
            details = {
                'message_id': packet.get('message_id_external', packet.get('message_id')),
                'schema_type': packet.get('schema_type'),
            }
            payload = packet.get('payload', {}) if isinstance(packet, dict) else {}
            if payload.get('verification_status'):
                details['verification_status'] = payload.get('verification_status')
            escalations.append({
                'event_type': 'architect_packet_waiting',
                'severity': 'high',
                'work_item_ref': self._work_item_ref(current_task),
                'summary': 'Architect queue has a waiting packet.',
                'details': details,
                'recommended_route': 'Architect',
                'status': 'open',
            })
            if reset_required_after_failed_rework:
                escalations.append({
                    'event_type': 'reset_branch_recommended',
                    'severity': 'high',
                    'work_item_ref': self._work_item_ref(current_task),
                    'summary': 'The current slice has repeated the same scope failure after an in-place narrowing attempt; a reset branch recovery should be chosen instead of another incremental cleanup pass.',
                    'details': {
                        'architect_rejection_comment_at': (architect_rejection_before_rework or {}).get('createdAt'),
                        'python_rework_comment_at': (latest_python_update or {}).get('createdAt'),
                        'qa_repeat_review_comment_at': (latest_qa_review or {}).get('createdAt'),
                    },
                    'recommended_route': 'Architect',
                    'status': 'open',
                })
                recommended.insert(0, {
                    'priority': 1,
                    'action_type': 'route_to_architect_for_reset_decision',
                    'reason': 'A repeated QA scope escalation after an Architect-directed rework indicates branch contamination; Architect should record a reset-branch recovery decision instead of requesting another in-place cleanup.',
                    'target_role': 'Architect',
                    'blocking': True,
                })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_architect',
                'reason': 'Architect queue has a waiting acceptance packet.',
                'target_role': 'Architect',
                'blocking': True,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if qa_packet and escalation_superseded and issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
            stage = 'qa_pending'
            owner = 'QA'
            unattended_safe = False
            escalations.append({
                'event_type': 'qa_escalation_superseded',
                'severity': 'low',
                'work_item_ref': self._work_item_ref(current_task),
                'summary': 'A newer Python rework/handoff has superseded the earlier QA escalation for this issue.',
                'details': {
                    'superseded_qa_packet_id': qa_packet.get('message_id'),
                    'latest_python_handoff_comment_at': (latest_python_handoff or {}).get('createdAt'),
                    'latest_python_update_comment_at': (latest_python_update or {}).get('createdAt'),
                    'latest_qa_handoff_comment_at': (latest_qa_handoff or {}).get('createdAt'),
                },
                'recommended_route': 'QA',
                'status': 'suppressed',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_qa',
                'reason': 'Python has posted a newer narrowed handoff for the same issue; fresh QA verification is the next step.',
                'target_role': 'QA',
                'blocking': True,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if architect_rejected_after_qa and issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
            assert qa_packet is not None
            stage = 'dev_reset_required' if reset_required_after_failed_rework else 'dev_rework_required'
            owner = 'Dev'
            unattended_safe = False
            if reset_required_after_failed_rework:
                escalations.append({
                    'event_type': 'reset_branch_required',
                    'severity': 'high',
                    'work_item_ref': self._work_item_ref(current_task),
                    'summary': 'The issue has repeated the same scope failure after an in-place rework. The correct recovery is a clean reset branch from main, not another incremental narrowing pass.',
                    'details': {
                        'qa_packet_id': qa_packet.get('message_id'),
                        'verification_status': qa_packet.get('verification_status'),
                        'architect_comment_at': (architect_rejection_before_rework or {}).get('createdAt'),
                        'architect_comment_url': (architect_rejection_before_rework or {}).get('url'),
                        'python_rework_comment_at': (latest_python_update or {}).get('createdAt'),
                        'qa_repeat_review_comment_at': (latest_qa_review or {}).get('createdAt'),
                    },
                    'recommended_route': 'Dev',
                    'status': 'open',
                })
                recommended.append({
                    'priority': 1,
                    'action_type': 'route_to_dev_reset_branch',
                    'reason': 'A second QA scope escalation after Architect-directed rework is a reliable contamination signal; rebuild the slice on a fresh branch from current main.',
                    'target_role': 'Dev',
                    'blocking': True,
                })
            else:
                escalations.append({
                    'event_type': 'architect_rejection_recorded',
                    'severity': 'high',
                    'work_item_ref': self._work_item_ref(current_task),
                    'summary': 'Architect has already reviewed the QA escalation and rejected the current PR head pending a narrower rework.',
                    'details': {
                        'qa_packet_id': qa_packet.get('message_id'),
                        'verification_status': qa_packet.get('verification_status'),
                        'architect_comment_at': (latest_architect_rejection or {}).get('createdAt'),
                        'architect_comment_url': (latest_architect_rejection or {}).get('url'),
                    },
                    'recommended_route': 'Dev',
                    'status': 'open',
                })
                recommended.append({
                    'priority': 1,
                    'action_type': 'route_to_dev',
                    'reason': 'Architect has already rejected the current head and asked for the slice to be narrowed before any fresh QA review.',
                    'target_role': 'Dev',
                    'blocking': True,
                })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if qa_packet and issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
            verdict = qa_packet.get('verification_status')
            if verdict == 'needs_human_review' and not escalation_superseded:
                stage = 'techlead_qa_review_pending'
                owner = 'TechLead'
                unattended_safe = False
                assert qa_packet is not None
                escalations.append({
                    'event_type': 'qa_escalation_pending',
                    'severity': 'high',
                    'work_item_ref': self._work_item_ref(current_task),
                    'summary': 'QA has escalated the active slice for Architect review.',
                    'details': {
                        'qa_packet_id': qa_packet.get('message_id'),
                        'verification_status': verdict,
                        'recommended_action': qa_packet.get('recommended_action', {}),
                        'scope': qa_packet.get('technical_scope_checks', {}),
                        'path': qa_packet.get('path'),
                    },
                    'recommended_route': 'TechLead',
                    'status': 'open',
                })
                recommended.append({
                    'priority': 1,
                    'action_type': 'route_to_techlead',
                    'reason': 'QA marked the current slice needs_human_review and TechLead should make the next routing decision.',
                    'target_role': 'TechLead',
                    'blocking': True,
                })
                return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)
            if verdict == 'pass':
                stage = 'techlead_qa_review_pending'
                owner = 'TechLead'
                unattended_safe = False
                assert qa_packet is not None
                acceptance_decision_result = None
                try:
                    acceptance_decision_service = self._acceptance_decision_service_factory()
                    acceptance_decision_request = self._build_acceptance_decision_request(
                        current_task=current_task,
                        pr=pr,
                        qa_packet=qa_packet,
                        source_packet=qa_packet,
                        workflow_stage=stage,
                    )
                    acceptance_decision_result = acceptance_decision_service.derive_acceptance_decision(
                        acceptance_decision_request
                    )
                except Exception:
                    acceptance_decision_result = None
                escalations.append({
                    'event_type': 'qa_pass_pending_acceptance',
                    'severity': 'medium',
                    'work_item_ref': self._work_item_ref(current_task),
                    'summary': (
                        acceptance_decision_result.summary.decision_summary
                        if acceptance_decision_result is not None and acceptance_decision_result.summary.decision_summary
                        else 'QA passed the active slice, but Architect acceptance is still pending.'
                    ),
                    'details': {
                        'qa_packet_id': qa_packet.get('message_id'),
                        'path': qa_packet.get('path'),
                        'acceptance_decision_supported': (
                            acceptance_decision_result.summary.decision_supported
                            if acceptance_decision_result is not None
                            else None
                        ),
                        'acceptance_next_decision': (
                            acceptance_decision_result.summary.recommended_next_decision
                            if acceptance_decision_result is not None
                            else None
                        ),
                    },
                    'recommended_route': 'TechLead',
                    'status': 'open',
                })
                recommended.append({
                    'priority': 1,
                    'action_type': 'route_to_techlead',
                    'reason': (
                        acceptance_decision_result.summary.decision_summary
                        if acceptance_decision_result is not None and acceptance_decision_result.summary.decision_summary
                        else 'QA pass is recorded locally, and TechLead should decide whether the slice is ready for merge preparation.'
                    ),
                    'target_role': 'TechLead',
                    'blocking': True,
                })
                return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        dev_queue = queues.get(self._dev_queue_name()) or queues.get('fractal-core-python') or {}
        if dev_queue.get('messages_ready', 0) > 0:
            stage = 'architect_authorized'
            owner = 'Dev'
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_dev',
                'reason': 'Python queue has a waiting Architect packet.',
                'target_role': 'Dev',
                'blocking': False,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
            stage = 'dev_in_progress'
            owner = 'Dev'
            recommended.append({
                'priority': 2,
                'action_type': 'monitor_dev',
                'reason': f'Issue #{issue["number"]} has an open PR but no waiting queue handoff.',
                'target_role': 'Dev',
                'blocking': False,
            })
            return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

        if current_task:
            stage = 'dev_in_progress'
            owner = 'Dev'

        return RuntimeWorkflowDerivation(stage, owner, escalations, recommended, unattended_safe)

    @staticmethod
    def _work_item_ref(current_task: dict[str, Any] | None) -> dict[str, Any] | None:
        if current_task is None:
            return None
        return {
            'issue_number': current_task.get('issue_number'),
            'task_id': current_task.get('task_id'),
        }

    @staticmethod
    def apply_terminal_lineage_override(
        *,
        local_decision_packet: dict[str, Any] | None,
        queues: dict[str, Any],
        issue: dict[str, Any] | None,
        pr: dict[str, Any] | None,
        workflow_stage: str,
        owner_role: str,
        recommended: list[dict[str, Any]],
        unattended_safe: bool,
    ) -> tuple[str, str, list[dict[str, Any]], bool]:
        if not local_decision_packet:
            return workflow_stage, owner_role, recommended, unattended_safe
        payload = local_decision_packet.get('payload') or {}
        if payload.get('lineage_state') != 'closed':
            return workflow_stage, owner_role, recommended, unattended_safe
        if any((queue_data.get('preview') or []) for queue_data in queues.values()):
            return workflow_stage, owner_role, recommended, unattended_safe
        latest_lineage_action = payload.get('lineage_action')
        if latest_lineage_action == 'proof_only_closed':
            return 'proof_only_closed', 'TechLead', [], True
        if pr and pr.get('mergedAt') and (issue and (issue.get('state') or '').upper() == 'CLOSED'):
            return 'techlead_decision_recorded', 'TechLead', [], True
        return workflow_stage, owner_role, recommended, unattended_safe

    @staticmethod
    def parse_created_at(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except Exception:
            return None


__all__ = [
    'DefaultRuntimeWorkflowService',
    'RuntimeWorkflowDerivation',
]
