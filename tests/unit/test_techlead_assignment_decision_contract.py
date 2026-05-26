from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_assignment_decision import (
    TECHLEAD_ASSIGNMENT_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_assignment_decision.contracts import TechLeadAssignmentDecisionService
from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME


class TechLeadAssignmentDecisionContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component_registry(self) -> None:
        self.assertEqual(TECHLEAD_ASSIGNMENT_DECISION_SERVICE_METADATA.name, 'TechLeadAssignmentDecisionService')
        self.assertEqual(TECHLEAD_ASSIGNMENT_DECISION_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_assignment_method(self) -> None:
        self.assertTrue(hasattr(TechLeadAssignmentDecisionService, 'derive_assignment_decision'))

    def test_component_registry_exposes_metadata_by_component_name(self) -> None:
        self.assertIs(
            COMPONENT_METADATA_BY_NAME['TechLeadAssignmentDecisionService'],
            TECHLEAD_ASSIGNMENT_DECISION_SERVICE_METADATA,
        )


if __name__ == '__main__':
    unittest.main()
