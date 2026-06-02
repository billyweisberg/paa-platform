"""Compatibility wrappers over unified runtime queue services."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from paa_core import handoff_runtime
from paa_core.runtime_packet_dispatch import (
    dispatch_packet,
    dispatch_techlead_packet,
    resolve_packet_queue,
    resolve_techlead_packet_queue,
)
from paa_core.runtime_paths import repo_queue_state_root


def run_queue_command(repo_root: Path, argv: list[str]) -> int:
    os.environ.setdefault('FRACTAL_CORE_HANDOFF_STATE_DIR', str(repo_queue_state_root(repo_root)))
    return handoff_runtime.main(['--repo-root', str(repo_root), *argv])


__all__ = [
    'dispatch_packet',
    'dispatch_techlead_packet',
    'resolve_packet_queue',
    'resolve_techlead_packet_queue',
    'run_queue_command',
]
