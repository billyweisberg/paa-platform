#!/usr/bin/env python3
"""Install or remove a pilot-only authority overlay for disposable fixtures."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
import sys


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def authority_install_root(repo_root: Path) -> Path:
    return repo_root / ".project" / "data" / "paa" / "authority" / "current"


def overlay_root(repo_root: Path, issue_number: int) -> Path:
    return authority_install_root(repo_root) / "overlays" / "pilot-fixtures" / f"issue-{issue_number}"


def fixture_root(repo_root: Path, issue_number: int) -> Path:
    return repo_root / ".codex-work" / "pilot-fixtures" / f"issue-{issue_number}"


def summary_path(repo_root: Path, issue_number: int) -> Path:
    return fixture_root(repo_root, issue_number) / "fixture-summary.json"


def current_manifest_path(repo_root: Path) -> Path:
    return authority_install_root(repo_root) / "authority" / "fractal-core-python-authority.json"


def current_metadata_path(repo_root: Path) -> Path:
    return authority_install_root(repo_root) / "package-metadata.json"


def current_artifacts_root(repo_root: Path) -> Path:
    return authority_install_root(repo_root) / "artifacts"


def build_overlay_task(summary: dict, package: dict, brief: dict, *, package_path: Path, brief_path: Path) -> dict:
    authority_context = package.get("authority_context") or {}
    implementation_target = package.get("implementation_target") or {}
    product_basis = package.get("product_and_source_basis") or {}
    requirement_set = package.get("requirement_set") or {}
    references = [
        summary["issue"]["url"],
        summary["pr"]["url"],
        summary["doc_rel_path"],
        f"artifacts/{package_path.name}",
        f"artifacts/{brief_path.name}",
    ]
    return {
        "task_id": summary["task_id"],
        "issue_number": summary["issue"]["number"],
        "phase_id": "p9-team-worker-automation-pilot",
        "milestone_id": "m9-team-worker-automation-pilot",
        "title": authority_context.get("task_title") or "Author a Team Worker automation runtime state note",
        "status": "queued",
        "merge_policy": "qa_required",
        "requires_qa": True,
        "allowed_successors": [],
        "protected_contracts": ["automation-pilot", "authority-overlay"],
        "source_authorities": references,
        "dependencies": [],
        "authoring": {
            "objective": (
                product_basis.get("product_outcome_statement")
                or "Publish the authorized Team Worker automation pilot note."
            ),
            "background": product_basis.get("roadmap_context")
            or [
                "This is a disposable supervised pilot slice.",
                "The installed current authority must explicitly authorize pilot work before Team Worker automations act.",
            ],
            "current_gap": implementation_target.get("current_gap")
            or [
                "The pilot note is not yet authored.",
                "Without an authority-backed pilot slice, Team Worker automation behavior cannot be validated end to end on a fresh task.",
            ],
            "acceptance_criteria": requirement_set.get("requirements")
            or brief.get("behavioral_contract", {}).get("behavior_to_add_or_change")
            or ["Produce the authorized Team Worker automation runtime note."],
            "validation_commands": brief.get("test_contract", {}).get("tests_to_run")
            or ["test -f docs/paa-team-worker-automation-pilot.md"],
            "out_of_scope": implementation_target.get("out_of_scope_items")
            or brief.get("anti_goals", {}).get("anti_goals")
            or ["Do not broaden beyond the pilot note."],
            "references": references,
        },
        "design_package_id_external": summary["package_id_external"],
        "coder_brief_id_external": summary["brief_id_external"],
    }


def normalize_overlay_artifacts(summary: dict, package: dict, brief: dict, *, authority_version: str) -> tuple[dict, dict]:
    phase_id = "p9-team-worker-automation-pilot"
    milestone_id = "m9-team-worker-automation-pilot"
    task_id = summary["task_id"]
    task_title = "Author a Team Worker automation runtime state note"
    issue_number = int(summary["issue"]["number"])
    pr_number = int(summary["pr"]["number"])

    package = json.loads(json.dumps(package))
    brief = json.loads(json.dumps(brief))

    package_authority = package.setdefault("authority_context", {})
    package_authority.update(
        {
            "authority_version": authority_version,
            "milestone_id": milestone_id,
            "phase_id": phase_id,
            "task_id": task_id,
            "task_title": task_title,
            "issue_number": issue_number,
            "allowed_successors": [],
            "predecessor_tasks": [],
        }
    )

    brief_authority = brief.setdefault("authority_context", {})
    brief_authority.update(
        {
            "authority_version": authority_version,
            "milestone_id": milestone_id,
            "phase_id": phase_id,
            "task_id": task_id,
            "issue_number": issue_number,
            "pr_number": pr_number,
        }
    )
    return package, brief


def install_overlay(repo_root: Path, issue_number: int) -> dict:
    summary = load_json(summary_path(repo_root, issue_number))
    fixture = fixture_root(repo_root, issue_number)
    package_path = fixture / "artifacts" / f"stage1_design_package.issue{issue_number}.team_worker_automation_runtime_note.json"
    brief_path = fixture / "artifacts" / f"coder_run_brief.issue{issue_number}.team-worker-automation-runtime-note.json"
    package = load_json(package_path)
    brief = load_json(brief_path)

    manifest_file = current_manifest_path(repo_root)
    metadata_file = current_metadata_path(repo_root)
    manifest = load_json(manifest_file)
    metadata = load_json(metadata_file)
    authority_version = str((manifest.get("project") or {}).get("authority_version") or "pilot-overlay")
    package, brief = normalize_overlay_artifacts(summary, package, brief, authority_version=authority_version)
    write_json(package_path, package)
    write_json(brief_path, brief)
    task = build_overlay_task(summary, package, brief, package_path=package_path, brief_path=brief_path)

    artifacts_root = current_artifacts_root(repo_root)
    overlay_dir = overlay_root(repo_root, issue_number)
    if overlay_dir.exists():
        shutil.rmtree(overlay_dir)
    overlay_dir.mkdir(parents=True, exist_ok=True)

    copied_artifacts: list[str] = []
    for src in [package_path, brief_path]:
        dst = artifacts_root / src.name
        shutil.copy2(src, dst)
        shutil.copy2(src, overlay_dir / src.name)
        copied_artifacts.append(str(dst))

    manifest["tasks"] = [
        existing
        for existing in manifest.get("tasks", [])
        if existing.get("task_id") != task["task_id"] and existing.get("issue_number") != issue_number
    ]
    manifest["tasks"].append(task)
    manifest["tasks"].sort(key=lambda item: (item.get("issue_number") or 0, str(item.get("task_id") or "")))
    write_json(manifest_file, manifest)

    overlays = metadata.setdefault("pilot_overlays", [])
    if not isinstance(overlays, list):
        overlays = []
        metadata["pilot_overlays"] = overlays
    overlays = [
        entry
        for entry in overlays
        if entry.get("issue_number") != issue_number and entry.get("task_id") != task["task_id"]
    ]
    overlay_metadata = {
        "overlay_type": "pilot_fixture",
        "installed_at": utc_now(),
        "issue_number": issue_number,
        "task_id": task["task_id"],
        "package_id_external": summary["package_id_external"],
        "brief_id_external": summary["brief_id_external"],
        "issue_url": summary["issue"]["url"],
        "pr_url": summary["pr"]["url"],
        "copied_artifacts": copied_artifacts,
        "overlay_root": str(overlay_dir),
    }
    overlays.append(overlay_metadata)
    metadata["pilot_overlays"] = overlays
    included_artifacts = metadata.setdefault("included_artifacts", [])
    if isinstance(included_artifacts, list):
        for artifact_path in [f"artifacts/{package_path.name}", f"artifacts/{brief_path.name}"]:
            if artifact_path not in included_artifacts:
                included_artifacts.append(artifact_path)
    write_json(metadata_file, metadata)

    summary["overlay_installed"] = True
    summary["overlay_root"] = str(overlay_dir)
    summary["package_artifact"] = str(package_path)
    summary["brief_artifact"] = str(brief_path)
    write_json(summary_path(repo_root, issue_number), summary)
    write_json(overlay_dir / "overlay-metadata.json", overlay_metadata)
    write_json(overlay_dir / "manifest-task.json", task)

    return {
        "ok": True,
        "action": "install",
        "repo_root": str(repo_root),
        "issue_number": issue_number,
        "task_id": task["task_id"],
        "overlay_root": str(overlay_dir),
        "copied_artifacts": copied_artifacts,
    }


def remove_overlay(repo_root: Path, issue_number: int) -> dict:
    manifest_file = current_manifest_path(repo_root)
    metadata_file = current_metadata_path(repo_root)
    manifest = load_json(manifest_file)
    metadata = load_json(metadata_file)
    overlay_dir = overlay_root(repo_root, issue_number)
    overlay_metadata_file = overlay_dir / "overlay-metadata.json"
    overlay_metadata = load_json(overlay_metadata_file) if overlay_metadata_file.exists() else {}
    task_id = overlay_metadata.get("task_id")

    manifest["tasks"] = [
        task
        for task in manifest.get("tasks", [])
        if task.get("issue_number") != issue_number and (not task_id or task.get("task_id") != task_id)
    ]
    write_json(manifest_file, manifest)

    overlays = metadata.get("pilot_overlays", [])
    if isinstance(overlays, list):
        metadata["pilot_overlays"] = [
            entry
            for entry in overlays
            if entry.get("issue_number") != issue_number and (not task_id or entry.get("task_id") != task_id)
        ]

    for artifact_path in overlay_metadata.get("copied_artifacts", []):
        path = Path(artifact_path)
        if path.exists():
            path.unlink()

    if overlay_dir.exists():
        shutil.rmtree(overlay_dir)
    write_json(metadata_file, metadata)

    return {
        "ok": True,
        "action": "remove",
        "repo_root": str(repo_root),
        "issue_number": issue_number,
        "task_id": task_id,
    }


def status_overlay(repo_root: Path, issue_number: int) -> dict:
    manifest = load_json(current_manifest_path(repo_root))
    metadata = load_json(current_metadata_path(repo_root))
    task = next((task for task in manifest.get("tasks", []) if task.get("issue_number") == issue_number), None)
    overlays = metadata.get("pilot_overlays", [])
    overlay_metadata = next((entry for entry in overlays if entry.get("issue_number") == issue_number), None) if isinstance(overlays, list) else None
    return {
        "ok": True,
        "repo_root": str(repo_root),
        "issue_number": issue_number,
        "installed": task is not None,
        "task": task,
        "overlay_metadata": overlay_metadata,
        "overlay_root": str(overlay_root(repo_root, issue_number)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Consumer repo root")
    parser.add_argument("--issue-number", required=True, type=int)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install")
    sub.add_parser("remove")
    sub.add_parser("status")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()
    if args.command == "install":
        result = install_overlay(repo_root, args.issue_number)
    elif args.command == "remove":
        result = remove_overlay(repo_root, args.issue_number)
    else:
        result = status_overlay(repo_root, args.issue_number)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
