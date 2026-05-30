"""Result-normalization support for the PAA operator CLI."""

from __future__ import annotations

from typing import Any

from .models import (
    OperatorCommand,
    OperatorCommandResult,
    OperatorFailure,
    OperatorOutputMessage,
    OperatorOutputSection,
)


class CommandResultNormalizer:
    """Normalize adapter outputs into stable CLI-owned result objects."""

    def normalize(self, command: OperatorCommand, raw_result: Any) -> OperatorCommandResult:
        if isinstance(raw_result, OperatorCommandResult):
            return raw_result
        if isinstance(raw_result, dict):
            return self._from_mapping(command, raw_result)
        return OperatorCommandResult(
            command=command,
            supported=False,
            success=False,
            exit_code=2,
            failure=OperatorFailure(
                code='unsupported_result_shape',
                summary='Adapter returned an unsupported result shape.',
                details=(type(raw_result).__name__,),
            ),
        )

    def _from_mapping(self, command: OperatorCommand, payload: dict[str, Any]) -> OperatorCommandResult:
        success = bool(payload.get('success', True))
        supported = bool(payload.get('supported', True))
        exit_code = int(payload.get('exit_code', 0 if success else 1))
        messages = tuple(
            OperatorOutputMessage(level=item.get('level', 'info'), text=item.get('text', ''))
            for item in payload.get('messages', ())
        )
        section = OperatorOutputSection(
            title=payload.get('section_title', 'Result'),
            messages=messages,
            data=dict(payload.get('data', {})),
        )
        failure_payload = payload.get('failure')
        failure = None
        if failure_payload:
            failure = OperatorFailure(
                code=failure_payload.get('code', 'failed'),
                summary=failure_payload.get('summary', 'Command failed.'),
                details=tuple(failure_payload.get('details', ())),
                blocking=bool(failure_payload.get('blocking', True)),
                metadata=dict(failure_payload.get('metadata', {})),
            )
        return OperatorCommandResult(
            command=command,
            supported=supported,
            success=success,
            exit_code=exit_code,
            sections=(section,),
            failure=failure,
            metadata=dict(payload.get('metadata', {})),
        )


__all__ = ['CommandResultNormalizer']
