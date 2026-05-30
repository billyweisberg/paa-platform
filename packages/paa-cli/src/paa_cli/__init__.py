"""PAA operator CLI package for the unified Typer host surface."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import PAAOperatorCLI, StructuredLogger

PAA_OPERATOR_CLI_METADATA = GovernedComponentMetadata(
    name='PAAOperatorCLI',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'lane-aware operator command host contract',
        'normalized operator command invocation boundary',
        'stable command-family support contract',
    ),
    does_not_own=(
        'implementation-plan persistence',
        'workflow lifecycle truth',
        'queue transport primitives',
        'runtime worker execution policy',
    ),
)

__all__ = [
    'PAAOperatorCLI',
    'PAA_OPERATOR_CLI_METADATA',
    'StructuredLogger',
]
