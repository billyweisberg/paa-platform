from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.methodology_execution import METHODOLOGY_EXECUTION_REPOSITORY_METADATA
from paa_core.repositories.methodology_execution.contracts import MethodologyExecutionRepository


class MethodologyExecutionRepositoryContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_repository(self) -> None:
        self.assertEqual(METHODOLOGY_EXECUTION_REPOSITORY_METADATA.name, 'MethodologyExecutionRepository')
        self.assertEqual(METHODOLOGY_EXECUTION_REPOSITORY_METADATA.kind, 'repository')

    def test_contract_protocol_exposes_first_slice_repository_methods(self) -> None:
        self.assertTrue(hasattr(MethodologyExecutionRepository, 'get_methodology_execution'))
        self.assertTrue(hasattr(MethodologyExecutionRepository, 'find_methodology_execution_by_primary_ref'))
        self.assertTrue(hasattr(MethodologyExecutionRepository, 'list_methodology_execution_events'))
        self.assertTrue(hasattr(MethodologyExecutionRepository, 'list_methodology_execution_bindings'))
        self.assertTrue(hasattr(MethodologyExecutionRepository, 'load_methodology_execution_projection_inputs'))
        self.assertTrue(hasattr(MethodologyExecutionRepository, 'upsert_methodology_execution'))
        self.assertTrue(hasattr(MethodologyExecutionRepository, 'append_methodology_execution_event'))
        self.assertTrue(hasattr(MethodologyExecutionRepository, 'replace_methodology_execution_bindings'))


if __name__ == '__main__':
    unittest.main()
