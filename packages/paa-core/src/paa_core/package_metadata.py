"""Authority-package and install-metadata helper types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PackageIdentity:
    """Stable identity for a published authority package."""

    project_id: str
    authority_version: str
    package_format_version: str

