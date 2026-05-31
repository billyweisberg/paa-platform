"""Thin Typer application root for the unified PAA operator CLI."""

from __future__ import annotations

from typing import Final

try:
    import typer
except ImportError as exc:  # pragma: no cover - exercised only in missing-dependency environments
    typer = None
    _TYPER_IMPORT_ERROR = exc
else:  # pragma: no branch
    _TYPER_IMPORT_ERROR = None

from .command_adapters import ComponentCommandAdapter, PlanCommandAdapter
from .contracts import PAAOperatorCLI, StructuredLogger
from .environment import EnvironmentResolutionInput, EnvironmentResolver
from .models import (
    OperatorCommand,
    OperatorCommandRequest,
    OperatorCommandResult,
    OperatorFailure,
)
from .normalization import CommandResultNormalizer
from .rendering import OutputRenderer
from .router import CommandRegistration, CommandRouter

_OUTPUT_MODES: Final[tuple[str, ...]] = ('table', 'json', 'summary')


class NullStructuredLogger:
    """Default logger used until the richer methodology pointer surfaces arrive."""

    def info(self, event: str, **fields: object) -> None:
        del event, fields

    def warning(self, event: str, **fields: object) -> None:
        del event, fields


class DefaultPAAOperatorCLI(PAAOperatorCLI):
    """Concrete thin host over the realized component and plan command families."""

    def __init__(
        self,
        *,
        logger: StructuredLogger,
        environment_resolver: EnvironmentResolver,
        router: CommandRouter,
        normalizer: CommandResultNormalizer,
        renderer: OutputRenderer,
    ) -> None:
        self._logger = logger
        self.environment_resolver = environment_resolver
        self.router = router
        self.normalizer = normalizer
        self.renderer = renderer

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def run_command(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        self.logger.info(
            'paa_cli.command.start',
            command_family=request.command.command_family,
            command_name=request.command.command_name,
        )
        try:
            raw_result = self.router.route(request)
        except KeyError:
            raw_result = OperatorCommandResult(
                command=request.command,
                supported=False,
                success=False,
                exit_code=2,
                failure=OperatorFailure(
                    code='unsupported_command_family',
                    summary='Unsupported command family for the current CLI shell.',
                    details=(request.command.command_family,),
                ),
            )
        result = self.normalizer.normalize(request.command, raw_result)
        if result.failure is not None:
            self.logger.warning(
                'paa_cli.command.failed',
                command_family=request.command.command_family,
                command_name=request.command.command_name,
                failure_code=result.failure.code,
            )
        else:
            self.logger.info(
                'paa_cli.command.completed',
                command_family=request.command.command_family,
                command_name=request.command.command_name,
                exit_code=result.exit_code,
            )
        return result

    def supports_command_family(self, command_family: str) -> bool:
        return self.router.supports_command_family(command_family)

    def render_result(self, result: OperatorCommandResult, *, output_mode: str) -> str:
        return self.renderer.render(result, output_mode=output_mode)


def build_default_cli() -> DefaultPAAOperatorCLI:
    return DefaultPAAOperatorCLI(
        logger=NullStructuredLogger(),
        environment_resolver=EnvironmentResolver(),
        router=CommandRouter(
            (
                CommandRegistration(command_family='component', adapter=ComponentCommandAdapter()),
                CommandRegistration(command_family='plan', adapter=PlanCommandAdapter()),
            )
        ),
        normalizer=CommandResultNormalizer(),
        renderer=OutputRenderer(),
    )


def _invoke(
    cli: DefaultPAAOperatorCLI,
    *,
    command_family: str,
    command_name: str,
    repo_root: str | None,
    output_mode: str,
    dry_run: bool,
    strict_mode: bool,
    arguments: dict[str, object],
) -> int:
    context = cli.environment_resolver.resolve(
        EnvironmentResolutionInput(
            repo_root=repo_root,
            output_mode=output_mode,
            dry_run=dry_run,
            strict_mode=strict_mode,
        )
    )
    request = OperatorCommandRequest(
        command=OperatorCommand(command_family=command_family, command_name=command_name),
        invocation_context=context,
        arguments=arguments,
    )
    result = cli.run_command(request)
    typer.echo(cli.render_result(result, output_mode=output_mode))
    return result.exit_code


def build_app(cli: DefaultPAAOperatorCLI | None = None):
    if typer is None:  # pragma: no cover - depends on host environment
        raise RuntimeError(
            'Typer is required to build the PAA operator CLI app. '
            'Install the `paa-cli` package dependencies first.'
        ) from _TYPER_IMPORT_ERROR

    cli = cli or build_default_cli()
    app = typer.Typer(
        help='Unified operator CLI for the PAA methodology.',
        no_args_is_help=True,
        add_completion=False,
        pretty_exceptions_enable=False,
    )
    component_app = typer.Typer(help='Component-realization lane commands.', no_args_is_help=True)
    plan_app = typer.Typer(help='Implementation-plan inspection commands.', no_args_is_help=True)

    @component_app.command('materialize')
    def component_materialize(
        spec: str = typer.Option(..., '--spec', help='Absolute or relative component spec path.'),
        project_slug: str | None = typer.Option(None, '--project-slug', help='Optional project slug override.'),
        repo_root: str | None = typer.Option(None, '--repo-root', help='Invocation repo root override.'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run', help='Resolve invocation context without mutating runtime state.'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict', help='Enable strict fail-closed handling.'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='materialize',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'spec': spec, **({'project_slug': project_slug} if project_slug else {})},
        )
        raise typer.Exit(code=code)

    @component_app.command('progress')
    def component_progress(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='progress',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'plan_id': plan_id},
        )
        raise typer.Exit(code=code)

    @component_app.command('reconcile')
    def component_reconcile(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='reconcile',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'plan_id': plan_id},
        )
        raise typer.Exit(code=code)

    @component_app.command('next')
    def component_next(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='next',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'plan_id': plan_id},
        )
        raise typer.Exit(code=code)

    @component_app.command('complete')
    def component_complete(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        activity_key: str = typer.Option(..., '--activity-key', help='Implementation plan activity key.'),
        completed_at: str | None = typer.Option(None, '--completed-at', help='Optional completion timestamp override.'),
        metadata_json: str | None = typer.Option(None, '--metadata-json', help='Optional JSON object merged into activity metadata.'),
        no_reconcile: bool = typer.Option(False, '--no-reconcile', help='Skip automatic reconcile after completion.'),
        no_next: bool = typer.Option(False, '--no-next', help='Skip automatic next-activity derivation after reconcile.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='complete',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'plan_id': plan_id,
                'activity_key': activity_key,
                **({'completed_at': completed_at} if completed_at else {}),
                **({'metadata_json': metadata_json} if metadata_json else {}),
                'no_reconcile': no_reconcile,
                'no_next': no_next,
            },
        )
        raise typer.Exit(code=code)

    @plan_app.command('progress')
    def plan_progress(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='plan',
            command_name='progress',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'plan_id': plan_id},
        )
        raise typer.Exit(code=code)

    @plan_app.command('inspect')
    def plan_inspect(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='plan',
            command_name='inspect',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'plan_id': plan_id},
        )
        raise typer.Exit(code=code)

    app.add_typer(component_app, name='component')
    app.add_typer(plan_app, name='plan')
    return app


def main() -> int:
    app = build_app()
    app(prog_name='paa')
    return 0


__all__ = ['DefaultPAAOperatorCLI', 'NullStructuredLogger', 'build_app', 'build_default_cli', 'main']
