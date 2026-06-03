"""Placeholder home for future producer-side artifact derivation commands."""

from __future__ import annotations

import json
from pathlib import Path


def derive_inventory(repo_root: Path) -> dict[str, object]:
    return {
        'ok': True,
        'repo_root': str(repo_root),
        'message': 'Artifact derivation commands are now platform-owned; project-specific derivation logic belongs here next.',
    }
