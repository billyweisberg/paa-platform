"""Contracts for source-authority persistence."""

from __future__ import annotations

from typing import Protocol

from .models import (
    AuthorityVersionRecord,
    AuthorityVersionUpsertSpec,
    ImplementationTargetRecord,
    ImplementationTargetUpsertSpec,
    ProjectRecord,
    ProjectUpsertSpec,
    SpecFragmentRecord,
    SpecFragmentUpsertSpec,
    WorkItemRecord,
    WorkItemUpsertSpec,
)


class SourceAuthorityRepository(Protocol):
    """Persistence boundary for source-authority anchor records."""

    def get_project_by_slug(self, project_slug: str) -> ProjectRecord | None:
        ...

    def upsert_project(self, spec: ProjectUpsertSpec) -> ProjectRecord:
        ...

    def upsert_authority_version(self, spec: AuthorityVersionUpsertSpec) -> AuthorityVersionRecord:
        ...

    def upsert_spec_fragment(self, spec: SpecFragmentUpsertSpec) -> SpecFragmentRecord:
        ...

    def upsert_implementation_target(
        self, spec: ImplementationTargetUpsertSpec
    ) -> ImplementationTargetRecord:
        ...

    def upsert_work_item(self, spec: WorkItemUpsertSpec) -> WorkItemRecord:
        ...

    def find_work_item_by_project_and_authority_anchor(
        self,
        project_slug: str,
        *,
        issue_number: int | None = None,
        spec_fragment_ref: str | None = None,
    ) -> WorkItemRecord | None:
        ...


__all__ = ['SourceAuthorityRepository']
