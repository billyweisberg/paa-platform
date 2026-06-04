"""Shared PAA path conventions."""

from __future__ import annotations

from pathlib import Path

CODEX_INSTALL_ROOT = Path(".codex") / "paa"
PROJECT_DATA_ROOT = Path(".project") / "data" / "paa"


def ensure_directory(path: Path) -> Path:
    """Create a directory tree if needed and return the path."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_from_repo_root(repo_root: Path, relative_path: str) -> Path:
    """Resolve a repo-relative path from a known repo root."""

    return (repo_root / relative_path).resolve()


def authority_package_staging_root(base: Path) -> Path:
    """Return the canonical staging root used during publication."""

    return base / "authority-package"

