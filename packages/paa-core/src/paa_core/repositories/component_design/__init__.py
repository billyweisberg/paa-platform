"""Component Design repository package."""

from .contracts import ComponentDesignRepository
from .models import (
    BriefRealizationTargetUpsertSpec,
    ComponentUpsertSpec,
    ComponentElementUpsertSpec,
    CoderBriefRealizationTargetRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRealizationUpsertSpec,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
    DesignPackageRecord,
    DesignPackageSignoffRecord,
    DesignPackageSignoffUpsertSpec,
    DesignPackageUpsertSpec,
    ElementTypeRealizationLinkRecord,
    ElementTypeRealizationLinkSpec,
    RealizationTypeUpsertSpec,
)
from .postgres import PostgresComponentDesignRepository

__all__ = [
    'BriefRealizationTargetUpsertSpec',
    'ComponentUpsertSpec',
    'ComponentElementUpsertSpec',
    'CoderBriefRealizationTargetRecord',
    'ComponentDesignRepository',
    'ComponentElementRealizationRecord',
    'ComponentElementRealizationTypeRecord',
    'ComponentElementRealizationUpsertSpec',
    'ComponentElementRecord',
    'ComponentElementTypeRecord',
    'ComponentRecord',
    'DesignPackageRecord',
    'DesignPackageSignoffRecord',
    'DesignPackageSignoffUpsertSpec',
    'DesignPackageUpsertSpec',
    'ElementTypeRealizationLinkRecord',
    'ElementTypeRealizationLinkSpec',
    'PostgresComponentDesignRepository',
    'RealizationTypeUpsertSpec',
]
