"""Contracts for runtime identity persistence."""

from __future__ import annotations

from typing import Protocol

from .models import AgentRecord, AgentUpsertSpec, RoleRecord, RoleUpsertSpec


class RuntimeIdentityRepository(Protocol):
    """Persistence boundary for project-scoped runtime roles and agents."""

    def get_role_by_name(self, project_slug: str, role_name: str) -> RoleRecord | None:
        ...

    def upsert_role(self, spec: RoleUpsertSpec) -> RoleRecord:
        ...

    def get_agent_by_name(self, project_slug: str, agent_name: str) -> AgentRecord | None:
        ...

    def upsert_agent(self, spec: AgentUpsertSpec) -> AgentRecord:
        ...


__all__ = ['RuntimeIdentityRepository']
