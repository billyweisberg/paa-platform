"""Team Worker Role registry loading and lookup helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from paa_core.runtime_paths import repo_paa_root, repo_root_from_cwd


DEFAULT_TEAM_WORKER_ROLES: dict[str, Any] = {
    "version": "2026-05-09",
    "queue_bindings": {
        "implementation": "fractal-core-python",
    },
    "worker_roles": [
        {
            "key": "python-team",
            "display_name": "Python Dev",
            "family": "implementation",
            "branch_suffix": "dev",
            "queue_binding": "implementation",
            "automation_id": "python-team-automation",
            "skill_id": "fractal-core-dev-result",
            "result_packet_family": "worker_result_packet",
            "active": True,
        },
        {
            "key": "frontend-dev",
            "display_name": "Frontend Dev",
            "family": "implementation",
            "branch_suffix": "frontend",
            "queue_binding": "implementation",
            "automation_id": "frontend-dev-automation",
            "skill_id": "fractal-core-dev-result",
            "result_packet_family": "worker_result_packet",
            "active": True,
        },
        {
            "key": "backend-dev",
            "display_name": "Backend Dev",
            "family": "implementation",
            "branch_suffix": "backend",
            "queue_binding": "implementation",
            "automation_id": "backend-dev-automation",
            "skill_id": "fractal-core-dev-result",
            "result_packet_family": "worker_result_packet",
            "active": True,
        },
        {
            "key": "infra-dev",
            "display_name": "Infra Dev",
            "family": "infra",
            "branch_suffix": "infra",
            "queue_binding": "implementation",
            "automation_id": "infra-dev-automation",
            "skill_id": "fractal-core-dev-result",
            "result_packet_family": "worker_result_packet",
            "active": True,
        },
        {
            "key": "docs-dev",
            "display_name": "Docs Dev",
            "family": "docs",
            "branch_suffix": "docs",
            "queue_binding": "implementation",
            "automation_id": "docs-dev-automation",
            "skill_id": "fractal-core-dev-result",
            "result_packet_family": "worker_result_packet",
            "active": True,
        },
    ],
}


@dataclass(frozen=True)
class TeamWorkerRole:
    key: str
    display_name: str
    family: str
    branch_suffix: str
    queue_binding: str
    automation_id: str
    skill_id: str
    result_packet_family: str
    active: bool = True


@dataclass(frozen=True)
class TeamWorkerRolesConfig:
    path: Path | None
    version: str
    queue_bindings: dict[str, str]
    worker_roles: list[TeamWorkerRole]


def _default_registry_path(repo_root: Path) -> Path:
    return repo_paa_root(repo_root) / "team-worker-roles.json"


def _configured_registry_path(repo_root: Path) -> Path | None:
    config_path = repo_paa_root(repo_root) / "project-config.json"
    if not config_path.exists():
        return None
    try:
        data = json.loads(config_path.read_text())
    except Exception:
        return None
    configured = data.get("team_worker_roles_path")
    if not configured:
        return None
    return (repo_root / str(configured)).resolve()


def _load_registry_data(path: Path | None) -> tuple[Path | None, dict[str, Any]]:
    if path and path.exists():
        return path, json.loads(path.read_text())
    return None, DEFAULT_TEAM_WORKER_ROLES


def load_team_worker_roles(repo_root: Path | None = None, path: Path | None = None) -> TeamWorkerRolesConfig:
    resolved_repo_root = (repo_root or repo_root_from_cwd()).resolve()
    candidate = path
    if candidate is None:
        candidate = _configured_registry_path(resolved_repo_root)
    if candidate is None:
        candidate = _default_registry_path(resolved_repo_root)
    loaded_path, data = _load_registry_data(candidate)
    roles = [
        TeamWorkerRole(
            key=item["key"],
            display_name=item["display_name"],
            family=item["family"],
            branch_suffix=item["branch_suffix"],
            queue_binding=item["queue_binding"],
            automation_id=item["automation_id"],
            skill_id=item["skill_id"],
            result_packet_family=item.get("result_packet_family", "worker_result_packet"),
            active=bool(item.get("active", True)),
        )
        for item in data.get("worker_roles", [])
    ]
    return TeamWorkerRolesConfig(
        path=loaded_path,
        version=str(data.get("version", "unknown")),
        queue_bindings=dict(data.get("queue_bindings", {})),
        worker_roles=roles,
    )


def active_team_worker_roles(repo_root: Path | None = None, path: Path | None = None) -> list[TeamWorkerRole]:
    return [role for role in load_team_worker_roles(repo_root=repo_root, path=path).worker_roles if role.active]


def team_worker_role_by_key(key: str, repo_root: Path | None = None) -> TeamWorkerRole | None:
    for role in active_team_worker_roles(repo_root=repo_root):
        if role.key == key:
            return role
    return None


def team_worker_role_by_display_name(display_name: str, repo_root: Path | None = None) -> TeamWorkerRole | None:
    for role in active_team_worker_roles(repo_root=repo_root):
        if role.display_name == display_name:
            return role
    return None


def team_worker_role_keys(repo_root: Path | None = None) -> list[str]:
    return [role.key for role in active_team_worker_roles(repo_root=repo_root)]


def team_worker_role_display_names(repo_root: Path | None = None) -> list[str]:
    return [role.display_name for role in active_team_worker_roles(repo_root=repo_root)]


def team_worker_branch_suffix_map(repo_root: Path | None = None) -> dict[str, str]:
    return {role.key: role.branch_suffix for role in active_team_worker_roles(repo_root=repo_root)}


def team_worker_cli_to_display_map(repo_root: Path | None = None) -> dict[str, str]:
    return {role.key: role.display_name for role in active_team_worker_roles(repo_root=repo_root)}


def team_worker_display_to_cli_map(repo_root: Path | None = None) -> dict[str, str]:
    return {role.display_name: role.key for role in active_team_worker_roles(repo_root=repo_root)}


def team_worker_result_route_pairs(repo_root: Path | None = None) -> set[tuple[str, str]]:
    return {(role.display_name, "TechLead") for role in active_team_worker_roles(repo_root=repo_root)}


def techlead_assignment_route_pairs(repo_root: Path | None = None) -> set[tuple[str, str]]:
    pairs = {("TechLead", "Delivery Architect"), ("TechLead", "QA")}
    pairs.update({("TechLead", role.display_name) for role in active_team_worker_roles(repo_root=repo_root)})
    return pairs


def team_worker_queue_name_by_key(key: str, repo_root: Path | None = None) -> str | None:
    config = load_team_worker_roles(repo_root=repo_root)
    role = next((item for item in config.worker_roles if item.key == key and item.active), None)
    if role is None:
        return None
    return config.queue_bindings.get(role.queue_binding)


def team_worker_queue_name_by_display_name(display_name: str, repo_root: Path | None = None) -> str | None:
    config = load_team_worker_roles(repo_root=repo_root)
    role = next((item for item in config.worker_roles if item.display_name == display_name and item.active), None)
    if role is None:
        return None
    return config.queue_bindings.get(role.queue_binding)
