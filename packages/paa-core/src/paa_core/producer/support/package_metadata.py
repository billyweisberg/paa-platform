"""Authority-package and install-metadata helper types."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PackageIdentity:
    """Stable identity for a published authority package."""

    project_id: str
    authority_version: str
    package_format_version: str


@dataclass(frozen=True)
class AuthorityPackageMetadata:
    """Published authority package metadata."""

    project_id: str
    authority_version: str
    published_at: str
    published_from_repo: str
    published_from_revision: str
    package_format_version: str
    producer_platform_version: str
    included_docs: list[str]
    included_artifacts: list[str]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable mapping."""

        return asdict(self)

