"""Project-local PAA config helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_RUNTIME_QUEUE_EXCHANGE = 'paa-handoff'
DEFAULT_RUNTIME_QUEUE_NAMES: dict[str, str] = {
    'techlead': 'paa-techlead',
    'dev': 'paa-dev',
    'qa': 'paa-qa',
}
_QUEUE_NAME_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    'techlead': ('techlead', 'architect'),
    'dev': ('dev', 'python'),
    'qa': ('qa',),
}
_ROLE_TO_QUEUE_KEY: dict[str, str] = {
    'TechLead': 'techlead',
    'Dev': 'dev',
    'Python Dev': 'dev',
    'Frontend Dev': 'dev',
    'Backend Dev': 'dev',
    'Infra Dev': 'dev',
    'Docs Dev': 'dev',
    'QA': 'qa',
    'Architect': 'techlead',
    'Authority Architect': 'techlead',
    'Delivery Architect': 'techlead',
}
_SCHEMA_TO_QUEUE_KEY: dict[str, str] = {
    'architect_cycle_packet': 'dev',
    'slice_result_packet': 'qa',
    'worker_result_packet': 'techlead',
    'qa_verification_packet': 'techlead',
    'delivery_review_packet': 'techlead',
}


@dataclass(frozen=True)
class ProducerProjectConfig:
    """Producer-side project config."""

    path: Path
    project_id: str
    project_pack: str
    mode: str
    authority_manifest_path: str
    supporting_docs_root: str
    artifact_examples_root: str
    publication_output_root: str
    github_repo: str
    supporting_docs: list[str]
    artifact_paths: list[str]


@dataclass(frozen=True)
class RuntimeProjectConfig:
    """Runtime-side project config."""

    path: Path
    project_id: str
    project_pack: str
    mode: str
    authority_install_root: str
    runtime_data_root: str
    github_repo: str
    queue_names: dict[str, str]
    db_profile: str
    queue_exchange: str | None = None
    team_worker_roles_path: str | None = None


@dataclass(frozen=True)
class UnifiedRuntimeProjectConfig:
    """Unified producer/runtime project config."""

    path: Path
    project_id: str
    project_pack: str
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
    queue_exchange: str | None = None
    team_worker_roles_path: str | None = None


@dataclass(frozen=True)
class RuntimeQueueTopology:
    """Repo-local queue topology configuration."""

    path: Path | None
    queue_names: dict[str, str]
    queue_exchange: str | None = None


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file into a dict."""

    return json.loads(path.read_text())


def load_producer_project_config(path: Path) -> ProducerProjectConfig:
    """Load a producer project config from JSON."""

    data = load_json(path)
    return ProducerProjectConfig(
        path=path,
        project_id=data["project_id"],
        project_pack=data.get("project_pack", "fractal-core"),
        mode=data["mode"],
        authority_manifest_path=data["authority_manifest_path"],
        supporting_docs_root=data["supporting_docs_root"],
        artifact_examples_root=data["artifact_examples_root"],
        publication_output_root=data["publication_output_root"],
        github_repo=data["github_repo"],
        supporting_docs=data.get("supporting_docs", []),
        artifact_paths=data.get("artifact_paths", []),
    )


def load_runtime_project_config(path: Path) -> RuntimeProjectConfig:
    """Load a runtime project config from JSON."""

    data = load_json(path)
    return RuntimeProjectConfig(
        path=path,
        project_id=data["project_id"],
        project_pack=data.get("project_pack", "fractal-core"),
        mode=data["mode"],
        authority_install_root=data["authority_install_root"],
        runtime_data_root=data["runtime_data_root"],
        github_repo=data["github_repo"],
        queue_names=data["queue_names"],
        queue_exchange=data.get("queue_exchange"),
        db_profile=data["db_profile"],
        team_worker_roles_path=data.get("team_worker_roles_path"),
    )


def load_unified_runtime_project_config(path: Path) -> UnifiedRuntimeProjectConfig:
    """Load a unified producer/runtime project config from JSON."""

    data = load_json(path)
    return UnifiedRuntimeProjectConfig(
        path=path,
        project_id=data["project_id"],
        project_pack=data.get("project_pack", "fractal-core"),
        mode=data["mode"],
        authority_manifest_path=data["authority_manifest_path"],
        supporting_docs_root=data["supporting_docs_root"],
        artifact_examples_root=data["artifact_examples_root"],
        publication_output_root=data["publication_output_root"],
        authority_install_root=data["authority_install_root"],
        runtime_data_root=data["runtime_data_root"],
        github_repo=data["github_repo"],
        queue_names=data["queue_names"],
        queue_exchange=data.get("queue_exchange"),
        db_profile=data["db_profile"],
        team_worker_roles_path=data.get("team_worker_roles_path"),
    )


def load_runtime_queue_topology(path: Path) -> RuntimeQueueTopology:
    """Load only queue topology from one repo-local project config."""

    data = load_json(path)
    return RuntimeQueueTopology(
        path=path,
        queue_names=dict(data.get("queue_names", {})),
        queue_exchange=data.get("queue_exchange"),
    )


def resolve_runtime_queue_names(queue_names: dict[str, str] | None) -> dict[str, str]:
    """Normalize queue names to the canonical PAA queue keys."""

    resolved = dict(DEFAULT_RUNTIME_QUEUE_NAMES)
    source = dict(queue_names or {})
    for target_key, aliases in _QUEUE_NAME_KEY_ALIASES.items():
        for alias in aliases:
            candidate = source.get(alias)
            if candidate:
                resolved[target_key] = str(candidate)
                break
    return resolved


def normalize_runtime_queue_topology(topology: RuntimeQueueTopology | None) -> RuntimeQueueTopology:
    """Return a topology with canonical queue keys and PAA defaults applied."""

    return RuntimeQueueTopology(
        path=topology.path if topology is not None else None,
        queue_names=resolve_runtime_queue_names(topology.queue_names if topology is not None else None),
        queue_exchange=(
            topology.queue_exchange
            if topology is not None and topology.queue_exchange
            else DEFAULT_RUNTIME_QUEUE_EXCHANGE
        ),
    )


def runtime_queue_name_by_key(
    key: str,
    *,
    topology: RuntimeQueueTopology | None = None,
) -> str | None:
    """Resolve a canonical queue key to a concrete queue name."""

    normalized = normalize_runtime_queue_topology(topology)
    return normalized.queue_names.get(key)


def runtime_queue_name_for_role(
    role_name: str | None,
    *,
    topology: RuntimeQueueTopology | None = None,
) -> str | None:
    """Resolve a runtime role to its configured queue."""

    if not role_name:
        return None
    queue_key = _ROLE_TO_QUEUE_KEY.get(role_name)
    if queue_key is None:
        return None
    return runtime_queue_name_by_key(queue_key, topology=topology)


ConsumerProjectConfig = RuntimeProjectConfig
ProducerConsumerProjectConfig = UnifiedRuntimeProjectConfig
load_consumer_project_config = load_runtime_project_config
load_producer_consumer_project_config = load_unified_runtime_project_config


def runtime_queue_name_for_schema(
    schema_type: str | None,
    *,
    topology: RuntimeQueueTopology | None = None,
) -> str | None:
    """Resolve a packet schema family to its configured queue."""

    if not schema_type:
        return None
    queue_key = _SCHEMA_TO_QUEUE_KEY.get(schema_type)
    if queue_key is None:
        return None
    return runtime_queue_name_by_key(queue_key, topology=topology)
