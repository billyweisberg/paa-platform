from __future__ import annotations

import json
from typing import Any, cast

from paa_core.application.dto.authority import AuthorityInstallRequest, AuthorityInstallResultView
from paa_core.runtime.support.install import install_authority_package


class DefaultAuthorityInstallApplicationService:
    def install_package(self, request: AuthorityInstallRequest) -> AuthorityInstallResultView:
        result = install_authority_package(
            repo_root=request.repo_root,
            package_root=request.package_root,
            authority_install_root=request.authority_install_root,
        )
        metadata_path = result.authority_install_root / 'package-metadata.json'
        metadata = cast(dict[str, Any], json.loads(metadata_path.read_text())) if metadata_path.exists() else {}
        return AuthorityInstallResultView(
            payload={
                'ok': True,
                'repo_root': str(result.repo_root),
                'package_root': str(result.package_root),
                'authority_install_root': str(result.authority_install_root),
                'package_metadata': metadata,
            },
            exit_code=0,
        )
