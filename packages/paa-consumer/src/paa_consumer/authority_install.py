"""Consumer authority package installation helpers."""

from __future__ import annotations

import json
from pathlib import Path

from paa_core.install import install_authority_package as install_authority_package_impl


def install_authority(repo_root: Path, package_root: Path, authority_install_root: Path | None = None) -> dict[str, object]:
    result = install_authority_package_impl(repo_root=repo_root, package_root=package_root, authority_install_root=authority_install_root)
    metadata_path = result.authority_install_root / 'package-metadata.json'
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    return {
        'ok': True,
        'repo_root': str(result.repo_root),
        'package_root': str(result.package_root),
        'authority_install_root': str(result.authority_install_root),
        'package_metadata': metadata,
    }
