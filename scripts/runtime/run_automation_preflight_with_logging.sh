#!/bin/sh
set -eu

usage() {
  cat <<'USAGE' >&2
Usage:
  run_automation_preflight_with_logging.sh \
    --repo-root <path> \
    --automation-id <id> \
    --role-key <key> \
    --role-display-name <name> \
    --target-role <role> \
    [--phase <phase>] \
    [--issue-number <n>] \
    [--package-id-external <id>] \
    [--brief-id-external <id>]
USAGE
  exit 2
}

REPO_ROOT=""
AUTOMATION_ID=""
ROLE_KEY=""
ROLE_DISPLAY_NAME=""
TARGET_ROLE=""
PHASE="preflight"
ISSUE_NUMBER=""
PACKAGE_ID_EXTERNAL=""
BRIEF_ID_EXTERNAL=""

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
    --target-role)
      TARGET_ROLE="$2"; shift 2 ;;
    --phase)
      PHASE="$2"; shift 2 ;;
    --issue-number)
      ISSUE_NUMBER="$2"; shift 2 ;;
    --package-id-external)
      PACKAGE_ID_EXTERNAL="$2"; shift 2 ;;
    --brief-id-external)
      BRIEF_ID_EXTERNAL="$2"; shift 2 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage ;;
  esac
done

[ -n "$REPO_ROOT" ] || usage
[ -n "$AUTOMATION_ID" ] || usage
[ -n "$ROLE_KEY" ] || usage
[ -n "$ROLE_DISPLAY_NAME" ] || usage
[ -n "$TARGET_ROLE" ] || usage

REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
RUNTIME_SCRIPTS="$REPO_ROOT/.codex/paa/scripts/runtime"
BOOTSTRAP="$RUNTIME_SCRIPTS/bootstrap_automation_logging.sh"
EVENT_HELPER="$RUNTIME_SCRIPTS/log_automation_event.py"
CONSUMER="$REPO_ROOT/.codex/paa/bin/paa-consumer"

set -- \
  --repo-root "$REPO_ROOT" \
  --automation-id "$AUTOMATION_ID" \
  --role-key "$ROLE_KEY" \
  --role-display-name "$ROLE_DISPLAY_NAME" \
  --phase "$PHASE"

if [ -n "$ISSUE_NUMBER" ]; then
  set -- "$@" --issue-number "$ISSUE_NUMBER"
fi
if [ -n "$PACKAGE_ID_EXTERNAL" ]; then
  set -- "$@" --package-id-external "$PACKAGE_ID_EXTERNAL"
fi
if [ -n "$BRIEF_ID_EXTERNAL" ]; then
  set -- "$@" --brief-id-external "$BRIEF_ID_EXTERNAL"
fi

EXPORTS="$($BOOTSTRAP "$@")"
# shellcheck disable=SC2086
# shellcheck disable=SC1090
eval "$EXPORTS"

PREFLIGHT_OUTPUT="$($CONSUMER automation-preflight --repo-root "$REPO_ROOT" --target-role "$TARGET_ROLE" 2>>"$PAA_AUTOMATION_STDERR_LOG")"
printf '%s\n' "$PREFLIGHT_OUTPUT" > "$PAA_AUTOMATION_RUN_DIR/preflight.json"
printf '%s\n' "$PREFLIGHT_OUTPUT" >> "$PAA_AUTOMATION_STDOUT_LOG"

PRETTY_MESSAGE="$(python3 - <<'PY' "$PAA_AUTOMATION_RUN_DIR/preflight.json"
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
should = payload.get('should_invoke_model')
reason = payload.get('gate_reason')
print(f"should_invoke_model={should}; gate_reason={reason}")
PY
)"
EXTRA_JSON="$(python3 - <<'PY' "$PAA_AUTOMATION_RUN_DIR/preflight.json"
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
print(json.dumps({
    'should_invoke_model': payload.get('should_invoke_model'),
    'skip_model_invocation': payload.get('skip_model_invocation'),
    'gate_reason': payload.get('gate_reason'),
    'workflow_stage': payload.get('workflow_stage'),
    'current_owner_role': payload.get('current_owner_role'),
}))
PY
)"
MODEL_FLAG="$(python3 - <<'PY' "$PAA_AUTOMATION_RUN_DIR/preflight.json"
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
print('1' if payload.get('should_invoke_model') else '0')
PY
)"

if [ "$MODEL_FLAG" = "1" ]; then
  "$EVENT_HELPER" \
    --event preflight_check \
    --phase "$PHASE" \
    --status work_present \
    --message "$PRETTY_MESSAGE" \
    --model-invoked \
    --cwd "$REPO_ROOT" \
    --extra-json "$EXTRA_JSON"
else
  "$EVENT_HELPER" \
    --event preflight_check \
    --phase "$PHASE" \
    --status no_work \
    --message "$PRETTY_MESSAGE" \
    --cwd "$REPO_ROOT" \
    --extra-json "$EXTRA_JSON"
fi

python3 - <<'PY' "$PAA_AUTOMATION_SUMMARY_FILE" "$PAA_AUTOMATION_RUN_DIR/preflight.json"
import json, sys
from pathlib import Path
summary_path = Path(sys.argv[1])
preflight_path = Path(sys.argv[2])
summary = json.loads(summary_path.read_text())
preflight = json.loads(preflight_path.read_text())
summary['preflight'] = {
    'should_invoke_model': preflight.get('should_invoke_model'),
    'skip_model_invocation': preflight.get('skip_model_invocation'),
    'gate_reason': preflight.get('gate_reason'),
    'workflow_stage': preflight.get('workflow_stage'),
    'current_owner_role': preflight.get('current_owner_role'),
}
summary['status'] = 'preflight_complete'
summary_path.write_text(json.dumps(summary, indent=2) + '\n')
PY

printf '%s\n' "$PREFLIGHT_OUTPUT"
