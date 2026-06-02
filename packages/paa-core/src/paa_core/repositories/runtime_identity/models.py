"""DTOs for runtime identity persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RoleRecord:
    role_id: str
    project_id: str
    name: str
    category: str
    description: str | None
    is_human_capable: bool
    is_automation_capable: bool
    sort_order: int
    active: bool
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class RoleUpsertSpec:
    project_slug: str
    name: str
    category: str
    description: str | None = None
    is_human_capable: bool = True
    is_automation_capable: bool = True
    sort_order: int = 100
    active: bool = True


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    project_id: str
    role_id: str | None
    name: str
    agent_type: str
    runtime_kind: str | None
    active: bool
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class AgentUpsertSpec:
    project_slug: str
    name: str
    role_name: str | None = None
    agent_type: str = 'automation'
    runtime_kind: str | None = 'codex'
    active: bool = True
    metadata: dict[str, Any] | None = None


__all__ = [
    'AgentRecord',
    'AgentUpsertSpec',
    'RoleRecord',
    'RoleUpsertSpec',
]
