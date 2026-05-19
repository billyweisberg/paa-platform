"""Structured metadata for governed architectural elements."""

from __future__ import annotations

from dataclasses import dataclass

from .language import AlignmentState, ComponentKind, LifecycleStage


@dataclass(frozen=True)
class GovernedComponentMetadata:
    """Minimal code-truth metadata for a governed component boundary."""

    name: str
    kind: ComponentKind
    alignment: AlignmentState
    lifecycle_stage: LifecycleStage
    owns: tuple[str, ...]
    does_not_own: tuple[str, ...]


__all__ = ['GovernedComponentMetadata']
