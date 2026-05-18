from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.policies.deployment_capability import DefaultDeploymentCapabilityPolicy
from paa_core.repositories.execution_package import (
    ExecutionPackageInstallRecord,
    ExecutionPackageOverlayRecord,
    InstalledExecutionContextRecord,
)
from paa_core.services.execution_package_resolution import (
    DefaultExecutionPackageResolutionService,
    ExecutionPackageResolutionRequest,
)


class _Logger:
    def __init__(self) -> None:
        self.info_events: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **fields: object) -> None:
        self.info_events.append((event, fields))

    def warning(self, event: str, **fields: object) -> None:
        self.info_events.append((event, fields))


class _Repository:
    def __init__(self, context: InstalledExecutionContextRecord | None) -> None:
        self._context = context

    def get_execution_package_install(self, execution_package_install_id: str):
        if self._context and self._context.install.execution_package_install_id == execution_package_install_id:
            return self._context.install
        return None

    def get_active_install_for_execution_surface(self, execution_surface_key: str):
        if self._context and self._context.execution_surface_key == execution_surface_key:
            return self._context.install
        return None

    def get_active_install_for_repo_root(self, repo_root_path: str):
        if self._context and self._context.repo_root_path == repo_root_path:
            return self._context.install
        return None

    def get_active_install_for_runtime_root(self, runtime_root_path: str):
        if self._context and self._context.runtime_root_path == runtime_root_path:
            return self._context.install
        return None

    def list_overlays_for_install(self, execution_package_install_id: str):
        if self._context and self._context.install.execution_package_install_id == execution_package_install_id:
            return list(self._context.active_overlays)
        return []

    def list_active_overlays_for_install(self, execution_package_install_id: str):
        if self._context and self._context.install.execution_package_install_id == execution_package_install_id:
            return list(self._context.active_overlays)
        return []

    def resolve_active_execution_context(self, execution_surface_key: str):
        if self._context and self._context.execution_surface_key == execution_surface_key:
            return self._context
        return None


def _context() -> InstalledExecutionContextRecord:
    install = ExecutionPackageInstallRecord(
        execution_package_install_id='install-1',
        project_id='project-1',
        authority_version_id='authority-1',
        installed_by_agent_id='agent-1',
        installed_by_role_id='role-1',
        execution_surface_type='consumer_repo_runtime',
        execution_surface_key='surface-python-team',
        repo_root_path='/repo',
        runtime_root_path='/repo/.project/data/paa',
        install_slot_name='current',
        package_name='paa-authority',
        package_version='1.0.0',
        package_build_ref='build-1',
        package_hash='hash-1',
        package_schema_version='1.0',
        install_status='active',
        installed_from_source='published_authority_package',
        superseded_by_install_id=None,
        replaced_install_id=None,
        deactivation_reason_code=None,
        deactivation_reason_text=None,
        installed_manifest_path='/repo/.project/data/paa/authority/current/authority/manifest.json',
        installed_package_metadata_path='/repo/.project/data/paa/authority/current/package-metadata.json',
        installed_docs_root_path='/repo/.project/data/paa/authority/current/docs',
        installed_artifacts_root_path='/repo/.project/data/paa/authority/current/artifacts',
        installed_at='2026-05-17T12:00:00+00:00',
        activated_at='2026-05-17T12:01:00+00:00',
        deactivated_at=None,
        metadata={'consumer_context_key': 'python'},
        created_at='2026-05-17T12:00:00+00:00',
        updated_at='2026-05-17T12:01:00+00:00',
    )
    overlay = ExecutionPackageOverlayRecord(
        execution_package_overlay_id='overlay-1',
        execution_package_install_id='install-1',
        project_id='project-1',
        authority_version_id='authority-1',
        work_item_id='work-1',
        activated_by_agent_id='agent-1',
        activated_by_role_id='role-1',
        overlay_key='task-brief-overlay',
        overlay_type='task_overlay',
        overlay_name='Task Brief Overlay',
        overlay_version='1',
        overlay_hash='hash-overlay',
        overlay_schema_version='1.0',
        overlay_status='active',
        overlay_source='published_authority_package_overlay',
        replaced_overlay_id=None,
        superseded_by_overlay_id=None,
        deactivation_reason_code=None,
        deactivation_reason_text=None,
        overlay_root_path='/repo/.project/data/paa/authority/current/overlays/task-brief',
        overlay_metadata_path='/repo/.project/data/paa/authority/current/overlays/task-brief/overlay-metadata.json',
        overlay_manifest_task_path='/repo/.project/data/paa/authority/current/overlays/task-brief/manifest-task.json',
        overlay_summary_path='/repo/.project/data/paa/authority/current/overlays/task-brief/summary.json',
        activated_at='2026-05-17T12:02:00+00:00',
        deactivated_at=None,
        metadata={'scope': 'task'},
        created_at='2026-05-17T12:02:00+00:00',
        updated_at='2026-05-17T12:02:00+00:00',
    )
    return InstalledExecutionContextRecord(
        execution_surface_key='surface-python-team',
        execution_surface_type='consumer_repo_runtime',
        install=install,
        active_overlays=(overlay,),
        manifest_path=install.installed_manifest_path,
        package_metadata_path=install.installed_package_metadata_path,
        docs_root_path=install.installed_docs_root_path,
        artifacts_root_path=install.installed_artifacts_root_path,
        repo_root_path=install.repo_root_path,
        runtime_root_path=install.runtime_root_path,
        metadata={'package_name': install.package_name, 'active_overlay_keys': ('task-brief-overlay',)},
    )


