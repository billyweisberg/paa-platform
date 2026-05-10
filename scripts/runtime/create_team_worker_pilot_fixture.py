#!/usr/bin/env python3
"""Create a disposable Team Worker pilot fixture backed by GitHub and PAA DB state."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from paa_core.db import run_psql, sql_literal
from paa_producer.issue_loader import (
    IssueArtifactBundle,
    _brief_insert_sql,
    _design_package_insert_sql,
    _materialize_obligations_for_bundle,
    _sequence_insert_sql,
    _work_item_insert_sql,
)


def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"command failed: {cmd}")
    return result.stdout.strip()


def run_json(cmd: list[str], *, cwd: Path | None = None) -> dict:
    return json.loads(run(cmd, cwd=cwd))


def repo_default_branch(repo_root: Path) -> str:
    return run(["git", "rev-parse", "--abbrev-ref", "origin/HEAD"], cwd=repo_root).split("/")[-1]


def next_issue_title() -> str:
    return "[PAA][Pilot] Team Worker automation runtime state note"


def next_issue_body() -> str:
    return (
        "## Purpose\n\n"
        "Create a disposable but realistic Team Worker pilot slice for PAA-backed Codex automation validation.\n\n"
        "## Authorized outcome\n\n"
        "Author or refine `docs/paa-team-worker-automation-pilot.md` so it explains:\n"
        "- no-work polling\n"
        "- claimable work detection\n"
        "- stale assignment handling\n"
        "- active role execution handoff\n\n"
        "## Constraints\n\n"
        "- docs-only slice\n"
        "- no runtime behavior changes\n"
        "- keep the change narrow and easy for QA to verify\n\n"
        "## Note\n\n"
        "This issue is a disposable supervised pilot fixture for PAA automation validation.\n"
    )


def create_issue(repo_root: Path) -> dict:
    url = run(
        [
            "gh",
            "issue",
            "create",
            "--repo",
            "billyweisberg/fractal-core-python",
            "--title",
            next_issue_title(),
            "--body",
            next_issue_body(),
        ],
        cwd=repo_root,
    )
    issue = run_json(
        ["gh", "issue", "view", url, "--repo", "billyweisberg/fractal-core-python", "--json", "number,title,url,state"],
        cwd=repo_root,
    )
    return issue


def seed_pr(repo_root: Path, issue_number: int, *, fixture_root: Path) -> dict:
    branch = f"issue-{issue_number}"
    base = repo_default_branch(repo_root)
    worktree = fixture_root / "canonical-worktree"
    doc_rel = Path("docs/paa-team-worker-automation-pilot.md")
    if worktree.exists():
        shutil.rmtree(worktree)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "worktree", "add", "-b", branch, str(worktree), f"origin/{base}"], cwd=repo_root)
    try:
        doc_path = worktree / doc_rel
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(
            "# PAA Team Worker Automation Pilot\n\n"
            "This draft note is a seeded fixture for a supervised Team Worker automation pilot.\n\n"
            "Expected follow-up from Docs Dev:\n"
            "- explain no-work polling\n"
            "- explain claimable work detection\n"
            "- explain stale assignment handling\n"
            "- explain active role execution handoff\n"
        )
        run(["git", "add", str(doc_rel)], cwd=worktree)
        run(["git", "commit", "-m", f"Seed Team Worker pilot fixture for issue {issue_number}"], cwd=worktree)
        run(["git", "push", "-u", "origin", branch], cwd=worktree)
        pr_url = run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                "billyweisberg/fractal-core-python",
                "--draft",
                "--base",
                base,
                "--head",
                branch,
                "--title",
                f"[PAA Pilot] Team Worker automation runtime state note (issue #{issue_number})",
                "--body",
                (
                    f"Closes #{issue_number}\n\n"
                    "This draft PR seeds a disposable Team Worker automation pilot fixture.\n"
                    "Docs Dev is expected to replace the placeholder note with the real pilot content.\n"
                ),
            ],
            cwd=worktree,
        )
        pr = run_json(
            ["gh", "pr", "view", pr_url, "--repo", "billyweisberg/fractal-core-python", "--json", "number,title,url,state,isDraft,headRefName,baseRefName"],
            cwd=worktree,
        )
    finally:
        run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo_root)
    return {
        "branch": branch,
        "base_branch": base,
        "doc_rel_path": str(doc_rel),
        "pr": pr,
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def build_fixture_artifacts(
    *,
    consumer_repo_root: Path,
    fixture_root: Path,
    issue_number: int,
    pr_number: int,
    branch: str,
    doc_rel_path: str,
) -> IssueArtifactBundle:
    artifacts_root = consumer_repo_root / ".project" / "data" / "paa" / "authority" / "current" / "artifacts"
    base_package = load_json(artifacts_root / "stage1_design_package.issue106.retirement_boundary_diagnostics.json")
    base_brief = load_json(artifacts_root / "coder_run_brief.issue106.retirement-boundary-diagnostics.json")

    package_id = f"fcore-stagew7-2026-05-10-issue{issue_number}-team-worker-automation-runtime-note"
    brief_id = f"fcore-coder-2026-05-10-issue{issue_number}-team-worker-automation-runtime-note"
    task_id = "py-pilot-team-worker-automation-runtime-note"
    title = "Author a Team Worker automation runtime state note"
    slice_name = "team worker automation runtime state note"
    delta_family = "paa-team-worker-automation-runtime-note"

    package = json.loads(json.dumps(base_package))
    package["package_id"] = package_id
    package["authority_context"]["task_id"] = task_id
    package["authority_context"]["task_title"] = title
    package["authority_context"]["issue_number"] = issue_number
    package["product_and_source_basis"]["product_outcome_statement"] = (
        "Publish a small documentation note that explains Team Worker automation runtime states "
        "so the Codex app launcher boundary is easier to reason about."
    )
    package["product_and_source_basis"]["roadmap_context"] = [
        "This is a disposable authority-backed pilot slice for PAA automation validation.",
        "The pilot targets a docs-only Team Worker lane so the end-to-end loop can be exercised safely.",
    ]
    package["requirement_set"]["requirements"] = [
        "Document no-work polling for Team Worker automations.",
        "Document claimable-work detection at the app launch boundary.",
        "Document stale-assignment handling versus active execution handling.",
        "Keep the slice docs-only and safe for QA review.",
    ]
    package["design_decision_set"]["design_decisions"] = [
        "Use Docs Dev as the first non-Python Team Worker live pilot role.",
        "Keep the pilot docs-only so the work remains narrow and easy to verify.",
        "Anchor the note in the consumer repo so the output is visible where the pilot actually runs.",
    ]
    package["spec_fragment"]["spec_fragment_id"] = f"spec-{delta_family}-issue{issue_number}"
    package["spec_fragment"]["spec_fragment_title"] = "Team Worker automation runtime state note"
    package["spec_fragment"]["canonical_statement"] = (
        "The system should support a small, docs-only Team Worker pilot slice that explains "
        "automation runtime states without changing runtime behavior."
    )
    package["spec_fragment"]["authorized_delta_family"] = delta_family
    package["implementation_target"]["implementation_target_id"] = f"impl-{delta_family}-issue{issue_number}"
    package["implementation_target"]["current_gap"] = [
        "The app-launch boundary has now been exercised, but the runtime-state explanation is not captured in a single lightweight doc note.",
        "Future pilot users should not need to reconstruct no-work, stale-assignment, and active-work behavior from scattered notes.",
    ]
    package["implementation_target"]["desired_state"] = [
        "A small note in the consumer repo explains the main Team Worker automation runtime states.",
        "The note is safe to review through the Team Worker docs lane and does not change runtime behavior.",
    ]
    package["implementation_target"]["expected_touch_surfaces"] = [doc_rel_path]
    package["implementation_target"]["out_of_scope_items"] = [
        "runtime behavior changes",
        "automation launcher redesign",
        "queue topology changes",
        "non-docs code changes",
    ]
    package["architectural_authority_constraints"]["target_module_boundaries"] = [
        "Touch the pilot note only.",
        "Do not broaden into runtime or queue behavior changes.",
        "Do not change Team Worker routing or worktree logic in this slice.",
    ]
    package["component_model_slice"]["primary_component"] = "RetirementBoundaryDiagnostics"

    brief = json.loads(json.dumps(base_brief))
    brief["brief_id"] = brief_id
    brief["authority_context"]["task_id"] = task_id
    brief["authority_context"]["issue_number"] = issue_number
    brief["authority_context"]["pr_number"] = pr_number
    brief["slice_scope_ref"]["slice_name"] = slice_name
    brief["slice_scope_ref"]["authorized_delta_family"] = delta_family
    brief["component_assignment"]["component_name"] = "RetirementBoundaryDiagnostics"
    brief["component_assignment"]["component_role"] = "docs note describing Team Worker automation runtime states"
    brief["component_assignment"]["system_layer"] = "documentation"
    brief["component_assignment"]["tier"] = "docs"
    brief["component_assignment"]["component_aspects"] = ["docs"]
    brief["component_assignment"]["target_modules"] = [doc_rel_path]
    brief["architecture_constraints"]["allowed_edit_surfaces"] = [doc_rel_path]
    brief["architecture_constraints"]["forbidden_edit_surfaces"] = [
        "runtime code",
        "queue runtime code",
        "automation launcher code",
        "unrelated docs",
    ]
    brief["behavioral_contract"]["behavior_to_add_or_change"] = [
        "Document no-work polling for Team Worker automations.",
        "Document claimable-work detection and stale-assignment handling.",
        "Keep the note narrowly scoped to app-launched Team Worker runtime states.",
    ]
    brief["test_contract"]["tests_to_run"] = [
        f"test -f {doc_rel_path}",
        f"git diff -- {doc_rel_path}",
    ]
    brief["test_contract"]["tests_to_add_or_update"] = []
    brief["test_contract"]["artifacts_expected"] = ["docs note"]
    brief["change_budget"]["expected_touch_surfaces"] = [doc_rel_path]
    brief["change_budget"]["max_responsibility_expansion"] = (
        "This pilot slice may create or refine the Team Worker automation runtime note only."
    )
    brief["anti_goals"]["anti_goals"] = [
        "Do not change runtime behavior during the pilot docs slice.",
        "Do not broaden into queue, worktree, or Codex launcher redesign work.",
    ]

    package_path = fixture_root / "artifacts" / f"stage1_design_package.issue{issue_number}.team_worker_automation_runtime_note.json"
    brief_path = fixture_root / "artifacts" / f"coder_run_brief.issue{issue_number}.team-worker-automation-runtime-note.json"
    write_json(package_path, package)
    write_json(brief_path, brief)

    manifest_task = {
        "task_id": task_id,
        "issue_number": issue_number,
        "task_title": title,
        "status": "queued",
        "merge_policy": "qa_required",
        "requires_qa": True,
    }
    return IssueArtifactBundle(
        issue_number=issue_number,
        package_path=package_path,
        package_json=package,
        brief_paths=[brief_path],
        brief_jsons=[brief],
        manifest_task=manifest_task,
    )


def insert_fixture_bundle(bundle: IssueArtifactBundle, *, repo_root: Path) -> None:
    statements = [
        _work_item_insert_sql(bundle),
        _design_package_insert_sql(bundle),
        *(_brief_insert_sql(bundle, path, brief) for path, brief in zip(bundle.brief_paths, bundle.brief_jsons)),
        *(_sequence_insert_sql(bundle, brief) for brief in bundle.brief_jsons),
    ]
    run_psql("BEGIN;\n" + "\n\n".join(statements) + "\nCOMMIT;\n")
    _materialize_obligations_for_bundle(repo_root=repo_root, bundle=bundle)


def create_fixture(args) -> dict:
    consumer_repo = Path(args.consumer_repo).resolve()
    producer_repo = Path(args.producer_repo).resolve()
    issue = create_issue(consumer_repo)
    issue_number = int(issue["number"])
    fixture_root = consumer_repo / ".codex-work" / "pilot-fixtures" / f"issue-{issue_number}"
    fixture_root.mkdir(parents=True, exist_ok=True)
    branch_info = seed_pr(consumer_repo, issue_number, fixture_root=fixture_root)
    pr_number = int(branch_info["pr"]["number"])
    bundle = build_fixture_artifacts(
        consumer_repo_root=consumer_repo,
        fixture_root=fixture_root,
        issue_number=issue_number,
        pr_number=pr_number,
        branch=branch_info["branch"],
        doc_rel_path=branch_info["doc_rel_path"],
    )
    insert_fixture_bundle(bundle, repo_root=producer_repo)
    result = {
        "ok": True,
        "issue": issue,
        "pr": branch_info["pr"],
        "canonical_branch": branch_info["branch"],
        "doc_rel_path": branch_info["doc_rel_path"],
        "fixture_root": str(fixture_root),
        "package_id_external": bundle.package_json["package_id"],
        "brief_id_external": bundle.brief_jsons[0]["brief_id"],
        "task_id": bundle.package_json["authority_context"]["task_id"],
    }
    (fixture_root / "fixture-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--consumer-repo", required=True)
    parser.add_argument("--producer-repo", required=True)
    args = parser.parse_args()
    print(json.dumps(create_fixture(args), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
