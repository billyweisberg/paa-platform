"""Source-authority repository package."""

from .contracts import SourceAuthorityRepository
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
from .postgres import PostgresSourceAuthorityRepository

__all__ = [
    'AuthorityVersionRecord',
    'AuthorityVersionUpsertSpec',
    'ImplementationTargetRecord',
    'ImplementationTargetUpsertSpec',
    'PostgresSourceAuthorityRepository',
    'ProjectRecord',
    'ProjectUpsertSpec',
    'SourceAuthorityRepository',
    'SpecFragmentRecord',
    'SpecFragmentUpsertSpec',
    'WorkItemRecord',
    'WorkItemUpsertSpec',
]
