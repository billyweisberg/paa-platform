"""Authority-task and brief resolution helpers for producer flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from paa_core.producer.authority_packet_support import load_ready_coder_briefs_from_paa


def find_task(
    data: dict[str, Any],
    issue_number: int | None = None,
    task_id: str | None = None,
) -> dict[str, Any] | None:
    for task in data.get('tasks', []):
        if not isinstance(task, dict):
            continue
        if issue_number is not None and task.get('issue_number') == issue_number:
            return task
        if task_id is not None and task.get('task_id') == task_id:
            return task
    return None


def build_authority_context(
    manifest: Path,
    manifest_data: dict[str, Any],
    package: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    package_authority_context = package['authority_context']
    task = find_task(manifest_data, task_id=package_authority_context['task_id'])
    authority_context = {
        'manifest_path': str(manifest),
        'authority_version': package_authority_context.get('authority_version') or manifest_data['project']['authority_version'],
        'milestone_id': package_authority_context['milestone_id'],
        'phase_id': package_authority_context['phase_id'],
        'task_id': package_authority_context['task_id'],
    }
    if task:
        authority_context.update(
            {
                'authority_version': manifest_data['project']['authority_version'],
                'issue_number': task.get('issue_number'),
                'task_title': task.get('title'),
            }
        )
    return authority_context, task


def resolve_brief_for_packet(
    *,
    project_slug: str,
    package_id_external: str,
    brief_id_external: str,
    require_ready: bool = True,
) -> dict[str, Any]:
    briefs = load_ready_coder_briefs_from_paa(
        project_slug=project_slug,
        package_id_external=package_id_external,
    )
    if not briefs:
        raise RuntimeError(f'No coder briefs found for design package {package_id_external}')
    selected = next((brief for brief in briefs if brief['brief_id_external'] == brief_id_external), None)
    if selected is None:
        raise RuntimeError(f'Brief {brief_id_external} not found in design package {package_id_external}')
    readiness_state = selected['readiness_state']
    if require_ready and readiness_state not in {'execution_ready', 'parallel_ready'}:
        raise RuntimeError(
            f'Brief {brief_id_external} is not execution-eligible (readiness={readiness_state})'
        )
    return selected
