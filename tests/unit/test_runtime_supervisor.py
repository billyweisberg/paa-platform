from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.hosts.supervisor import RuntimeSupervisor


class _FakeHost:
    def __init__(self, name: str) -> None:
        self._name = name
        self.calls: list[dict[str, object]] = []

    def run_loop(self, **kwargs):
        self.calls.append(kwargs)
        return {
            'host_name': self._name,
            'iteration_count': kwargs['max_iterations'],
            'intake_mode': kwargs['intake_mode'],
        }


class RuntimeSupervisorTests(unittest.TestCase):
    def test_run_starts_all_three_hosts_and_collects_results(self) -> None:
        techlead_host = _FakeHost('techlead-runtime-host')
        dev_host = _FakeHost('dev-runtime-host')
        qa_host = _FakeHost('qa-runtime-host')
        supervisor = RuntimeSupervisor(
            techlead_host=techlead_host,
            dev_host=dev_host,
            qa_host=qa_host,
        )

        result = supervisor.run(
            intake_mode='claim_next',
            emit_next_assignment=True,
            emit_worker_result=True,
            emit_verification=True,
            max_iterations=2,
            poll_interval_seconds=0.1,
        )

        self.assertTrue(result['ok'])
        self.assertEqual(result['host_count'], 3)
        self.assertEqual(set(result['results'].keys()), {'techlead', 'dev', 'qa'})
        self.assertEqual(techlead_host.calls[0]['emit_next_assignment'], True)
        self.assertEqual(dev_host.calls[0]['emit_worker_result'], True)
        self.assertEqual(qa_host.calls[0]['emit_verification'], True)


if __name__ == '__main__':
    unittest.main()
