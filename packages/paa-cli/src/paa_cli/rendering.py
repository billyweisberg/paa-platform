"""Output-rendering support for the PAA operator CLI."""

from __future__ import annotations

import json

from .models import OperatorCommandResult, OperatorOutputSection, OperatorOutputTable


class OutputRenderer:
    """Render operator command results for machine or human consumption."""

    def render(self, result: OperatorCommandResult, *, output_mode: str = 'table') -> str:
        if output_mode == 'json':
            return self._render_json(result)
        if output_mode == 'summary':
            return self._render_summary(result)
        return self._render_table(result)

    def _render_json(self, result: OperatorCommandResult) -> str:
        payload = {
            'command_family': result.command.command_family,
            'command_name': result.command.command_name,
            'supported': result.supported,
            'success': result.success,
            'exit_code': result.exit_code,
            'sections': [self._section_payload(section) for section in result.sections],
            'failure': None if result.failure is None else {
                'code': result.failure.code,
                'summary': result.failure.summary,
                'details': list(result.failure.details),
                'blocking': result.failure.blocking,
                'metadata': result.failure.metadata,
            },
            'metadata': result.metadata,
        }
        return json.dumps(payload, indent=2)

    def _render_summary(self, result: OperatorCommandResult) -> str:
        lines = [
            f"{result.command.command_family}:{result.command.command_name}",
            f"supported={str(result.supported).lower()} success={str(result.success).lower()} exit_code={result.exit_code}",
        ]
        for section in result.sections:
            for message in section.messages:
                lines.append(f"[{message.level}] {message.text}")
        if result.failure is not None:
            lines.append(f"failure={result.failure.code}: {result.failure.summary}")
        return '\n'.join(lines)

    def _render_table(self, result: OperatorCommandResult) -> str:
        lines = []
        for section in result.sections:
            lines.extend(self._render_section(section))
        if result.failure is not None:
            lines.append(f"FAILURE | {result.failure.code} | {result.failure.summary}")
        return '\n'.join(lines).strip()

    def _render_section(self, section: OperatorOutputSection) -> list[str]:
        lines = [section.title]
        for message in section.messages:
            lines.append(f"- {message.level}: {message.text}")
        for table in section.tables:
            lines.extend(self._render_output_table(table))
        return lines

    @staticmethod
    def _render_output_table(table: OperatorOutputTable) -> list[str]:
        lines = [table.title, ' | '.join(table.columns)]
        for row in table.rows:
            lines.append(' | '.join(row))
        return lines

    @staticmethod
    def _section_payload(section: OperatorOutputSection) -> dict[str, object]:
        return {
            'title': section.title,
            'messages': [{'level': msg.level, 'text': msg.text} for msg in section.messages],
            'tables': [
                {
                    'title': table.title,
                    'columns': list(table.columns),
                    'rows': [list(row) for row in table.rows],
                }
                for table in section.tables
            ],
            'data': section.data,
        }


__all__ = ['OutputRenderer']
