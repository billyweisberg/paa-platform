"""Consumer-facing queue wrappers over the shared handoff runtime."""

from __future__ import annotations

import os
from pathlib import Path

from paa_core import handoff_runtime
from paa_core.runtime_paths import repo_queue_state_root


def run_queue_command(repo_root: Path, argv: list[str]) -> int:
    os.environ.setdefault('FRACTAL_CORE_HANDOFF_STATE_DIR', str(repo_queue_state_root(repo_root)))
    return handoff_runtime.main(argv)
