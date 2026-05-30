"""DTOs for the PAA operator CLI host surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OperatorCommand:
    """Normalized command identity for one operator invocation."""

    command_family: str
    command_name: str
    subcommand_name: str | None = None


@dataclass(frozen=True)
class OperatorInvocationContext:
    """Resolved environment and invocation context for one CLI run."""

    repo_root: str | None = None
    output_mode: str = 'table'
    dry_run: bool = False
    strict_mode: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperatorOutputMessage:
    """One human-facing output message."""

    level: str
    text: str


@dataclass(frozen=True)
class OperatorOutputTable:
    """One structured table payload for rendering."""

    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class OperatorOutputSection:
    """One output section composed of messages and optional tables."""

    title: str
    messages: tuple[OperatorOutputMessage, ...] = ()
    tables: tuple[OperatorOutputTable, ...] = ()
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperatorFailure:
    """Normalized operator-safe failure output."""

    code: str
    summary: str
    details: tuple[str, ...] = ()
    blocking: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperatorCommandRequest:
    """Normalized request object for one CLI command invocation."""

    command: OperatorCommand
    invocation_context: OperatorInvocationContext
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperatorCommandResult:
    """Normalized result object for one CLI command invocation."""

    command: OperatorCommand
    supported: bool
    success: bool
    exit_code: int
    sections: tuple[OperatorOutputSection, ...] = ()
    failure: OperatorFailure | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    'OperatorCommand',
    'OperatorCommandRequest',
    'OperatorCommandResult',
    'OperatorFailure',
    'OperatorInvocationContext',
    'OperatorOutputMessage',
    'OperatorOutputSection',
    'OperatorOutputTable',
]
