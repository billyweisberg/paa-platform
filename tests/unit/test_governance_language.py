from __future__ import annotations

import unittest
from typing import get_args

from paa_core.governance.language import (
    ALIGNMENT_STATES,
    COMPONENT_KINDS,
    IMPLEMENTATION_STATES,
    LIFECYCLE_STAGES,
    VALIDATION_STATES,
    AlignmentState,
    ComponentKind,
    ImplementationState,
    LifecycleStage,
    ValidationState,
)


class GovernanceLanguageTests(unittest.TestCase):
    def test_alignment_state_literal_matches_exported_values(self) -> None:
        self.assertEqual(tuple(get_args(AlignmentState)), ALIGNMENT_STATES)

    def test_implementation_state_literal_matches_exported_values(self) -> None:
        self.assertEqual(tuple(get_args(ImplementationState)), IMPLEMENTATION_STATES)

    def test_validation_state_literal_matches_exported_values(self) -> None:
        self.assertEqual(tuple(get_args(ValidationState)), VALIDATION_STATES)

    def test_component_kind_literal_matches_exported_values(self) -> None:
        self.assertEqual(tuple(get_args(ComponentKind)), COMPONENT_KINDS)

    def test_lifecycle_stage_literal_matches_exported_values(self) -> None:
        self.assertEqual(tuple(get_args(LifecycleStage)), LIFECYCLE_STAGES)


if __name__ == "__main__":
    unittest.main()
