"""Consumer runtime smoke test helpers."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from paa_core.runtime_guardrails import validate_runtime_install


def run_smoke_test(
    repo_root: Path,
    *,
    expected_branch: str | None = None,
    validate_schema_flag: bool = False,
    output_path: Path | None = None,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    runtime = validate_runtime_install(repo_root, expected_branch=expected_branch)
    if not runtime.get('ok'):
        errors.extend(str(item) for item in runtime.get('errors', []))

    report = None
    try:
        cmd = [str(repo_root / '.codex' / 'paa' / 'bin' / 'paa-consumer'), 'techlead-status']
        if validate_schema_flag:
            cmd.append('--validate-schema')
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'repo-local techlead-status failed')
        report = json.loads(result.stdout)
    except Exception as exc:  # pragma: no cover - smoke path
        errors.append(f'techlead/report failed: {exc}')

    result = {
        'ok': not errors,
        'repo_root': str(repo_root),
        'expected_branch': expected_branch,
        'runtime': runtime,
        'warnings': warnings,
        'errors': errors,
        'queues': report.get('queues') if report else None,
        'latest_accepted_chain': ((report or {}).get('traceability') or {}).get('latest_accepted_chain'),
        'active_work_chain': ((report or {}).get('traceability') or {}).get('active_work_chain'),
        'unattended_safe': report.get('unattended_safe') if report else None,
        'authority_status': ((report or {}).get('authority') or {}).get('status'),
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2) + '\n')
    return result
