import unittest
from unittest.mock import patch

from paa_core.handoff_runtime import resolve_work_item_id_from_message


class HandoffRuntimeTests(unittest.TestCase):
    def test_resolve_work_item_id_from_message_falls_back_to_package_and_brief_authority(self):
        message = {
            'project': 'paa-platform',
            'github_context': {
                'issue_number': 9002,
            },
            'payload': {
                'coder_brief_resolution': {
                    'package_id_external': 'paa-stage1-2026-05-16-component-design-planning-service',
                    'brief_id_external': 'paa-coder-2026-05-16-component-design-planning-service-governed-draft',
                }
            },
        }
        with patch('paa_core.handoff_runtime.run_psql', return_value='9e4509a5-5738-476b-a417-28e0012278f1\n') as mock_run:
            work_item_id = resolve_work_item_id_from_message(message)
        self.assertEqual(work_item_id, '9e4509a5-5738-476b-a417-28e0012278f1')
        called_sql = mock_run.call_args[0][0]
        self.assertIn('paa-stage1-2026-05-16-component-design-planning-service', called_sql)
        self.assertIn('paa-coder-2026-05-16-component-design-planning-service-governed-draft', called_sql)


if __name__ == '__main__':
    unittest.main()
