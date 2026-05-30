from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-cli' / 'src'))

from paa_cli import PAA_OPERATOR_CLI_METADATA
from paa_cli.contracts import PAAOperatorCLI


class PAAOperatorCLIContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(PAA_OPERATOR_CLI_METADATA.name, 'PAAOperatorCLI')
        self.assertEqual(PAA_OPERATOR_CLI_METADATA.kind, 'service')

    def test_contract_protocol_exposes_operator_command_methods(self) -> None:
        self.assertTrue(hasattr(PAAOperatorCLI, 'run_command'))
        self.assertTrue(hasattr(PAAOperatorCLI, 'supports_command_family'))


if __name__ == '__main__':
    unittest.main()
