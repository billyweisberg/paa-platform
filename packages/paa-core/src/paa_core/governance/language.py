"""Governed code vocabulary that mirrors approved PAA language."""

from __future__ import annotations

from typing import Literal


AlignmentState = Literal['aligned', 'hybrid', 'legacy']
ImplementationState = Literal['defined', 'scaffolded', 'partially_implemented', 'implemented']
ValidationState = Literal['not_validated', 'lint_clean', 'unit_validated', 'proof_validated']
ComponentKind = Literal['service', 'repository', 'policy', 'adapter', 'projection', 'runtime_hub']
LifecycleStage = Literal['design', 'plan', 'build', 'test', 'deploy', 'operate', 'reference']

ALIGNMENT_STATES: tuple[AlignmentState, ...] = ('aligned', 'hybrid', 'legacy')
IMPLEMENTATION_STATES: tuple[ImplementationState, ...] = (
    'defined',
    'scaffolded',
    'partially_implemented',
    'implemented',
)
VALIDATION_STATES: tuple[ValidationState, ...] = (
    'not_validated',
    'lint_clean',
    'unit_validated',
    'proof_validated',
)
COMPONENT_KINDS: tuple[ComponentKind, ...] = (
    'service',
    'repository',
    'policy',
    'adapter',
    'projection',
    'runtime_hub',
)
LIFECYCLE_STAGES: tuple[LifecycleStage, ...] = (
    'design',
    'plan',
    'build',
    'test',
    'deploy',
    'operate',
    'reference',
)

__all__ = [
    'ALIGNMENT_STATES',
    'COMPONENT_KINDS',
    'IMPLEMENTATION_STATES',
    'LIFECYCLE_STAGES',
    'VALIDATION_STATES',
    'AlignmentState',
    'ComponentKind',
    'ImplementationState',
    'LifecycleStage',
    'ValidationState',
]
