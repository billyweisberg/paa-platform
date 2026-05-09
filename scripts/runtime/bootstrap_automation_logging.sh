#!/bin/sh
set -eu

usage() {
  cat <<'USAGE' >&2
Usage:
  bootstrap_automation_logging.sh \
    --repo-root <path> \
    --automation-id <id> \
    --role-key <key> \
    [--role-display-name <name>] \
    [--phase <phase>] \
    [--issue-number <n>] \
    [--package-id-external <id>] \
    [--brief-id-external <id>] \
    [--worktree-path <path>] \
    [--log-level <level>] \
    [--log-format <format>]
USAGE
  exit 2
}

REPO_ROOT=""
AUTOMATION_ID=""
ROLE_KEY=""
ROLE_DISPLAY_NAME=""
PHASE="launch"
ISSUE_NUMBER=""
PACKAGE_ID_EXTERNAL=""
BRIEF_ID_EXTERNAL=""
WORKTREE_PATH=""
LOG_LEVEL="INFO"
LOG_FORMAT="jsonl"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"; shift 2 ;;
    --automation-id)
      AUTOMATION_ID="$2"; shift 2 ;;
    --role-key)
      ROLE_KEY="$2"; shift 2 ;;
    --role-display-name)
      ROLE_DISPLAY_NAME="$2"; shift 2 ;;
    --phase)
      PHASE="$2"; shift 2 ;;
    --issue-number)
      ISSUE_NUMBER="$2"; shift 2 ;;
    --package-id-external)
      PACKAGE_ID_EXTERNAL="$2"; shift 2 ;;
    --brief-id-external)
      BRIEF_ID_EXTERNAL="$2"; shift 2 ;;
    --worktree-path)
      WORKTREE_PATH="$2"; shift 2 ;;
    --log-level)
      LOG_LEVEL="$2"; shift 2 ;;
    --log-format)
      LOG_FORMAT="$2"; shift 2 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage ;;
  esac
done

[ -n "$REPO_ROOT" ] || usage
[ -n "$AUTOMATION_ID" ] || usage
[ -n "$ROLE_KEY" ] || usage

REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
LOG_ROOT="$REPO_ROOT/.project/data/paa/logs/automations"
RUN_ID="$(date -u +%Y-%m-%dT%H-%M-%SZ)-$$"
RUN_DIR="$LOG_ROOT/$AUTOMATION_ID/$RUN_ID"
EVENTS_FILE="$RUN_DIR/events.jsonl"
STDOUT_LOG="$RUN_DIR/stdout.log"
STDERR_LOG="$RUN_DIR/stderr.log"
SUMMARY_FILE="$RUN_DIR/summary.json"
ENV_FILE="$RUN_DIR/env.sh"

mkdir -p "$RUN_DIR"
: > "$STDOUT_LOG"
: > "$STDERR_LOG"
: > "$EVENTS_FILE"

python3 - <<'PY' "$SUMMARY_FILE" "$RUN_ID" "$AUTOMATION_ID" "$ROLE_KEY" "$ROLE_DISPLAY_NAME" "$PHASE" "$REPO_ROOT" "$WORKTREE_PATH" "$ISSUE_NUMBER" "$PACKAGE_ID_EXTERNAL" "$BRIEF_ID_EXTERNAL" "$LOG_LEVEL" "$LOG_FORMAT"
import json, sys
from datetime import datetime, UTC
(
    summary_path,
    run_id,
    automation_id,
    role_key,
    role_display_name,
    phase,
    repo_root,
    worktree_path,
    issue_number,
    package_id_external,
    brief_id_external,
    log_level,
    log_format,
) = sys.argv[1:]
payload = {
    "run_id": run_id,
    "automation_id": automation_id,
    "role_key": role_key,
    "role_display_name": role_display_name or None,
    "phase": phase,
    "started_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "repo_root": repo_root,
    "worktree_path": worktree_path or None,
    "issue_number": issue_number or None,
    "package_id_external": package_id_external or None,
    "brief_id_external": brief_id_external or None,
    "log_level": log_level,
    "log_format": log_format,
    "status": "started",
}
with open(summary_path, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=2)
    fh.write("\n")
PY

python3 - <<'PY' "$EVENTS_FILE" "$RUN_ID" "$AUTOMATION_ID" "$ROLE_KEY" "$ROLE_DISPLAY_NAME" "$PHASE" "$REPO_ROOT"
import json, sys
from datetime import datetime, UTC
(events_file, run_id, automation_id, role_key, role_display_name, phase, repo_root) = sys.argv[1:]
event = {
    "ts": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "run_id": run_id,
    "automation_id": automation_id,
    "role_key": role_key,
    "role_display_name": role_display_name or None,
    "phase": phase,
    "event": "run_bootstrap",
    "status": "started",
    "repo_root": repo_root,
}
with open(events_file, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(event) + "\n")
PY

cat > "$ENV_FILE" <<ENVVARS
export PAA_AUTOMATION_LOG_ROOT='$LOG_ROOT'
export PAA_AUTOMATION_RUN_DIR='$RUN_DIR'
export PAA_AUTOMATION_RUN_ID='$RUN_ID'
export PAA_AUTOMATION_REPO_ROOT='$REPO_ROOT'
export PAA_AUTOMATION_AUTOMATION_ID='$AUTOMATION_ID'
export PAA_AUTOMATION_ROLE_KEY='$ROLE_KEY'
export PAA_AUTOMATION_ROLE_DISPLAY_NAME='$ROLE_DISPLAY_NAME'
export PAA_AUTOMATION_EVENTS_FILE='$EVENTS_FILE'
export PAA_AUTOMATION_STDOUT_LOG='$STDOUT_LOG'
export PAA_AUTOMATION_STDERR_LOG='$STDERR_LOG'
export PAA_AUTOMATION_SUMMARY_FILE='$SUMMARY_FILE'
export PAA_AUTOMATION_LOG_LEVEL='$LOG_LEVEL'
export PAA_AUTOMATION_LOG_FORMAT='$LOG_FORMAT'
ENVVARS

printf '%s\n' \
  "export PAA_AUTOMATION_LOG_ROOT='$LOG_ROOT'" \
  "export PAA_AUTOMATION_RUN_DIR='$RUN_DIR'" \
  "export PAA_AUTOMATION_RUN_ID='$RUN_ID'" \
  "export PAA_AUTOMATION_REPO_ROOT='$REPO_ROOT'" \
  "export PAA_AUTOMATION_AUTOMATION_ID='$AUTOMATION_ID'" \
  "export PAA_AUTOMATION_ROLE_KEY='$ROLE_KEY'" \
  "export PAA_AUTOMATION_ROLE_DISPLAY_NAME='$ROLE_DISPLAY_NAME'" \
  "export PAA_AUTOMATION_EVENTS_FILE='$EVENTS_FILE'" \
  "export PAA_AUTOMATION_STDOUT_LOG='$STDOUT_LOG'" \
  "export PAA_AUTOMATION_STDERR_LOG='$STDERR_LOG'" \
  "export PAA_AUTOMATION_SUMMARY_FILE='$SUMMARY_FILE'" \
  "export PAA_AUTOMATION_LOG_LEVEL='$LOG_LEVEL'" \
  "export PAA_AUTOMATION_LOG_FORMAT='$LOG_FORMAT'"
