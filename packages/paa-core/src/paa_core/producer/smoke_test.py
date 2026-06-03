"""Producer runtime smoke test helpers."""

from __future__ import annotations

import json
from pathlib import Path

from paa_core.config import load_producer_project_config
from paa_producer.authority_runtime import load_manifest, resolve_producer_project_config_path


def run_smoke_test(repo_root: Path, *, output_path: Path | None = None) -> dict[str, object]:
    repo_root = repo_root.resolve()
    config_path = resolve_producer_project_config_path(repo_root)
    config = load_producer_project_config(config_path)
    manifest_path, manifest = load_manifest(str((repo_root / config.authority_manifest_path).resolve()))
    active_tasks = [
        task['task_id']
        for task in manifest.get('tasks', [])
        if task.get('status') in {'planned', 'in_dev', 'in_qa', 'in_review'}
    ]
    result = {
        'ok': True,
        'repo_root': str(repo_root),
        'project_config_path': str(config_path),
        'authority_manifest_path': str(manifest_path),
        'authority_version': manifest.get('project', {}).get('authority_version'),
        'project_id': config.project_id,
        'publication_output_root': str(config.publication_output_root),
        'active_tasks': active_tasks,
        'supporting_docs': list(config.supporting_docs),
        'artifact_paths': list(config.artifact_paths),
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2) + '\n')
    return result
