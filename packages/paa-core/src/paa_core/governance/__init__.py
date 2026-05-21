"""Governed vocabulary and proof helpers shared between docs and code."""

from .component_metadata import GovernedComponentMetadata
from .component_spec_materialization import (
    ActivityDependencySeed,
    ActivitySeed,
    ComponentElementSeed,
    ComponentIdentitySeed,
    ComponentRealizationSeed,
    ComponentSpecExtractionError,
    ComponentSpecMaterializationSeed,
    ImplementationPlanSeed,
    VerificationSurfaceSeed,
    extract_component_spec_materialization_seed,
    seed_as_jsonable as component_spec_seed_as_jsonable,
)
from .component_spec_model_consistency import (
    ComponentSpecModelConsistencyReport,
    check_component_spec_model_consistency,
    evaluate_component_spec_model_consistency,
    report_as_jsonable as component_spec_model_report_as_jsonable,
)
from .language import (
    ALIGNMENT_STATES,
    COMPONENT_KINDS,
    IMPLEMENTATION_STATES,
    LIFECYCLE_STAGES,
    VALIDATION_STATES,
    AlignmentState,
    ComponentKind,
    ImplementationState,
    LifecycleStage,
    ValidationState,
)

__all__ = [
    'ALIGNMENT_STATES',
    'ActivityDependencySeed',
    'ActivitySeed',
    'AlignmentState',
    'COMPONENT_KINDS',
    'ComponentElementSeed',
    'ComponentIdentitySeed',
    'ComponentKind',
    'ComponentRealizationSeed',
    'ComponentSpecExtractionError',
    'ComponentSpecMaterializationSeed',
    'ComponentSpecModelConsistencyReport',
    'GovernedComponentMetadata',
    'IMPLEMENTATION_STATES',
    'ImplementationPlanSeed',
    'ImplementationState',
    'LIFECYCLE_STAGES',
    'LifecycleStage',
    'VALIDATION_STATES',
    'ValidationState',
    'VerificationSurfaceSeed',
    'component_spec_model_report_as_jsonable',
    'component_spec_seed_as_jsonable',
    'check_component_spec_model_consistency',
    'evaluate_component_spec_model_consistency',
    'extract_component_spec_materialization_seed',
]
