"""Project-local PAA config helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProducerProjectConfig:
    """Producer-side project config."""

    path: Path
    project_id: str
    mode: str
    authority_manifest_path: str
    supporting_docs_root: str
    artifact_examples_root: str
    publication_output_root: str
    github_repo: str


@dataclass(frozen=True)
class ConsumerProjectConfig:
    """Consumer-side project config."""

    path: Path
    project_id: str
    mode: str
    authority_install_root: str
    runtime_data_root: str
    github_repo: str
    queue_names: dict[str, str]
    db_profile: str


@dataclass(frozen=True)
class ProducerConsumerProjectConfig:
    """Unified producer-consumer project config."""

    path: Path
    project_id: str
    mode: str
    authority_manifest_path: str
    supporting_docs_root: str
    artifact_examples_root: str
    publication_output_root: str
    authority_install_root: str
    runtime_data_root: str
    github_repo: str
    queue_names: dict[str, str]
    db_profile: str


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file into a dict."""

    return json.loads(path.read_text())


def load_producer_project_config(path: Path) -> ProducerProjectConfig:
    """Load a producer project config from JSON."""

    data = load_json(path)
    return ProducerProjectConfig(
        path=path,
        project_id=data["project_id"],
        mode=data["mode"],
        authority_manifest_path=data["authority_manifest_path"],
        supporting_docs_root=data["supporting_docs_root"],
        artifact_examples_root=data["artifact_examples_root"],
        publication_output_root=data["publication_output_root"],
        github_repo=data["github_repo"],
    )


def load_consumer_project_config(path: Path) -> ConsumerProjectConfig:
    """Load a consumer project config from JSON."""

    data = load_json(path)
    return ConsumerProjectConfig(
        path=path,
        project_id=data["project_id"],
        mode=data["mode"],
        authority_install_root=data["authority_install_root"],
        runtime_data_root=data["runtime_data_root"],
        github_repo=data["github_repo"],
        queue_names=data["queue_names"],
        db_profile=data["db_profile"],
    )


def load_producer_consumer_project_config(path: Path) -> ProducerConsumerProjectConfig:
    """Load a unified producer-consumer project config from JSON."""

    data = load_json(path)
    return ProducerConsumerProjectConfig(
        path=path,
        project_id=data["project_id"],
        mode=data["mode"],
        authority_manifest_path=data["authority_manifest_path"],
        supporting_docs_root=data["supporting_docs_root"],
        artifact_examples_root=data["artifact_examples_root"],
        publication_output_root=data["publication_output_root"],
        authority_install_root=data["authority_install_root"],
        runtime_data_root=data["runtime_data_root"],
        github_repo=data["github_repo"],
        queue_names=data["queue_names"],
        db_profile=data["db_profile"],
    )
