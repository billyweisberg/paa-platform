from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
from paa_core.services.techlead_reset_recovery_decision import (
    TECHLEAD_RESET_RECOVERY_DECISION_SERVICE_METADATA,
)
from paa_core.services.techlead_reset_recovery_decision.contracts import (
    TechLeadResetRecoveryDecisionService,
)


class TechLeadResetRecoveryDecisionContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component_registry(self) -> None:
        self.assertEqual(
            TECHLEAD_RESET_RECOVERY_DECISION_SERVICE_METADATA.name,
            'TechLeadResetRecoveryDecisionService',
        )
        self.assertEqual(TECHLEAD_RESET_RECOVERY_DECISION_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_reset_recovery_decision_methods(self) -> None:
        self.assertTrue(hasattr(TechLeadResetRecoveryDecisionService, 'derive_reset_recovery_decision'))
        self.assertTrue(hasattr(TechLeadResetRecoveryDecisionService, 'supports_reset_recovery_decision'))

    def test_component_registry_exposes_metadata_by_component_name(self) -> None:
        self.assertIs(
            COMPONENT_METADATA_BY_NAME['TechLeadResetRecoveryDecisionService'],
            TECHLEAD_RESET_RECOVERY_DECISION_SERVICE_METADATA,
        )


if __name__ == '__main__':
    unittest.main()
