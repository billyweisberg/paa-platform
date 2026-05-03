"""Repo-local runtime path resolution for PAA."""

from __future__ import annotations

import json
from pathlib import Path

from paa_core.paths import CODEX_INSTALL_ROOT, PROJECT_DATA_ROOT, ensure_directory, resolve_from_repo_root


def repo_root_from_cwd(cwd: Path | None = None) -> Path:
    start = (cwd or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / '.git').exists():
            return candidate
    return start


def repo_paa_root(repo_root: Path) -> Path:
    return repo_root / CODEX_INSTALL_ROOT


def repo_runtime_root(repo_root: Path) -> Path:
    return repo_root / PROJECT_DATA_ROOT


def repo_authority_install_root(repo_root: Path) -> Path:
    return repo_runtime_root(repo_root) / 'authority' / 'current'


def repo_authority_manifest_path(repo_root: Path) -> Path:
    authority_root = repo_authority_install_root(repo_root)
    authority_dir = authority_root / 'authority'
    matches = sorted(authority_dir.glob('*-authority.json'))
    if matches:
        return matches[0]
    return authority_dir / 'fractal-core-python-authority.json'


def repo_installed_artifact_path(repo_root: Path, name: str) -> Path:
    return repo_authority_install_root(repo_root) / 'artifacts' / name


def repo_consumer_bin(repo_root: Path) -> Path:
    return repo_paa_root(repo_root) / 'bin' / 'paa-consumer'


def repo_producer_bin(repo_root: Path) -> Path:
    return repo_paa_root(repo_root) / 'bin' / 'paa-producer'


def repo_automations_root(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'automations'


def repo_skills_root(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'skills'


def repo_queue_state_root(repo_root: Path) -> Path:
    return ensure_directory(repo_runtime_root(repo_root) / 'queue-state' / 'fractal-core-handoff')


def default_installed_manifest_path() -> Path:
    return repo_authority_manifest_path(repo_root_from_cwd())


def default_installed_artifact_path(name: str) -> Path:
    return repo_installed_artifact_path(repo_root_from_cwd(), name)


def producer_manifest_candidates(cwd: Path) -> list[Path]:
    repo_root = repo_root_from_cwd(cwd)
    config_path = repo_paa_root(repo_root) / 'project-config.json'
    candidates: list[Path] = []
    if config_path.exists():
        data = json.loads(config_path.read_text())
        manifest_path = data.get('authority_manifest_path')
        if manifest_path:
            candidates.append(resolve_from_repo_root(repo_root, manifest_path))
    candidates.append((repo_root / 'docs/architecture/tom-baby7-fractal-core/project-authority/fractal-core-python-authority.json').resolve())
    return [p for p in candidates if p.exists()]
