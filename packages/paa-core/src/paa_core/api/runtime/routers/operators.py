# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_operator_command_service
from paa_core.application.dto.operator import OperatorCommand, OperatorCommandRequest, OperatorInvocationContext
from paa_core.application.services import DefaultOperatorCommandApplicationService

router = APIRouter(prefix='/runtime/operators', tags=['runtime-operators'])


class OperatorCommandModel(BaseModel):
    command_family: str
    command_name: str
    subcommand_name: str | None = None


class OperatorInvocationContextModel(BaseModel):
    repo_root: str | None = None
    output_mode: str = 'table'
    dry_run: bool = False
    strict_mode: bool = True
    metadata: dict[str, object] = {}


class OperatorCommandRequestModel(BaseModel):
    command: OperatorCommandModel
    invocation_context: OperatorInvocationContextModel
    arguments: dict[str, object] = {}


def _string_key_map(value: object) -> dict[str, Any]:
    raw = cast(dict[object, object], value)
    return {str(key): item for key, item in raw.items()}


@router.post('/command')
def run_operator_command(
    request: OperatorCommandRequestModel,
    service: DefaultOperatorCommandApplicationService = Depends(get_operator_command_service),
) -> dict[str, object]:
    result = service.run_command(
        OperatorCommandRequest(
            command=OperatorCommand(
                command_family=cast(str, request.command.command_family),
                command_name=cast(str, request.command.command_name),
                subcommand_name=cast(str | None, request.command.subcommand_name),
            ),
            invocation_context=OperatorInvocationContext(
                repo_root=cast(str | None, request.invocation_context.repo_root),
                output_mode=cast(str, request.invocation_context.output_mode),
                dry_run=cast(bool, request.invocation_context.dry_run),
                strict_mode=cast(bool, request.invocation_context.strict_mode),
                metadata=_string_key_map(request.invocation_context.metadata),
            ),
            arguments=_string_key_map(request.arguments),
        )
    )
    return asdict(result)


@router.get('/supports/{command_family}')
def supports_operator_command_family(
    command_family: str,
    service: DefaultOperatorCommandApplicationService = Depends(get_operator_command_service),
) -> dict[str, object]:
    return {'command_family': command_family, 'supported': service.supports_command_family(command_family)}


__all__ = ['router']
