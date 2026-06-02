"""Runtime identity repository package."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import RuntimeIdentityRepository
from .models import AgentRecord, AgentUpsertSpec, RoleRecord, RoleUpsertSpec
from .postgres import PostgresRuntimeIdentityRepository

RUNTIME_IDENTITY_REPOSITORY_METADATA = GovernedComponentMetadata(
    name='RuntimeIdentityRepository',
    kind='repository',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'project-scoped runtime role persistence',
        'project-scoped runtime agent persistence',
    ),
    does_not_own=(
        'queue routing policy',
        'worker-host orchestration',
        'methodology execution truth',
    ),
)

__all__ = [
    'AgentRecord',
    'AgentUpsertSpec',
    'PostgresRuntimeIdentityRepository',
    'RoleRecord',
    'RoleUpsertSpec',
    'RuntimeIdentityRepository',
    'RUNTIME_IDENTITY_REPOSITORY_METADATA',
]
