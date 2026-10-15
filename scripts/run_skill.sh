#!/usr/bin/env bash
# Runs the refactor-arch skill headlessly inside one project.
#   phase12: invokes /refactor-arch (Phases 1-2) and stops at the confirmation question.
#   phase3:  resumes that session answering "y" (Phase 3).
# Usage: scripts/run_skill.sh <project-dir> <phase12|phase3>
set -euo pipefail

if [[ $# -ne 2 || ! "$2" =~ ^(phase12|phase3)$ ]]; then
  echo "usage: $0 <project-dir> <phase12|phase3>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$(cd "$1" && pwd)"
PHASE="$2"
MODEL="${REFACTOR_ARCH_MODEL:-claude-opus-5-5}"

case "$(basename "$PROJECT_DIR")" in
  code-smells-project) NUMBER=1 ;;
  ecommerce-api-legacy) NUMBER=2 ;;
  task-manager-api) NUMBER=3 ;;
  *) echo "unknown project: $PROJECT_DIR" >&2; exit 2 ;;
esac

LOG_DIR="$ROOT/reports/logs"
LOG_BASE="$LOG_DIR/project-$NUMBER-$PHASE"
SESSION_FILE="$LOG_DIR/project-$NUMBER-session-id"
mkdir -p "$LOG_DIR"

if [[ ! -f "$PROJECT_DIR/.claude/skills/refactor-arch/SKILL.md" ]]; then
  echo "skill not found in $PROJECT_DIR/.claude/skills/refactor-arch" >&2
  exit 1
fi

COMMON_ARGS=(
  -p
  --model "$MODEL"
  --permission-mode acceptEdits
  --allowedTools Bash
  --output-format stream-json
  --verbose
)

# caffeinate keeps macOS from idle-sleeping during long runs (a sleep aborts the API request).
RUNNER=(env -u CLAUDECODE)
command -v caffeinate > /dev/null && RUNNER=(caffeinate -i "${RUNNER[@]}")

cd "$PROJECT_DIR"
STATUS=0
if [[ "$PHASE" == "phase12" ]]; then
  "${RUNNER[@]}" claude "${COMMON_ARGS[@]}" "/refactor-arch" < /dev/null > "$LOG_BASE.jsonl" || STATUS=$?
else
  if [[ ! -s "$SESSION_FILE" ]]; then
    echo "run phase12 first: $SESSION_FILE is missing" >&2
    exit 1
  fi
  "${RUNNER[@]}" claude "${COMMON_ARGS[@]}" --resume "$(cat "$SESSION_FILE")" "y" < /dev/null > "$LOG_BASE.jsonl" || STATUS=$?
fi

python3 "$ROOT/scripts/render_transcript.py" "$LOG_BASE.jsonl" "$LOG_BASE.md" > "$LOG_BASE.session"
SESSION_ID="$(cat "$LOG_BASE.session")"
rm -f "$LOG_BASE.session"
[[ "$PHASE" == "phase12" ]] && echo "$SESSION_ID" > "$SESSION_FILE"

echo "session: $SESSION_ID"
echo "raw log: $LOG_BASE.jsonl"
echo "transcript: $LOG_BASE.md"
exit "$STATUS"
