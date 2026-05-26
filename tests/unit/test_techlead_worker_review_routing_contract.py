from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
from paa_core.services.techlead_worker_review_routing import (
    TECHLEAD_WORKER_REVIEW_ROUTING_SERVICE_METADATA,
)
from paa_core.services.techlead_worker_review_routing.contracts import (
    TechLeadWorkerReviewRoutingService,
)


class TechLeadWorkerReviewRoutingContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component_registry(self) -> None:
        self.assertEqual(
            TECHLEAD_WORKER_REVIEW_ROUTING_SERVICE_METADATA.name,
            'TechLeadWorkerReviewRoutingService',
        )
        self.assertEqual(TECHLEAD_WORKER_REVIEW_ROUTING_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_review_routing_methods(self) -> None:
        self.assertTrue(hasattr(TechLeadWorkerReviewRoutingService, 'derive_worker_review_routing'))
        self.assertTrue(hasattr(TechLeadWorkerReviewRoutingService, 'supports_worker_review_routing'))

    def test_component_registry_exposes_metadata_by_component_name(self) -> None:
        self.assertIs(
            COMPONENT_METADATA_BY_NAME['TechLeadWorkerReviewRoutingService'],
            TECHLEAD_WORKER_REVIEW_ROUTING_SERVICE_METADATA,
        )


if __name__ == '__main__':
    unittest.main()
