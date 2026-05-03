"""Authority publication helpers for producer repos."""

from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from paa_core.config import ProducerProjectConfig
from paa_core.package_metadata import AuthorityPackageMetadata
from paa_core.paths import authority_package_staging_root, ensure_directory, resolve_from_repo_root

PACKAGE_FORMAT_VERSION = "0.1.0"
PRODUCER_PLATFORM_VERSION = "0.1.0"


@dataclass(frozen=True)
class PublishPaths:
    """Resolved producer-side publication paths."""

    repo_root: Path
    manifest_path: Path
    schema_path: Path
    supporting_docs_root: Path
    publication_output_root: Path


@dataclass(frozen=True)
class PublishResult:
    """Result of a producer publication run."""

    package_root: Path
    metadata_path: Path
    manifest_path: Path
    authority_version: str


def resolve_publish_paths(repo_root: Path, config: ProducerProjectConfig) -> PublishPaths:
    """Resolve all producer publication paths from repo root + config."""

    manifest_path = resolve_from_repo_root(repo_root, config.authority_manifest_path)
    docs_root = resolve_from_repo_root(repo_root, config.supporting_docs_root)
    return PublishPaths(
        repo_root=repo_root,
        manifest_path=manifest_path,
        schema_path=manifest_path.parent / "project-authority.schema.json",
        supporting_docs_root=docs_root,
        publication_output_root=resolve_from_repo_root(repo_root, config.publication_output_root),
    )


def copy_file(src: Path, dst: Path) -> None:
    """Copy a file, creating parent directories as needed."""

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_authority_package(
    *,
    paths: PublishPaths,
    supporting_docs: list[str],
    artifact_paths: list[str] | None = None,
) -> PublishResult:
    """Build a staged authority package without publishing it elsewhere."""

    artifact_paths = artifact_paths or []
    manifest = json.loads(paths.manifest_path.read_text())
    package_name = f"{manifest['project']['project_id']}-authority-{manifest['project']['authority_version']}"

    with tempfile.TemporaryDirectory(prefix="paa-authority-package-") as tmp:
        tmp_root = Path(tmp)
        package_root = authority_package_staging_root(tmp_root) / package_name
        ensure_directory(package_root / "authority")
        ensure_directory(package_root / "docs")
        ensure_directory(package_root / "artifacts")

        manifest_dst = package_root / "authority" / paths.manifest_path.name
        schema_dst = package_root / "authority" / paths.schema_path.name
        copy_file(paths.manifest_path, manifest_dst)
        copy_file(paths.schema_path, schema_dst)

        for name in supporting_docs:
            copy_file(paths.supporting_docs_root / name, package_root / "docs" / name)

        included_artifacts: list[str] = []
        for rel in artifact_paths:
            src = resolve_from_repo_root(paths.repo_root, rel)
            dst = package_root / "artifacts" / src.name
            copy_file(src, dst)
            included_artifacts.append(str(Path("artifacts") / src.name))

        revision = (
            subprocess.run(
                ["git", "-C", str(paths.repo_root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
        )

        metadata = AuthorityPackageMetadata(
            project_id=manifest["project"]["project_id"],
            authority_version=manifest["project"]["authority_version"],
            published_at=manifest["project"]["published_at"],
            published_from_repo=manifest["project"]["repo"],
            published_from_revision=revision,
            package_format_version=PACKAGE_FORMAT_VERSION,
            producer_platform_version=PRODUCER_PLATFORM_VERSION,
            included_docs=[str(Path("docs") / name) for name in supporting_docs],
            included_artifacts=included_artifacts,
        )
        metadata_path = package_root / "package-metadata.json"
        metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2) + "\n")

        destination_root = ensure_directory(paths.publication_output_root) / package_name
        if destination_root.exists():
            shutil.rmtree(destination_root)
        shutil.copytree(package_root, destination_root)

        return PublishResult(
            package_root=destination_root,
            metadata_path=destination_root / "package-metadata.json",
            manifest_path=destination_root / "authority" / paths.manifest_path.name,
            authority_version=manifest["project"]["authority_version"],
        )
