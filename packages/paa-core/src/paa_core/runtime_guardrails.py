"""Repo-local runtime guardrails for producer and consumer installs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from paa_core.runtime_paths import repo_authority_manifest_path, repo_root_from_cwd


def git_branch(repo_root: Path) -> str:
    return subprocess.run(['git', '-C', str(repo_root), 'branch', '--show-current'], capture_output=True, text=True, check=True).stdout.strip()


def git_head(repo_root: Path, ref: str = 'HEAD') -> str:
    return subprocess.run(['git', '-C', str(repo_root), 'rev-parse', ref], capture_output=True, text=True, check=True).stdout.strip()


def branch_ahead_behind(repo_root: Path, upstream: str = 'origin/main') -> tuple[int, int]:
    result = subprocess.run(['git', '-C', str(repo_root), 'rev-list', '--left-right', '--count', f'{upstream}...HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    left, right = result.split() if result else ('0', '0')
    return int(left), int(right)


def authority_version(repo_root: Path) -> str | None:
    manifest = repo_authority_manifest_path(repo_root)
    if not manifest.exists():
        return None
    data = json.loads(manifest.read_text())
    return data.get('project', {}).get('authority_version')


def validate_consumer_runtime(repo_root: Path, *, expected_branch: str | None = None) -> dict[str, object]:
    repo_root = repo_root.resolve()
    current_branch = git_branch(repo_root)
    behind, ahead = branch_ahead_behind(repo_root)
    version = authority_version(repo_root)
    errors: list[str] = []
    if expected_branch and current_branch != expected_branch:
        errors.append(f'branch mismatch: expected {expected_branch}, found {current_branch}')
    if behind > 0:
        errors.append(f'workspace behind origin/main by {behind} commit(s)')
    if not version:
        errors.append('installed authority package missing or unreadable')
    return {
        'ok': not errors,
        'repo_root': str(repo_root),
        'branch': current_branch,
        'ahead': ahead,
        'behind': behind,
        'authority_version': version,
        'errors': errors,
    }


def validate_current_consumer_runtime() -> dict[str, object]:
    return validate_consumer_runtime(repo_root_from_cwd())
