import json
import unittest
from pathlib import Path
from unittest.mock import patch

from paa_producer.derivation_readiness import (
    _artifact_signoff_roles,
    _has_brief_lifecycle_support,
    _required_signoff_roles,
    evaluate_derivation_readiness,
)
from paa_producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
PACKAGE_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json'


class DerivationReadinessTests(unittest.TestCase):
    def test_required_signoff_roles_for_proof_slice(self):
        package = validate_stage1_design_package(PACKAGE_PATH, _resolve_stage1_schema_path())
        self.assertEqual(
            _required_signoff_roles(package),
            ['Architect', 'Product Owner', 'Project Designer', 'TechLead'],
        )

    def test_artifact_signoff_roles_for_proof_slice(self):
        package = validate_stage1_design_package(PACKAGE_PATH, _resolve_stage1_schema_path())
        self.assertEqual(
            _artifact_signoff_roles(package),
            {'Architect', 'Product Owner', 'Project Designer', 'TechLead'},
        )

    def test_has_brief_lifecycle_support_accepts_text_bools(self):
        with patch('paa_producer.derivation_readiness._query_single_row', return_value=['true', 'true', 'true']):
            self.assertTrue(_has_brief_lifecycle_support())

    def test_evaluate_derivation_readiness_for_proof_slice(self):
        result = evaluate_derivation_readiness(package_path=PACKAGE_PATH)
        self.assertTrue(result.ready)
        self.assertEqual(result.readiness_class, 'derivation_ready')
        self.assertEqual(result.primary_component_name, 'Component Design Planning Service')
        self.assertFalse(result.blockers)


if __name__ == '__main__':
    unittest.main()
