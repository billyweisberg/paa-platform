"""PAA operator CLI package for the unified Typer host surface."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .metadata import PAA_OPERATOR_CLI_METADATA

__all__ = [
    'PAA_OPERATOR_CLI_METADATA',
    'PAAOperatorCLI',
    'StructuredLogger',
    'EnvironmentResolutionInput',
    'EnvironmentResolver',
    'DefaultPAAOperatorCLI',
    'NullStructuredLogger',
    'build_app',
    'build_default_cli',
    'main',
    'ComponentCommandAdapter',
    'PlanCommandAdapter',
    'CommandResultNormalizer',
    'OutputRenderer',
    'CommandRegistration',
    'CommandRouter',
    'OperatorCommandAdapter',
    'OperatorCommand',
    'OperatorCommandRequest',
    'OperatorCommandResult',
    'OperatorFailure',
    'OperatorInvocationContext',
    'OperatorOutputMessage',
    'OperatorOutputSection',
    'OperatorOutputTable',
]

_MODULE_BY_NAME = {
    'PAAOperatorCLI': 'paa_cli.contracts',
    'StructuredLogger': 'paa_cli.contracts',
    'EnvironmentResolutionInput': 'paa_cli.environment',
    'EnvironmentResolver': 'paa_cli.environment',
    'DefaultPAAOperatorCLI': 'paa_cli.app',
    'NullStructuredLogger': 'paa_cli.app',
    'build_app': 'paa_cli.app',
    'build_default_cli': 'paa_cli.app',
    'main': 'paa_cli.app',
    'ComponentCommandAdapter': 'paa_cli.command_adapters',
    'PlanCommandAdapter': 'paa_cli.command_adapters',
    'CommandResultNormalizer': 'paa_cli.normalization',
    'OutputRenderer': 'paa_cli.rendering',
    'CommandRegistration': 'paa_cli.router',
    'CommandRouter': 'paa_cli.router',
    'OperatorCommandAdapter': 'paa_cli.router',
    'OperatorCommand': 'paa_cli.models',
    'OperatorCommandRequest': 'paa_cli.models',
    'OperatorCommandResult': 'paa_cli.models',
    'OperatorFailure': 'paa_cli.models',
    'OperatorInvocationContext': 'paa_cli.models',
    'OperatorOutputMessage': 'paa_cli.models',
    'OperatorOutputSection': 'paa_cli.models',
    'OperatorOutputTable': 'paa_cli.models',
}


def __getattr__(name: str) -> Any:
    if name == 'PAA_OPERATOR_CLI_METADATA':
        return PAA_OPERATOR_CLI_METADATA
    module_name = _MODULE_BY_NAME.get(name)
    if module_name is None:
        raise AttributeError(name)
    module = import_module(module_name)
    return getattr(module, name)
