"""Repository interfaces and concrete implementations for PAA data access."""

from .component_design import (
    CoderBriefRealizationTargetRecord,
    ComponentDesignRepository,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
    PostgresComponentDesignRepository,
)

__all__ = [
    "CoderBriefRealizationTargetRecord",
    "ComponentDesignRepository",
    "ComponentElementRealizationRecord",
    "ComponentElementRealizationTypeRecord",
    "ComponentElementRecord",
    "ComponentElementTypeRecord",
    "ComponentRecord",
    "PostgresComponentDesignRepository",
]
