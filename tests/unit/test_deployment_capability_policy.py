from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.policies.deployment_capability import (
    DefaultDeploymentCapabilityPolicy,
    DeploymentCapabilityContext,
    DeploymentCapabilityRequest,
)


class DeploymentCapabilityPolicyTests(unittest.TestCase):
    def test_allows_context_with_required_artifacts_and_overlay(self) -> None:
        policy = DefaultDeploymentCapabilityPolicy()
        request = DeploymentCapabilityRequest(
            execution_surface_type='consumer_repo_runtime',
            execution_surface_key='surface-python-team',
            required_surface_types=('consumer_repo_runtime',),
            required_artifact_refs=('installed_manifest', 'package_metadata', 'artifacts_root'),
            required_overlay_keys=('task-brief-overlay',),
        )
        context = DeploymentCapabilityContext(
            install_status='active',
            execution_surface_type='consumer_repo_runtime',
            execution_surface_key='surface-python-team',
            manifest_path='.project/data/paa/authority/current/authority/manifest.json',
            package_metadata_path='.project/data/paa/authority/current/package-metadata.json',
            docs_root_path='.project/data/paa/authority/current/docs',
            artifacts_root_path='.project/data/paa/authority/current/artifacts',
            active_overlay_keys=('task-brief-overlay',),
        )
        decision = policy.evaluate_capability(request, context)

        self.assertTrue(decision.allowed)
        self.assertIn('active_install', decision.satisfied_capabilities)
        self.assertIn('artifact:installed_manifest', decision.satisfied_capabilities)
        self.assertIn('overlay:task-brief-overlay', decision.satisfied_capabilities)

    def test_blocks_context_missing_active_install_and_manifest(self) -> None:
        policy = DefaultDeploymentCapabilityPolicy()
        request = DeploymentCapabilityRequest(
            execution_surface_type='consumer_repo_runtime',
            execution_surface_key='surface-python-team',
            required_surface_types=('consumer_repo_runtime',),
            required_artifact_refs=('installed_manifest',),
            require_active_install=True,
        )
        context = DeploymentCapabilityContext(
            install_status='superseded',
            execution_surface_type='consumer_repo_runtime',
            execution_surface_key='surface-python-team',
            manifest_path=None,
            package_metadata_path='.project/data/paa/authority/current/package-metadata.json',
            docs_root_path=None,
            artifacts_root_path=None,
            active_overlay_keys=(),
        )
        decision = policy.evaluate_capability(request, context)

        self.assertFalse(decision.allowed)
        self.assertIn('active_install', decision.missing_capabilities)
        self.assertIn('artifact:installed_manifest', decision.missing_capabilities)


if __name__ == '__main__':
    unittest.main()
