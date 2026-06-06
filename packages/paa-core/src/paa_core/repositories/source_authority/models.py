"""DTOs for source-authority persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    slug: str
    name: str
    repo_url: str | None
    execution_surface: str
    status: str
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class ProjectUpsertSpec:
    slug: str
    name: str
    repo_url: str | None = None
    execution_surface: str = 'github'
    status: str = 'active'


@dataclass(frozen=True)
class AuthorityVersionRecord:
    authority_version_id: str
    project_id: str
    version_label: str
    source_commit: str | None
    published_from_ref: str | None
    manifest_path: str | None
    published_at: str | None
    status: str
    notes: str | None
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class AuthorityVersionUpsertSpec:
    project_slug: str
    version_label: str
    source_commit: str | None = None
    published_from_ref: str | None = None
    manifest_path: str | None = None
    published_at: str | None = None
    status: str = 'published'
    notes: str | None = None


@dataclass(frozen=True)
class SpecFragmentRecord:
    spec_fragment_id: str
    project_id: str
    title: str
    canonical_statement: str
    fragment_kind: str
    delta_family: str | None
    authorized_delta_family: str | None
    out_of_scope_delta_families: tuple[str, ...]
    expected_touch_surfaces: tuple[str, ...]
    status: str
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class SpecFragmentUpsertSpec:
    project_slug: str
    title: str
    canonical_statement: str
    fragment_kind: str
    delta_family: str | None = None
    authorized_delta_family: str | None = None
    external_fragment_id: str | None = None
    out_of_scope_delta_families: tuple[str, ...] = ()
    expected_touch_surfaces: tuple[str, ...] = ()
    status: str = 'approved'
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ImplementationTargetRecord:
    implementation_target_id: str
    spec_fragment_id: str
    title: str
    current_gap: tuple[str, ...]
    desired_state: tuple[str, ...]
    protected_baseline: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    pre_handoff_scope_checks: tuple[str, ...]
    risk_level: str
    status: str
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class ImplementationTargetUpsertSpec:
    spec_fragment_id: str
    title: str
    external_target_id: str | None = None
    current_gap: tuple[str, ...] = ()
    desired_state: tuple[str, ...] = ()
    protected_baseline: tuple[str, ...] = ()
    out_of_scope: tuple[str, ...] = ()
    pre_handoff_scope_checks: tuple[str, ...] = ()
    risk_level: str = 'medium'
    status: str = 'approved'
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkItemRecord:
    work_item_id: str
    project_id: str
    authority_version_id: str | None
    title: str
    status: str
    merge_policy: str | None
    requires_qa: bool
    issue_number: int | None
    implementation_target_ref: str | None
    spec_fragment_ref: str | None
    domain_ref: dict[str, Any]
    spec_fragment_id: str | None
    implementation_target_id: str | None
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class WorkItemUpsertSpec:
    project_slug: str
    authority_version_id: str
    title: str
    spec_fragment_ref: str | None
    implementation_target_ref: str | None = None
    issue_number: int | None = None
    domain_ref: dict[str, Any] | None = None
    spec_fragment_id: str | None = None
    implementation_target_id: str | None = None
    status: str = 'authorized'
    merge_policy: str | None = 'architect_review_required'
    requires_qa: bool = False


__all__ = [
    'AuthorityVersionRecord',
    'AuthorityVersionUpsertSpec',
    'ImplementationTargetRecord',
    'ImplementationTargetUpsertSpec',
    'ProjectRecord',
    'ProjectUpsertSpec',
    'SpecFragmentRecord',
    'SpecFragmentUpsertSpec',
    'WorkItemRecord',
    'WorkItemUpsertSpec',
]
