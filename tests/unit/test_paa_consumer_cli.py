from __future__ import annotations

import io
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-consumer' / 'src'))

from paa_consumer.__main__ import main


class PaaConsumerCliTests(unittest.TestCase):
    def test_consumer_cli_is_removed_and_directs_to_paa(self) -> None:
        buffer = io.StringIO()
        with patch('sys.stdout', buffer):
            exit_code = main()

        self.assertEqual(exit_code, 2)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload['reason'], 'paa_consumer_cli_removed')
        self.assertIn('paa runtime start', payload['suggested_commands'])


if __name__ == '__main__':
    unittest.main()
