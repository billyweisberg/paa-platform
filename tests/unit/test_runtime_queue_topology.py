from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.support.config import (
    DEFAULT_RUNTIME_QUEUE_EXCHANGE,
    DEFAULT_RUNTIME_QUEUE_NAMES,
    runtime_queue_name_for_role,
    runtime_queue_name_for_schema,
)
from paa_core.runtime.support.runtime_paths import resolved_repo_runtime_queue_topology


class RuntimeQueueTopologyTests(unittest.TestCase):
    def test_repo_project_config_exposes_paa_native_queue_topology(self) -> None:
        topology = resolved_repo_runtime_queue_topology(ROOT)

        self.assertEqual(topology.queue_exchange, DEFAULT_RUNTIME_QUEUE_EXCHANGE)
        self.assertEqual(topology.queue_names, DEFAULT_RUNTIME_QUEUE_NAMES)

    def test_role_and_schema_resolution_use_canonical_paa_queue_keys(self) -> None:
        topology = resolved_repo_runtime_queue_topology(ROOT)

        self.assertEqual(runtime_queue_name_for_role('TechLead', topology=topology), 'paa-techlead')
        self.assertEqual(runtime_queue_name_for_role('Dev', topology=topology), 'paa-dev')
        self.assertEqual(runtime_queue_name_for_role('QA', topology=topology), 'paa-qa')
        self.assertEqual(runtime_queue_name_for_schema('worker_result_packet', topology=topology), 'paa-techlead')
        self.assertEqual(runtime_queue_name_for_schema('slice_result_packet', topology=topology), 'paa-qa')
        self.assertEqual(runtime_queue_name_for_schema('architect_cycle_packet', topology=topology), 'paa-dev')


if __name__ == '__main__':
    unittest.main()
