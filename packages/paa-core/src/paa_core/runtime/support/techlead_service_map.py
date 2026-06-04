"""Static reporting helpers for TechLead service ownership."""

from __future__ import annotations

from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME

TECHLEAD_EXTRACTED_SERVICE_NAMES: tuple[str, ...] = (
    'TechLeadAssignmentDecisionService',
    'TechLeadWorkerReviewRoutingService',
    'TechLeadAcceptanceDecisionService',
    'TechLeadDeliveryReviewDecisionService',
    'TechLeadResetRecoveryDecisionService',
    'TechLeadLineageDecisionService',
    'TechLeadCloseoutDecisionService',
)

TECHLEAD_SHELL_OWNERSHIP_POCKETS: tuple[dict[str, object], ...] = ()


def build_techlead_service_map() -> dict[str, object]:
    services = []
    for component_name in TECHLEAD_EXTRACTED_SERVICE_NAMES:
        metadata = COMPONENT_METADATA_BY_NAME[component_name]
        services.append(
            {
                'component_name': metadata.name,
                'kind': metadata.kind,
                'alignment': metadata.alignment,
                'lifecycle_stage': metadata.lifecycle_stage,
                'owns': list(metadata.owns),
                'does_not_own': list(metadata.does_not_own),
            }
        )
    return {
        'techlead_shell_status': 'retired',
        'extracted_service_count': len(services),
        'extracted_services': services,
        'remaining_shell_pockets': list(TECHLEAD_SHELL_OWNERSHIP_POCKETS),
        'next_bootstrap_recommendation': (
            'Keep the runtime host thin and route new decision commands through extracted services and runtime hosts.'
        ),
    }


__all__ = [
    'TECHLEAD_EXTRACTED_SERVICE_NAMES',
    'TECHLEAD_SHELL_OWNERSHIP_POCKETS',
    'build_techlead_service_map',
]
