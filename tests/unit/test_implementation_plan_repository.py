from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))


class ImplementationPlanRepositoryScaffoldTests(unittest.TestCase):
    def test_repository_scaffold_modules_import(self) -> None:
        from paa_core.repositories.implementation_plan import contracts, models, postgres

        self.assertEqual(contracts.__all__, [])
        self.assertEqual(models.__all__, [])
        self.assertEqual(postgres.__all__, [])


if __name__ == '__main__':
    unittest.main()
