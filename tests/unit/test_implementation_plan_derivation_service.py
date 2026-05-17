from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))


class ImplementationPlanDerivationServiceScaffoldTests(unittest.TestCase):
    def test_service_scaffold_modules_import(self) -> None:
        from paa_core.services.implementation_plan_derivation import contracts, default, models

        self.assertEqual(contracts.__all__, [])
        self.assertEqual(default.__all__, [])
        self.assertEqual(models.__all__, [])


if __name__ == '__main__':
    unittest.main()
