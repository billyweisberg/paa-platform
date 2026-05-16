import json
import unittest
from pathlib import Path
from unittest.mock import patch

from paa_producer.coder_brief_assembler import (
    _derive_forbidden_surfaces,
    _resolve_coder_brief_schema_path,
    assemble_coder_brief,
)
from paa_producer.derivation_readiness import DerivationReadinessResult
from paa_producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
PACKAGE_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json'
OUTPUT_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-assembled-draft-coder-run-brief.json'


class CoderBriefAssemblerTests(unittest.TestCase):
    def test_resolve_coder_brief_schema_path_prefers_local_copy(self):
        schema_path = _resolve_coder_brief_schema_path()
        self.assertEqual(schema_path, REPO_ROOT / 'schemas/derivation/coder_run_brief.schema.json')

    def test_derive_forbidden_surfaces_for_proof_slice(self):
        package = validate_stage1_design_package(PACKAGE_PATH, _resolve_stage1_schema_path())
        forbidden = _derive_forbidden_surfaces(package)
        self.assertIn('packages/paa-core/src/paa_core/repositories/component_design/postgres.py', forbidden)
        self.assertIn('packages/paa-core/src/paa_core/services/workflow_lifecycle/', forbidden)
        self.assertIn('migrations/postgres/', forbidden)

    def test_assemble_coder_brief_for_proof_slice_without_db_persist(self):
        if OUTPUT_PATH.exists():
            OUTPUT_PATH.unlink()
        result = assemble_coder_brief(
            package_path=PACKAGE_PATH,
            output_path=OUTPUT_PATH,
            persist_db=False,
        )
        self.assertEqual(result.project_slug, 'paa-platform')
        self.assertEqual(result.readiness_class, 'derivation_ready')
        self.assertTrue(OUTPUT_PATH.exists())
        brief = json.loads(OUTPUT_PATH.read_text())
        self.assertEqual(brief['schema_type'], 'coder_run_brief')
        self.assertEqual(brief['project'], 'paa-platform')
        self.assertEqual(brief['component_assignment']['component_name'], 'Component Design Planning Service')
        self.assertEqual(brief['execution_readiness']['readiness_class'], 'derivation_ready')
        OUTPUT_PATH.unlink(missing_ok=True)

    def test_assemble_coder_brief_refuses_to_overwrite_approved_authority(self):
        with patch(
            'paa_producer.coder_brief_assembler._existing_brief_for_design_package',
            return_value=('brief-id', 'brief-external', 'approved_brief'),
        ), patch(
            'paa_producer.coder_brief_assembler.evaluate_derivation_readiness'
        ) as mock_readiness, patch(
            'paa_producer.coder_brief_assembler._load_design_package_json'
        ) as mock_package:
            mock_readiness.return_value = DerivationReadinessResult(
                project_slug='paa-platform',
                package_id='package',
                package_path=str(PACKAGE_PATH),
                schema_path='schema',
                design_package_id='design-package',
                work_item_id='work-item',
                authority_version_id='authority-version',
                spec_fragment_id='spec-fragment',
                implementation_target_id='implementation-target',
                component_id='component-id',
                primary_component_name='Component Design Planning Service',
                readiness_class='derivation_ready',
                ready=True,
                blockers=[],
                warnings=[],
                checks=[],
                recommendations=[],
                evaluation_mode='evaluation_only',
            )
            mock_package.return_value = validate_stage1_design_package(PACKAGE_PATH, _resolve_stage1_schema_path())
            with self.assertRaisesRegex(RuntimeError, 'already approved_brief'):
                assemble_coder_brief(package_path=PACKAGE_PATH, persist_db=False)


if __name__ == '__main__':
    unittest.main()
