"""Bootstrap CLI surface for extracted TechLead service inventory."""

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

TECHLEAD_SHELL_OWNERSHIP_POCKETS: tuple[dict[str, object], ...] = (
    {
        'name': 'terminal_lineage_override_policy',
        'status': 'remaining_business_logic',
        'path': 'packages/paa-consumer/src/paa_consumer/techlead.py:1180',
        'summary': 'Terminal lineage override still interprets proof-only-closed and fully closed merged state at shell level.',
    },
    {
        'name': 'workflow_framing_and_escalation_synthesis',
        'status': 'mixed_orchestration',
        'path': 'packages/paa-consumer/src/paa_consumer/techlead.py:1536',
        'summary': 'derive_workflow still performs packet-precedence framing and escalation synthesis around the extracted services.',
    },
)


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
        'techlead_shell_status': 'mostly_shell',
        'extracted_service_count': len(services),
        'extracted_services': services,
        'remaining_shell_pockets': list(TECHLEAD_SHELL_OWNERSHIP_POCKETS),
        'next_bootstrap_recommendation': (
            'Keep the consumer CLI thin and route new decision commands through the extracted services before touching queue or GitHub orchestration.'
        ),
    }


__all__ = [
    'TECHLEAD_EXTRACTED_SERVICE_NAMES',
    'TECHLEAD_SHELL_OWNERSHIP_POCKETS',
    'build_techlead_service_map',
]
