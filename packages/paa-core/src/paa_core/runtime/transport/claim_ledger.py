"""File-backed queue claim ledger for the PAA runtime."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Optional

STATE_ENV_VAR = "FRACTAL_CORE_HANDOFF_STATE_DIR"


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: str | Path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: str | Path, data):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def get_git_root() -> Optional[Path]:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return None
    path = result.stdout.strip()
    return Path(path) if path else None


def state_root_candidates() -> list[tuple[Path, str]]:
    explicit = os.environ.get(STATE_ENV_VAR)
    if explicit:
        return [(Path(explicit).expanduser(), f"env:{STATE_ENV_VAR}")]

    candidates: list[tuple[Path, str]] = []
    home_root = Path.home() / ".codex/state/fractal-core-handoff"
    repo_root = get_git_root() or Path.cwd()
    runtime_root = repo_root / ".project/data/paa/queue-state/fractal-core-handoff"
    candidates.append((runtime_root, "repo-runtime"))
    candidates.append((home_root, "home"))

    git_root = get_git_root()
    if git_root:
        candidates.append((git_root / ".codex-state/fractal-core-handoff", "git-root"))

    cwd_root = Path.cwd() / ".codex-state/fractal-core-handoff"
    if all(cwd_root != path for path, _ in candidates):
        candidates.append((cwd_root, "cwd"))

    return candidates


def unique_state_root_candidates() -> list[tuple[Path, str]]:
    seen: set[Path] = set()
    ordered: list[tuple[Path, str]] = []
    for path, source in state_root_candidates():
        resolved = path.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append((resolved, source))
    return ordered


def path_is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".writable-{uuid.uuid4().hex}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except Exception:
        return False


def resolve_active_state_root() -> tuple[Path, str, list[dict[str, object]]]:
    candidates = unique_state_root_candidates()
    candidate_info = []
    explicit = bool(os.environ.get(STATE_ENV_VAR))
    for path, source in candidates:
        writable = path_is_writable_dir(path)
        candidate_info.append({"path": str(path), "source": source, "writable": writable})
        if writable:
            return path, source, candidate_info
    if explicit:
        raise RuntimeError(
            f"Configured state dir via {STATE_ENV_VAR} is not writable: {candidates[0][0]}"
        )
    raise RuntimeError(
        "No writable claim-ledger state directory found. Candidates: "
        + ", ".join(f"{info['source']}={info['path']} writable={info['writable']}" for info in candidate_info)
    )


def claims_dir(root: Path) -> Path:
    return root / "claims"


def ensure_state_dirs() -> tuple[Path, str, list[dict[str, object]]]:
    root, source, candidate_info = resolve_active_state_root()
    claims_dir(root).mkdir(parents=True, exist_ok=True)
    return root, source, candidate_info


def claim_path(claim_id: str, root: Optional[Path] = None) -> Path:
    if root is None:
        root, _, _ = ensure_state_dirs()
    return claims_dir(root) / f"{claim_id}.json"


def all_existing_claim_dirs() -> list[Path]:
    dirs: list[Path] = []
    seen: set[Path] = set()
    for root, _ in unique_state_root_candidates():
        cdir = claims_dir(root)
        if cdir.exists() and cdir not in seen:
            seen.add(cdir)
            dirs.append(cdir)
    return dirs


class FileQueueClaimLedgerRepository:
    def __init__(self, *, root: Path | None = None) -> None:
        if root is None:
            resolved_root, source, candidate_info = ensure_state_dirs()
        else:
            resolved_root = root
            source = 'explicit-root'
            candidate_info = [{'path': str(root), 'source': source, 'writable': True}]
            claims_dir(root).mkdir(parents=True, exist_ok=True)
        self.root = resolved_root
        self.source = source
        self.candidate_info = candidate_info

    def record_claim(self, claim_record: dict[str, object]) -> dict[str, object]:
        claim_id = str(uuid.uuid4())
        record = {
            'claim_id': claim_id,
            **claim_record,
            'state_dir': str(self.root),
            'state_dir_source': self.source,
        }
        save_json(claim_path(claim_id, self.root), record)
        return record

    def load_claim(self, claim_id: str) -> tuple[Path, dict]:
        for cdir in all_existing_claim_dirs():
            path = cdir / f"{claim_id}.json"
            if path.exists():
                return path, load_json(path)
        raise RuntimeError(f"claim not found: {claim_id}")

    def list_claims(self, *, queue: str | None = None, status: str | None = None) -> list[dict]:
        claims = []
        for cdir in all_existing_claim_dirs():
            for path in sorted(cdir.glob("*.json")):
                try:
                    data = load_json(path)
                except Exception:
                    continue
                if queue and data.get("queue") != queue:
                    continue
                if status and data.get("status") != status:
                    continue
                data.setdefault("state_dir", str(cdir.parent))
                claims.append(data)
        return claims

    def update_claim(self, path: Path, claim: dict) -> None:
        save_json(path, claim)


__all__ = [
    'FileQueueClaimLedgerRepository',
    'STATE_ENV_VAR',
    'all_existing_claim_dirs',
    'claim_path',
    'claims_dir',
    'ensure_state_dirs',
    'get_git_root',
    'load_json',
    'path_is_writable_dir',
    'resolve_active_state_root',
    'save_json',
    'state_root_candidates',
    'unique_state_root_candidates',
    'utc_now',
]