class ExecutionPackageResolutionServiceTests(unittest.TestCase):
    def test_shell_exposes_injected_collaborators(self) -> None:
        repository = _Repository(_context())
        policy = DefaultDeploymentCapabilityPolicy()
        logger = _Logger()
        service = DefaultExecutionPackageResolutionService(
            repository=repository,
            capability_policy=policy,
            logger=logger,
        )

        self.assertIs(service.repository, repository)
        self.assertIs(service.capability_policy, policy)
        self.assertIs(service.logger, logger)

    def test_resolve_execution_context_returns_normalized_view(self) -> None:
        logger = _Logger()
        service = DefaultExecutionPackageResolutionService(
            repository=_Repository(_context()),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
            logger=logger,
        )

        view = service.resolve_execution_context(
            ExecutionPackageResolutionRequest(
                execution_surface_key='surface-python-team',
                required_artifact_refs=('installed_manifest', 'package_metadata'),
                required_overlay_keys=('task-brief-overlay',),
            )
        )

        self.assertEqual(view.execution_package_install_id, 'install-1')
        self.assertEqual(view.package_name, 'paa-authority')
        self.assertEqual(view.active_overlay_keys, ('task-brief-overlay',))
        self.assertTrue(view.capability_summary.allowed)
        self.assertEqual(view.gaps, ())
        self.assertTrue(
            any(event == 'execution_package_resolution.resolve_execution_context'
                for event, _fields in logger.info_events)
        )

    def test_surface_helper_routes_into_main_resolution_request(self) -> None:
        service = DefaultExecutionPackageResolutionService(
            repository=_Repository(_context()),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
            logger=_Logger(),
        )

        view = service.resolve_execution_context_for_surface(
            'surface-python-team',
            ExecutionPackageResolutionRequest(
                required_artifact_refs=('installed_manifest',),
            ),
        )

        self.assertEqual(view.execution_surface_key, 'surface-python-team')
        self.assertTrue(view.capability_summary.allowed)

    def test_repo_root_helper_resolves_context(self) -> None:
        service = DefaultExecutionPackageResolutionService(
            repository=_Repository(_context()),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
        )

        view = service.resolve_execution_context_for_repo_root(
            '/repo',
            ExecutionPackageResolutionRequest(
                required_artifact_refs=('installed_manifest',),
            ),
        )

        self.assertEqual(view.repo_root_path, '/repo')
        self.assertEqual(view.execution_package_install_id, 'install-1')

    def test_missing_install_returns_blocked_view_and_gap(self) -> None:
        service = DefaultExecutionPackageResolutionService(
            repository=_Repository(None),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
        )

        view = service.resolve_execution_context(
            ExecutionPackageResolutionRequest(
                execution_surface_key='surface-missing',
                execution_surface_type='consumer_repo_runtime',
                required_artifact_refs=('installed_manifest',),
            )
        )

        self.assertFalse(view.capability_summary.allowed)
        self.assertEqual(view.execution_package_install_id, None)
        self.assertEqual(view.gaps[0].gap_code, 'missing_active_install')

    def test_detect_execution_package_gaps_returns_capability_gap_set(self) -> None:
        service = DefaultExecutionPackageResolutionService(
            repository=_Repository(_context()),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
        )

        gaps = service.detect_execution_package_gaps(
            ExecutionPackageResolutionRequest(
                execution_surface_key='surface-python-team',
                required_overlay_keys=('missing-overlay',),
            )
        )

        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].gap_code, 'missing_required_overlay')

    def test_request_requires_a_resolvable_identity(self) -> None:
        service = DefaultExecutionPackageResolutionService(
            repository=_Repository(_context()),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
        )

        with self.assertRaisesRegex(ValueError, 'requires execution_surface_key, repo_root_path, or runtime_root_path'):
            service.resolve_execution_context(ExecutionPackageResolutionRequest())


if __name__ == '__main__':
    unittest.main()
