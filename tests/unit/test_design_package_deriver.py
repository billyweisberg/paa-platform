import unittest
from pathlib import Path
from unittest.mock import patch

from paa_producer.design_package_deriver import (
    _node_for_primary_component,
    _project_name_from_slug,
    _query_scalar,
    _resolve_stage1_schema_path,
    validate_stage1_design_package,
)


REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
PACKAGE_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json'


class DesignPackageDeriverTests(unittest.TestCase):
    def test_project_name_from_slug(self):
        self.assertEqual(_project_name_from_slug('paa-platform'), 'Paa Platform')
        self.assertEqual(_project_name_from_slug('fractal_core_python'), 'Fractal Core Python')

    def test_resolve_stage1_schema_path_prefers_local_copy(self):
        schema_path = _resolve_stage1_schema_path()
        self.assertEqual(
            schema_path,
            REPO_ROOT / 'schemas/derivation/stage1_design_package.schema.json',
        )

    def test_validate_proof_slice_stage1_package(self):
        schema_path = _resolve_stage1_schema_path()
        package = validate_stage1_design_package(PACKAGE_PATH, schema_path)
        self.assertEqual(package['package_id'], 'paa-stage1-2026-05-16-component-design-planning-service')
        self.assertEqual(package['status'], 'approved_for_derivation')

    def test_node_for_primary_component(self):
        schema_path = _resolve_stage1_schema_path()
        package = validate_stage1_design_package(PACKAGE_PATH, schema_path)
        node = _node_for_primary_component(package)
        self.assertEqual(node['component_name'], 'Component Design Planning Service')
        self.assertEqual(node['system_layer'], 'domain-services')
        self.assertEqual(node['tier'], 'runtime')

    def test_query_scalar_ignores_psql_command_tag_lines(self):
        with patch('paa_producer.design_package_deriver.run_psql', return_value='abc-123\nINSERT 0 1\n'):
            self.assertEqual(_query_scalar('select 1'), 'abc-123')


if __name__ == '__main__':
    unittest.main()
