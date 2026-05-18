"""Default implementation of the deployment capability policy."""

from __future__ import annotations

from .models import (
    DeploymentCapabilityContext,
    DeploymentCapabilityDecision,
    DeploymentCapabilityRequest,
)


_ARTIFACT_ATTR_BY_KEY = {
    'installed_manifest': 'manifest_path',
    'package_metadata': 'package_metadata_path',
    'docs_root': 'docs_root_path',
    'artifacts_root': 'artifacts_root_path',
}


class DefaultDeploymentCapabilityPolicy:
    """Evaluate minimal deployment capability requirements over resolved execution context."""

    def evaluate_capability(
        self,
        request: DeploymentCapabilityRequest,
        context: DeploymentCapabilityContext,
    ) -> DeploymentCapabilityDecision:
        missing: list[str] = []
        blocking: list[str] = []
        satisfied: list[str] = []
        notes: list[str] = []

        if request.require_active_install:
            if context.install_status != 'active':
                missing.append('active_install')
                blocking.append(
                    f'Execution surface {context.execution_surface_key} does not have an active install.'
                )
            else:
                satisfied.append('active_install')

        if request.required_surface_types:
            if context.execution_surface_type not in request.required_surface_types:
                missing.append('execution_surface_type')
                blocking.append(
                    f'Execution surface type {context.execution_surface_type!r} is not allowed for this capability request.'
                )
            else:
                satisfied.append(f'surface_type:{context.execution_surface_type}')

        for artifact_key in request.required_artifact_refs:
            attr_name = _ARTIFACT_ATTR_BY_KEY.get(artifact_key)
            if attr_name is None:
                missing.append(f'unknown_artifact:{artifact_key}')
                blocking.append(f'Unknown deployment capability artifact requirement {artifact_key!r}.')
                continue
            if getattr(context, attr_name):
                satisfied.append(f'artifact:{artifact_key}')
            else:
                missing.append(f'artifact:{artifact_key}')
                blocking.append(
                    f'Missing required artifact surface {artifact_key!r} for execution surface {context.execution_surface_key}.'
                )

        active_overlay_keys = set(context.active_overlay_keys)
        for overlay_key in request.required_overlay_keys:
            if overlay_key in active_overlay_keys:
                satisfied.append(f'overlay:{overlay_key}')
            else:
                missing.append(f'overlay:{overlay_key}')
                blocking.append(
                    f'Missing required active overlay {overlay_key!r} for execution surface {context.execution_surface_key}.'
                )

        if not blocking:
            notes.append(
                f'Execution surface {context.execution_surface_key} satisfies the requested deployment capability set.'
            )

        return DeploymentCapabilityDecision(
            allowed=not blocking,
            missing_capabilities=tuple(missing),
            blocking_reasons=tuple(blocking),
            satisfied_capabilities=tuple(satisfied),
            notes=tuple(notes),
            metadata={
                'request_metadata': dict(request.metadata or {}),
                'context_metadata': dict(context.metadata or {}),
            },
        )


__all__ = ['DefaultDeploymentCapabilityPolicy']
