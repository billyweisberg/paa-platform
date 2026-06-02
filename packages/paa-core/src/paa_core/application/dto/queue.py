from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class QueueOperationResult:
    payload: dict[str, Any]
    exit_code: int = 0


@dataclass(frozen=True)
class QueueRepoRootRequest:
    repo_root: Path


@dataclass(frozen=True)
class QueueCheckRequest:
    repo_root: Path
    queue: str
    preview: int = 0


@dataclass(frozen=True)
class QueuePurgeRequest:
    repo_root: Path
    queue: str | None = None


@dataclass(frozen=True)
class QueueValidateRequest:
    message_file: Path


@dataclass(frozen=True)
class QueueSendRequest:
    repo_root: Path
    queue: str
    message_file: Path


@dataclass(frozen=True)
class QueueClaimNextRequest:
    repo_root: Path
    queue: str
    claimed_by: str = 'paa'


@dataclass(frozen=True)
class QueueListClaimsRequest:
    repo_root: Path
    queue: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class QueueClaimActionRequest:
    repo_root: Path
    claim_id: str


@dataclass(frozen=True)
class QueuePacketFileRequest:
    repo_root: Path
    message_file: Path
