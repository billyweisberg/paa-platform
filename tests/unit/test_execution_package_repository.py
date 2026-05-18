from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.execution_package import PostgresExecutionPackageRepository


class ExecutionPackageRepositoryTests(unittest.TestCase):
    def test_get_active_install_for_execution_surface_parses_root(self) -> None:
        repo = PostgresExecutionPackageRepository()
        output = '{"execution_package_install_id":"install-1","project_id":"project-1","authority_version_id":"authority-1","installed_by_agent_id":"agent-1","installed_by_role_id":"role-1","execution_surface_type":"consumer_repo_runtime","execution_surface_key":"surface-python-team","repo_root_path":"/repo","runtime_root_path":"/repo/.project/data/paa","install_slot_name":"current","package_name":"paa-authority","package_version":"1.0.0","package_build_ref":"build-1","package_hash":"hash-1","package_schema_version":"1.0","install_status":"active","installed_from_source":"published_authority_package","superseded_by_install_id":null,"replaced_install_id":null,"deactivation_reason_code":null,"deactivation_reason_text":null,"installed_manifest_path":"/repo/.project/data/paa/authority/current/authority/manifest.json","installed_package_metadata_path":"/repo/.project/data/paa/authority/current/package-metadata.json","installed_docs_root_path":"/repo/.project/data/paa/authority/current/docs","installed_artifacts_root_path":"/repo/.project/data/paa/authority/current/artifacts","installed_at":"2026-05-17T12:00:00+00:00","activated_at":"2026-05-17T12:01:00+00:00","deactivated_at":null,"metadata":{"consumer_context_key":"python"},"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:01:00+00:00"}'
        with patch('paa_core.repositories.execution_package.postgres.run_psql', return_value=output):
            row = repo.get_active_install_for_execution_surface('surface-python-team')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.execution_surface_type, 'consumer_repo_runtime')
        self.assertEqual(row.installed_manifest_path, '/repo/.project/data/paa/authority/current/authority/manifest.json')

    def test_list_active_overlays_for_install_parses_overlay_rows(self) -> None:
        repo = PostgresExecutionPackageRepository()
        output = '\n'.join(
            [
                '{"execution_package_overlay_id":"overlay-1","execution_package_install_id":"install-1","project_id":"project-1","authority_version_id":"authority-1","work_item_id":"work-1","activated_by_agent_id":"agent-1","activated_by_role_id":"role-1","overlay_key":"task-brief-overlay","overlay_type":"task_overlay","overlay_name":"Task Brief Overlay","overlay_version":"1","overlay_hash":"hash-overlay","overlay_schema_version":"1.0","overlay_status":"active","overlay_source":"published_authority_package_overlay","replaced_overlay_id":null,"superseded_by_overlay_id":null,"deactivation_reason_code":null,"deactivation_reason_text":null,"overlay_root_path":"/repo/.project/data/paa/authority/current/overlays/task-brief","overlay_metadata_path":"/repo/.project/data/paa/authority/current/overlays/task-brief/overlay-metadata.json","overlay_manifest_task_path":"/repo/.project/data/paa/authority/current/overlays/task-brief/manifest-task.json","overlay_summary_path":"/repo/.project/data/paa/authority/current/overlays/task-brief/summary.json","activated_at":"2026-05-17T12:02:00+00:00","deactivated_at":null,"metadata":{"scope":"task"},"created_at":"2026-05-17T12:02:00+00:00","updated_at":"2026-05-17T12:02:00+00:00"}'
            ]
        )
        with patch('paa_core.repositories.execution_package.postgres.run_psql', return_value=output):
            rows = repo.list_active_overlays_for_install('install-1')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].overlay_key, 'task-brief-overlay')
        self.assertEqual(rows[0].overlay_root_path, '/repo/.project/data/paa/authority/current/overlays/task-brief')

    def test_resolve_active_execution_context_combines_install_and_overlays(self) -> None:
        repo = PostgresExecutionPackageRepository()
        install_output = '{"execution_package_install_id":"install-1","project_id":"project-1","authority_version_id":"authority-1","installed_by_agent_id":"agent-1","installed_by_role_id":"role-1","execution_surface_type":"consumer_repo_runtime","execution_surface_key":"surface-python-team","repo_root_path":"/repo","runtime_root_path":"/repo/.project/data/paa","install_slot_name":"current","package_name":"paa-authority","package_version":"1.0.0","package_build_ref":"build-1","package_hash":"hash-1","package_schema_version":"1.0","install_status":"active","installed_from_source":"published_authority_package","superseded_by_install_id":null,"replaced_install_id":null,"deactivation_reason_code":null,"deactivation_reason_text":null,"installed_manifest_path":"/repo/.project/data/paa/authority/current/authority/manifest.json","installed_package_metadata_path":"/repo/.project/data/paa/authority/current/package-metadata.json","installed_docs_root_path":"/repo/.project/data/paa/authority/current/docs","installed_artifacts_root_path":"/repo/.project/data/paa/authority/current/artifacts","installed_at":"2026-05-17T12:00:00+00:00","activated_at":"2026-05-17T12:01:00+00:00","deactivated_at":null,"metadata":{"consumer_context_key":"python"},"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:01:00+00:00"}'
        overlay_output = '{"execution_package_overlay_id":"overlay-1","execution_package_install_id":"install-1","project_id":"project-1","authority_version_id":"authority-1","work_item_id":"work-1","activated_by_agent_id":"agent-1","activated_by_role_id":"role-1","overlay_key":"task-brief-overlay","overlay_type":"task_overlay","overlay_name":"Task Brief Overlay","overlay_version":"1","overlay_hash":"hash-overlay","overlay_schema_version":"1.0","overlay_status":"active","overlay_source":"published_authority_package_overlay","replaced_overlay_id":null,"superseded_by_overlay_id":null,"deactivation_reason_code":null,"deactivation_reason_text":null,"overlay_root_path":"/repo/.project/data/paa/authority/current/overlays/task-brief","overlay_metadata_path":"/repo/.project/data/paa/authority/current/overlays/task-brief/overlay-metadata.json","overlay_manifest_task_path":"/repo/.project/data/paa/authority/current/overlays/task-brief/manifest-task.json","overlay_summary_path":"/repo/.project/data/paa/authority/current/overlays/task-brief/summary.json","activated_at":"2026-05-17T12:02:00+00:00","deactivated_at":null,"metadata":{"scope":"task"},"created_at":"2026-05-17T12:02:00+00:00","updated_at":"2026-05-17T12:02:00+00:00"}'
        with patch('paa_core.repositories.execution_package.postgres.run_psql', side_effect=[install_output, overlay_output]):
            context = repo.resolve_active_execution_context('surface-python-team')

        self.assertIsNotNone(context)
        assert context is not None
        self.assertEqual(context.execution_surface_key, 'surface-python-team')
        self.assertEqual(context.install.package_name, 'paa-authority')
        self.assertEqual(context.metadata['active_overlay_keys'], ('task-brief-overlay',))


if __name__ == '__main__':
    unittest.main()
