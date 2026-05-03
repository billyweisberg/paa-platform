"""Consumer-side delivery runtime orchestration helpers."""

from __future__ import annotations

import json
from pathlib import Path

from paa_consumer.inbox import run_queue_command


def send_packet(repo_root: Path, queue_name: str, packet_path: Path) -> dict[str, object]:
    code = run_queue_command(repo_root, ['send', '--queue', queue_name, '--file', str(packet_path)])
    return {'ok': code == 0, 'queue': queue_name, 'packet_path': str(packet_path)}
