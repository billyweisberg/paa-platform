from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_dev_review_markdown(path: Path, packet: dict[str, Any]) -> None:
    brief = packet['payload']['coder_run_brief']
    review = [
        f"# Slice Result Packet Review: {packet['message_id']}",
        '',
        '## Component',
        f"- component: `{brief['component_assignment']['component_name']}`",
        f"- role: `{brief['component_assignment']['component_role']}`",
        f"- layer: `{brief['component_assignment']['system_layer']}`",
        '',
        '## GitHub context',
        f"- issue: `#{packet['payload']['issue']['number']}`",
        f"- PR: `#{packet['payload']['pr']['number']}`",
        f"- branch: `{packet['payload']['branch']['name']}`",
        '',
        '## Mechanism changed',
        json.dumps(packet['payload']['mechanism_changed'], indent=2),
        '',
        '## Validation',
        json.dumps(packet['payload']['validation'], indent=2),
        '',
        '## Protected baseline',
    ]
    review.extend([f"- {item}" for item in brief.get('behavioral_contract', {}).get('must_not_change', [])])
    review.extend([
        '',
        '## Architect decision needed',
        f"- {packet['payload']['architect_decision_needed']}",
    ])
    path.write_text('\n'.join(review) + '\n')


def write_qa_review_markdown(path: Path, packet: dict[str, Any]) -> None:
    review = [
        f"# QA Verification Packet Review: {packet['message_id']}",
        '',
        '## GitHub context',
        f"- issue: `#{packet['payload']['issue']['number']}`",
        f"- PR: `#{packet['payload']['pr']['number']}`",
        f"- verification_status: `{packet['payload']['verification_status']}`",
        '',
        '## Verification scope',
        json.dumps(packet['payload']['verification_scope'], indent=2),
        '',
        '## Technical scope checks',
        json.dumps(packet['payload']['technical_scope_checks'], indent=2),
        '',
        '## Protected path checks',
        json.dumps(packet['payload']['protected_path_checks'], indent=2),
        '',
        '## Findings',
        json.dumps(packet['payload']['findings'], indent=2),
        '',
        '## Recommended action',
        json.dumps(packet['payload']['recommended_action'], indent=2),
    ]
    path.write_text('\n'.join(review) + '\n')


def write_worker_result_review_markdown(path: Path, packet: dict[str, Any]) -> None:
    payload = packet['payload']
    review = [
        f"# Worker Result Packet Review: {packet['message_id']}",
        '',
        '## Worker',
        f"- role: `{payload['worker_role']}`",
        f"- family: `{payload['worker_family']}`",
        f"- result type: `{payload['result_type']}`",
        '',
        '## GitHub context',
        f"- issue: `#{payload['issue']['number']}`",
        f"- PR: `#{payload['pr']['number']}`",
        f"- branch: `{payload['branch']['name']}`",
        '',
        '## Implementation summary',
        json.dumps(payload['implementation_summary'], indent=2),
        '',
        '## Validation summary',
        json.dumps(payload['validation_summary'], indent=2),
        '',
        '## TechLead action recommended',
        json.dumps(payload['techlead_action_recommended'], indent=2),
    ]
    path.write_text('\n'.join(review) + '\n')


def write_delivery_review_packet_markdown(path: Path, packet: dict[str, Any]) -> None:
    payload = packet['payload']
    review = [
        f"# Delivery Review Packet Review: {packet['message_id']}",
        '',
        '## Review',
        f"- review type: `{payload['review_type']}`",
        f"- result type: `{payload['result_type']}`",
        '',
        '## GitHub context',
        f"- issue: `#{payload['issue']['number']}`",
        f"- PR: `#{payload['pr']['number']}`",
        f"- branch: `{payload['branch']['name']}`",
        '',
        '## Scope recommendation',
        json.dumps(payload['scope_recommendation'], indent=2),
        '',
        '## Authority impact',
        json.dumps(payload['authority_impact'], indent=2),
        '',
        '## Branch recommendation',
        json.dumps(payload['branch_recommendation'], indent=2),
        '',
        '## TechLead action recommended',
        json.dumps(payload['techlead_action_recommended'], indent=2),
        '',
        '## Findings',
        json.dumps(payload['findings'], indent=2),
    ]
    path.write_text('\n'.join(review) + '\n')


def write_techlead_assignment_review_markdown(path: Path, packet: dict[str, Any]) -> None:
    payload = packet['payload']
    review = [
        f"# TechLead Assignment Packet Review: {packet['message_id']}",
        '',
        '## Assignment',
        f"- target role: `{payload['target_role']}`",
        f"- assignment type: `{payload['assignment_type']}`",
        f"- canonical branch: `{payload['canonical_branch']}`",
        f"- role branch: `{payload['role_branch'] or '(none)'}`",
        '',
        '## GitHub context',
        f"- issue: `#{payload['issue']['number']}`",
        f"- PR: `#{payload['pr']['number']}`",
        '',
        '## Allowed result types',
    ]
    review.extend([f"- {item}" for item in payload['allowed_result_types']])
    review.extend([
        '',
        '## Assignment summary',
        str(payload['assignment_summary']),
        '',
        '## Source context',
        json.dumps(payload['source_context_ref'], indent=2),
    ])
    path.write_text('\n'.join(review) + '\n')


def write_techlead_decision_review_markdown(path: Path, packet: dict[str, Any]) -> None:
    payload = packet['payload']
    review = [
        f"# TechLead Decision Packet Review: {packet['message_id']}",
        '',
        '## Decision',
        f"- decision type: `{payload['decision_type']}`",
        f"- target role: `{payload['target_role'] or '(none)'}`",
        f"- next assignment type: `{payload['next_assignment_type'] or '(none)'}`",
        f"- canonical branch: `{payload['canonical_branch']}`",
        f"- role branch: `{payload['role_branch'] or '(none)'}`",
        '',
        '## GitHub context',
        f"- issue: `#{payload['issue']['number']}`",
        f"- PR: `#{payload['pr']['number']}`",
        '',
        '## Decision rationale',
        str(payload['decision_rationale']),
        '',
        '## Source packet reference',
        json.dumps(payload['source_packet_ref'], indent=2),
        '',
        '## Work-item status update intent',
        str(payload['work_item_status_update_intent']),
    ]
    path.write_text('\n'.join(review) + '\n')
