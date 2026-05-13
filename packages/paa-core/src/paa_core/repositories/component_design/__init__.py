"""Component Design repository package."""

from .contracts import ComponentDesignRepository
from .models import (
    BriefRealizationTargetUpsertSpec,
    CoderBriefRealizationTargetRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRealizationUpsertSpec,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
    ElementTypeRealizationLinkSpec,
    RealizationTypeUpsertSpec,
)
from .postgres import PostgresComponentDesignRepository

__all__ = [
    'BriefRealizationTargetUpsertSpec',
    'CoderBriefRealizationTargetRecord',
    'ComponentDesignRepository',
    'ComponentElementRealizationRecord',
    'ComponentElementRealizationTypeRecord',
    'ComponentElementRealizationUpsertSpec',
    'ComponentElementRecord',
    'ComponentElementTypeRecord',
    'ComponentRecord',
    'ElementTypeRealizationLinkSpec',
    'PostgresComponentDesignRepository',
    'RealizationTypeUpsertSpec',
]
