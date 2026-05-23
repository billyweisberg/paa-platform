from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.governance.component_vocabulary import (
    ComponentVocabularyError,
    validate_component_identity_vocabulary,
)


class ComponentVocabularyTests(unittest.TestCase):
    def test_validate_component_identity_vocabulary_accepts_canonical_values(self) -> None:
        validate_component_identity_vocabulary(
            system_layer='application-services',
            tier='runtime',
            status='active',
        )

    def test_validate_component_identity_vocabulary_rejects_noncanonical_layer(self) -> None:
        with self.assertRaises(ComponentVocabularyError):
            validate_component_identity_vocabulary(
                system_layer='application-orchestration',
                tier='runtime',
                status='active',
            )


if __name__ == '__main__':
    unittest.main()
