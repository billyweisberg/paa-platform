"""Registry of governed code components that publish code-truth metadata."""

from __future__ import annotations

from paa_core.repositories.implementation_plan import IMPLEMENTATION_PLAN_REPOSITORY_METADATA
from paa_core.repositories.methodology_execution import METHODOLOGY_EXECUTION_REPOSITORY_METADATA
from paa_core.repositories.runtime_identity import RUNTIME_IDENTITY_REPOSITORY_METADATA
from paa_core.services.methodology_execution_state import (
    METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA,
)
from paa_core.services.methodology_execution_projection import (
    METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA,
)
from paa_core.services.methodology_execution_preflight import (
    METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA,
)
from paa_core.services.execution_package_resolution import EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA

try:
    from paa_cli import PAA_OPERATOR_CLI_METADATA
except ImportError:  # pragma: no cover - optional package import during partial environments
    PAA_OPERATOR_CLI_METADATA = None
from paa_core.services.techlead_acceptance_decision import (
    TECHLEAD_ACCEPTANCE_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_delivery_review_decision import (
    TECHLEAD_DELIVERY_REVIEW_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_closeout_decision import (
    TECHLEAD_CLOSEOUT_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_reset_recovery_decision import (
    TECHLEAD_RESET_RECOVERY_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_lineage_decision import (
    TECHLEAD_LINEAGE_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_assignment_decision import (
    TECHLEAD_ASSIGNMENT_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_worker_review_routing import (
    TECHLEAD_WORKER_REVIEW_ROUTING_SERVICE_METADATA,
)
from paa_core.services.techlead_worker import (
    TECHLEAD_WORKER_SERVICE_METADATA,
)
from paa_core.services.packet_context_assembly import (
    PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA,
)
from paa_core.services.dev_worker import (
    DEV_WORKER_SERVICE_METADATA,
)
from paa_core.services.qa_worker import (
    QA_WORKER_SERVICE_METADATA,
)
from paa_core.services.queue_packet_runtime_controller import (
    QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA,
)
from paa_core.services.queue_claim_runtime import (
    QUEUE_CLAIM_RUNTIME_SERVICE_METADATA,
)
from paa_core.services.packet_reference_resolution import (
    PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA,
)
from paa_core.services.workflow_lifecycle import WORKFLOW_LIFECYCLE_SERVICE_METADATA

from .component_metadata import GovernedComponentMetadata

GOVERNED_COMPONENTS: tuple[GovernedComponentMetadata, ...] = tuple(
    metadata
    for metadata in (
        WORKFLOW_LIFECYCLE_SERVICE_METADATA,
        EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA,
        TECHLEAD_ACCEPTANCE_DECISION_SERVICE_METADATA,
        TECHLEAD_ASSIGNMENT_DECISION_SERVICE_METADATA,
        TECHLEAD_DELIVERY_REVIEW_DECISION_SERVICE_METADATA,
        TECHLEAD_CLOSEOUT_DECISION_SERVICE_METADATA,
        TECHLEAD_LINEAGE_DECISION_SERVICE_METADATA,
        TECHLEAD_RESET_RECOVERY_DECISION_SERVICE_METADATA,
        TECHLEAD_WORKER_REVIEW_ROUTING_SERVICE_METADATA,
        TECHLEAD_WORKER_SERVICE_METADATA,
        PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA,
        DEV_WORKER_SERVICE_METADATA,
        QA_WORKER_SERVICE_METADATA,
        QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA,
        QUEUE_CLAIM_RUNTIME_SERVICE_METADATA,
        PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA,
        IMPLEMENTATION_PLAN_REPOSITORY_METADATA,
        METHODOLOGY_EXECUTION_REPOSITORY_METADATA,
        RUNTIME_IDENTITY_REPOSITORY_METADATA,
        METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA,
        METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA,
        METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA,
        PAA_OPERATOR_CLI_METADATA,
    )
    if metadata is not None
)

COMPONENT_METADATA_BY_NAME: dict[str, GovernedComponentMetadata] = {
    metadata.name: metadata for metadata in GOVERNED_COMPONENTS
}

__all__ = [
    'COMPONENT_METADATA_BY_NAME',
    'GOVERNED_COMPONENTS',
]
