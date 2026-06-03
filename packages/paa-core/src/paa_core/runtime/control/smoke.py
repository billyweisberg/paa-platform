"""Unified runtime smoke test helpers for the `paa` CLI."""

from __future__ import annotations

import json
from pathlib import Path

from paa_core.runtime.control.supervisor import runtime_supervisor_status
from paa_core.runtime.support.runtime_guardrails import validate_runtime_install
from paa_core.runtime.support.runtime_paths import resolved_repo_runtime_queue_topology
from paa_core.runtime.transport.queue_admin import DefaultRuntimeQueueAdminService


def run_runtime_smoke_test(
    repo_root: Path,
    *,
    expected_branch: str | None = None,
    output_path: Path | None = None,
    queue_admin_service: DefaultRuntimeQueueAdminService | None = None,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    queue_admin = queue_admin_service or DefaultRuntimeQueueAdminService()

    runtime = validate_runtime_install(repo_root, expected_branch=expected_branch)
    runtime_ok = bool(runtime.get('ok'))
    runtime_errors = runtime.get('errors')
    if not runtime_ok:
        if isinstance(runtime_errors, list):
            errors.extend(str(item) for item in runtime_errors)
        elif isinstance(runtime_errors, tuple):
            errors.extend(str(item) for item in runtime_errors)
        elif runtime_errors is not None:
            errors.append(str(runtime_errors))

    supervisor = runtime_supervisor_status(repo_root)
    queue_reports: dict[str, object] = {}
    queue_depths: dict[str, int | None] = {}
    try:
        for queue_name in resolved_repo_runtime_queue_topology(repo_root).queue_names.values():
            report = queue_admin.check(repo_root=repo_root, queue=queue_name, preview=0)
            queue_reports[queue_name] = report
            if isinstance(report, dict):
                messages_ready = report.get('messages_ready')
                queue_depths[queue_name] = messages_ready if isinstance(messages_ready, int) else None
            else:
                queue_depths[queue_name] = None
    except Exception as exc:  # pragma: no cover - defensive smoke path
        errors.append(f'queue/report failed: {exc}')

    result = {
        'ok': not errors,
        'repo_root': str(repo_root),
        'expected_branch': expected_branch,
        'runtime': runtime,
        'runtime_supervisor': supervisor,
        'warnings': warnings,
        'errors': errors,
        'queues': queue_reports,
        'queue_depths': queue_depths,
        'unattended_safe': runtime_ok and bool(supervisor.get('running')) and not errors,
        'authority_status': 'installed' if runtime.get('authority_version') else 'missing',
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2) + '\n')
    return result


__all__ = ['run_runtime_smoke_test']
