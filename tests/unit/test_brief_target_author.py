import json
import unittest
from pathlib import Path

from paa_producer.brief_target_author import _target_blueprints, author_brief_targets
from paa_producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
PACKAGE_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json'
OUTPUT_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-authored-brief-targets.json'


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

    def test_author_brief_targets_for_proof_slice(self):
        OUTPUT_PATH.unlink(missing_ok=True)
        result = author_brief_targets(
            package_path=PACKAGE_PATH,
            output_path=OUTPUT_PATH,
        )
        self.assertEqual(result.project_slug, 'paa-platform')
        self.assertEqual(result.readiness_class, 'derivation_ready')
        self.assertEqual(result.target_count, 5)
        self.assertTrue(OUTPUT_PATH.exists())
        payload = json.loads(OUTPUT_PATH.read_text())
        self.assertEqual(payload['coder_run_brief_id'], result.coder_run_brief_id)
        self.assertEqual(len(payload['targets']), 5)
        self.assertEqual([target['sequence_order'] for target in payload['targets']], [10, 20, 30, 40, 50])
        OUTPUT_PATH.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
