"""PAA operator CLI package for the unified Typer host surface."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import PAAOperatorCLI, StructuredLogger
from .environment import EnvironmentResolutionInput, EnvironmentResolver
from .command_adapters import ComponentCommandAdapter, PlanCommandAdapter
from .normalization import CommandResultNormalizer
from .rendering import OutputRenderer
from .router import CommandRegistration, CommandRouter, OperatorCommandAdapter
from .models import (
    OperatorCommand,
    OperatorCommandRequest,
    OperatorCommandResult,
    OperatorFailure,
    OperatorInvocationContext,
    OperatorOutputMessage,
    OperatorOutputSection,
    OperatorOutputTable,
)

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
    'CommandRegistration',
    'ComponentCommandAdapter',
    'CommandResultNormalizer',
    'CommandRouter',
    'EnvironmentResolutionInput',
    'EnvironmentResolver',
    'OperatorCommand',
    'OperatorCommandAdapter',
    'OperatorCommandRequest',
    'OperatorCommandResult',
    'OperatorFailure',
    'OperatorInvocationContext',
    'OperatorOutputMessage',
    'OperatorOutputSection',
    'OperatorOutputTable',
    'OutputRenderer',
    'PlanCommandAdapter',
    'PAAOperatorCLI',
    'PAA_OPERATOR_CLI_METADATA',
    'StructuredLogger',
]
