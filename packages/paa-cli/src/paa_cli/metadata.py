"""Governed metadata for the PAA CLI host surface."""

from paa_core.governance import GovernedComponentMetadata

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

__all__ = ['PAA_OPERATOR_CLI_METADATA']
