from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
from paa_core.services.techlead_delivery_review_decision import (
    TECHLEAD_DELIVERY_REVIEW_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_delivery_review_decision.contracts import (
    TechLeadDeliveryReviewDecisionService,
)


class TechLeadDeliveryReviewDecisionContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component_registry(self) -> None:
        self.assertEqual(
            TECHLEAD_DELIVERY_REVIEW_DECISION_SERVICE_METADATA.name,
            'TechLeadDeliveryReviewDecisionService',
        )
        self.assertEqual(TECHLEAD_DELIVERY_REVIEW_DECISION_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_delivery_review_decision_methods(self) -> None:
        self.assertTrue(hasattr(TechLeadDeliveryReviewDecisionService, 'derive_delivery_review_decision'))
        self.assertTrue(hasattr(TechLeadDeliveryReviewDecisionService, 'supports_delivery_review_decision'))

    def test_component_registry_exposes_metadata_by_component_name(self) -> None:
        self.assertIs(
            COMPONENT_METADATA_BY_NAME['TechLeadDeliveryReviewDecisionService'],
            TECHLEAD_DELIVERY_REVIEW_DECISION_SERVICE_METADATA,
        )


if __name__ == '__main__':
    unittest.main()
