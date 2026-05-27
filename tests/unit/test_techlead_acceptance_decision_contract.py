from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
from paa_core.services.techlead_acceptance_decision import (
    TECHLEAD_ACCEPTANCE_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_acceptance_decision.contracts import (
    TechLeadAcceptanceDecisionService,
)


class TechLeadAcceptanceDecisionContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component_registry(self) -> None:
        self.assertEqual(
            TECHLEAD_ACCEPTANCE_DECISION_SERVICE_METADATA.name,
            'TechLeadAcceptanceDecisionService',
        )
        self.assertEqual(TECHLEAD_ACCEPTANCE_DECISION_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_acceptance_decision_methods(self) -> None:
        self.assertTrue(hasattr(TechLeadAcceptanceDecisionService, 'derive_acceptance_decision'))
        self.assertTrue(hasattr(TechLeadAcceptanceDecisionService, 'supports_acceptance_decision'))

    def test_component_registry_exposes_metadata_by_component_name(self) -> None:
        self.assertIs(
            COMPONENT_METADATA_BY_NAME['TechLeadAcceptanceDecisionService'],
            TECHLEAD_ACCEPTANCE_DECISION_SERVICE_METADATA,
        )


if __name__ == '__main__':
    unittest.main()
