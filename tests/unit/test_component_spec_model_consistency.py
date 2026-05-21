from __future__ import annotations

import unittest
from unittest.mock import patch

from paa_core.governance.component_spec_model_consistency import (
    evaluate_component_spec_model_consistency,
)
from paa_core.governance.component_spec_materialization import (
    extract_component_spec_materialization_seed,
)


WORKFLOW_SPEC_PATH = "/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md"
EXECUTION_SPEC_PATH = "/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-execution-package-resolution-service-component-spec.md"


class ComponentSpecModelConsistencyTests(unittest.TestCase):
    def test_reports_no_gaps_when_model_matches_rows(self) -> None:
        seed = extract_component_spec_materialization_seed(WORKFLOW_SPEC_PATH)
        with patch(
            'paa_core.governance.component_spec_model_consistency._load_model_detail',
            return_value=type('Detail', (), {
                'component_count': 1,
                'element_count': 4,
                'realization_count': 5,
                'activity_count': 4,
                'dependency_count': 3,
                'plan_present': True,
                'model_element_keys': tuple(sorted(element.element_name for element in seed.component_elements)),
                'model_realization_keys': tuple(sorted(realization.realization_key for realization in seed.realizations)),
                'model_activity_keys': tuple(sorted(activity.activity_key for activity in seed.activity_seeds)),
                'model_dependency_pairs': tuple(sorted(f"{dependency.depends_on_activity_key}->{dependency.activity_key}" for dependency in seed.activity_dependencies)),
            })(),
        ):
            report = evaluate_component_spec_model_consistency(seed)
        self.assertEqual(report.blocking_gaps, ())

    def test_detects_row_level_mismatch_when_model_differs(self) -> None:
        seed = extract_component_spec_materialization_seed(EXECUTION_SPEC_PATH)
        with patch(
            'paa_core.governance.component_spec_model_consistency._load_model_detail',
            return_value=type('Detail', (), {
                'component_count': 1,
                'element_count': 4,
                'realization_count': 4,
                'activity_count': 3,
                'dependency_count': 2,
                'plan_present': True,
                'model_element_keys': ('execution_context_resolution_interface', 'wrong_element'),
                'model_realization_keys': ('wrong_realization',),
                'model_activity_keys': ('wrong_activity',),
                'model_dependency_pairs': ('wrong->pair',),
            })(),
        ):
            report = evaluate_component_spec_model_consistency(seed)
        self.assertIn('realization_count_mismatch', report.blocking_gaps)
        self.assertIn('activity_count_mismatch', report.blocking_gaps)
        self.assertIn('dependency_count_mismatch', report.blocking_gaps)
        self.assertIn('element_key_mismatch', report.blocking_gaps)
        self.assertIn('realization_key_mismatch', report.blocking_gaps)
        self.assertIn('activity_key_mismatch', report.blocking_gaps)
        self.assertIn('dependency_pair_mismatch', report.blocking_gaps)


if __name__ == '__main__':
    unittest.main()
