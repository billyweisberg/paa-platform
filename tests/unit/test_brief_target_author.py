import unittest
from pathlib import Path

from paa_core.producer.brief_target_author import _target_blueprints
from paa_core.producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
PACKAGE_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json'


class BriefTargetAuthorTests(unittest.TestCase):
    def test_target_blueprints_cover_service_slice(self):
        package = validate_stage1_design_package(PACKAGE_PATH, _resolve_stage1_schema_path())
        blueprints = _target_blueprints(package)
        self.assertEqual([blueprint.realization_type_key for blueprint in blueprints], [
            'service_interface',
            'dto',
            'service_implementation',
            'test_module',
            'package_export',
        ])
        self.assertEqual(blueprints[2].depends_on_realization_key, blueprints[1].realization_key)


if __name__ == '__main__':
    unittest.main()
