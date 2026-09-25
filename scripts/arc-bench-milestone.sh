#!/usr/bin/env bash
# ARC-Bench Milestone — Upload coordination and A/B identity binding
# Usage: ./scripts/arc-bench-milestone.sh <command> [options]
#
# Commands:
#   upload-and-bind       : Upload agent build, record task_snapshot_id
#   validate-ab-pair      : Validate A/B identity chain for comparison
#   generate-frozen-seed  : Extract frozen seed from a reference run
#
# Options (upload-and-bind):
#   --agent-build-sha <sha>  : Git SHA of agent build
#   --task <name>            : bookstack or keep
#   --output <path>          : Receipt output path (default: evidence/arc-bench/upload-receipts/)
#
# Options (validate-ab-pair):
#   --base-receipt <file>    : Base upload receipt JSON
#   --head-receipt <file>    : Head upload receipt JSON
#   --run-id <id>            : Platform run ID to validate
#   --output <path>          : Validation output path
#
# Options (generate-frozen-seed):
#   --run-id <id>            : Reference run ID to extract seed from
#   --output <path>          : Seed output path

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMMAND="${1:-}"
shift || true

AGENT_BUILD_SHA=""
TASK=""
OUTPUT=""
BASE_RECEIPT=""
HEAD_RECEIPT=""
RUN_ID=""

for arg in "$@"; do
    case "$arg" in
        --agent-build-sha)
            shift
            AGENT_BUILD_SHA="${1:-}"
            shift || true
            ;;
        --task)
            shift
            TASK="${1:-}"
            shift || true
            ;;
        --output)
            shift
            OUTPUT="${1:-}"
            shift || true
            ;;
        --base-receipt)
            shift
            BASE_RECEIPT="${1:-}"
            shift || true
            ;;
        --head-receipt)
            shift
            HEAD_RECEIPT="${1:-}"
            shift || true
            ;;
        --run-id)
            shift
            RUN_ID="${1:-}"
            shift || true
            ;;
        --help|-h)
            sed -n '2,23p' "$0" | sed 's/^# //'
            exit 0
            ;;
    esac
done

pass() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m⚠\033[0m %s\n" "$1"; }
section() { printf "\n\033[1m── %s ──\033[0m\n" "$1"; }
info() { printf "  \033[36mℹ\033[0m %s\n" "$1"; }

# ── upload-and-bind ───────────────────────────────────────────────────
upload_and_bind() {
    section "Upload and Bind Agent Build"

    if [ -z "$AGENT_BUILD_SHA" ]; then
        fail "Missing --agent-build-sha <sha>"
        return 1
    fi

    if [ -z "$TASK" ]; then
        fail "Missing --task <bookstack|keep>"
        return 1
    fi

    local TIMESTAMP
    TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    local DEFAULT_OUTPUT="evidence/arc-bench/upload-receipts/${TASK}-${AGENT_BUILD_SHA:0:8}-${TIMESTAMP}.json"
    OUTPUT="${OUTPUT:-$DEFAULT_OUTPUT}"

    info "Agent Build SHA: $AGENT_BUILD_SHA"
    info "Task: $TASK"
    info "Output: $OUTPUT"

    # Simulate upload (actual implementation would call platform API)
    warn "Upload execution not yet implemented"
    warn "Expected steps:"
    warn "  1. Build agent package from $AGENT_BUILD_SHA"
    warn "  2. Upload to platform and receive task_snapshot_id"
    warn "  3. Record receipt with full identity chain"

    # Create receipt template
    mkdir -p "$(dirname "$OUTPUT")"
    cat > "$OUTPUT" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "agent_build_sha": "$AGENT_BUILD_SHA",
  "task": "$TASK",
  "task_snapshot_id": "PLACEHOLDER_SNAPSHOT_ID",
  "upload_url": "https://arc-bench.example.com/uploads/PLACEHOLDER",
  "platform_response": {
    "status": "pending",
    "note": "Upload not yet executed — this is a template"
  },
  "git_info": {
    "repo": "$(git remote get-url origin 2>/dev/null || echo 'unknown')",
    "branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "commit_timestamp": "$(git show -s --format=%ci "$AGENT_BUILD_SHA" 2>/dev/null || echo 'unknown')"
  }
}
EOF

    info "Receipt template written to: $OUTPUT"
    warn "Manual upload required to populate task_snapshot_id"

    return 1
}

# ── validate-ab-pair ──────────────────────────────────────────────────
validate_ab_pair() {
    section "Validate A/B Identity Pair"

    if [ -z "$BASE_RECEIPT" ] || [ -z "$HEAD_RECEIPT" ] || [ -z "$RUN_ID" ]; then
        fail "Missing required options: --base-receipt, --head-receipt, --run-id"
        return 1
    fi

    if [ ! -f "$BASE_RECEIPT" ]; then
        fail "Base receipt not found: $BASE_RECEIPT"
        return 1
    fi

    if [ ! -f "$HEAD_RECEIPT" ]; then
        fail "Head receipt not found: $HEAD_RECEIPT"
        return 1
    fi

    info "Base Receipt: $BASE_RECEIPT"
    info "Head Receipt: $HEAD_RECEIPT"
    info "Run ID: $RUN_ID"

    local DEFAULT_OUTPUT="evidence/arc-bench/ab-validations/${RUN_ID}-validation.json"
    OUTPUT="${OUTPUT:-$DEFAULT_OUTPUT}"

    # Extract fields (requires jq)
    if ! command -v jq >/dev/null 2>&1; then
        fail "jq not found (required for JSON parsing)"
        return 1
    fi

    local BASE_TASK BASE_SHA BASE_SNAPSHOT
    local HEAD_TASK HEAD_SHA HEAD_SNAPSHOT

    BASE_TASK=$(jq -r '.task' "$BASE_RECEIPT")
    BASE_SHA=$(jq -r '.agent_build_sha' "$BASE_RECEIPT")
    BASE_SNAPSHOT=$(jq -r '.task_snapshot_id' "$BASE_RECEIPT")

    HEAD_TASK=$(jq -r '.task' "$HEAD_RECEIPT")
    HEAD_SHA=$(jq -r '.agent_build_sha' "$HEAD_RECEIPT")
    HEAD_SNAPSHOT=$(jq -r '.task_snapshot_id' "$HEAD_RECEIPT")

    local VALIDATION_PASS=true
    local ISSUES=()

    # Check 1: Same task
    if [ "$BASE_TASK" != "$HEAD_TASK" ]; then
        fail "Task mismatch: base=$BASE_TASK, head=$HEAD_TASK"
        VALIDATION_PASS=false
        ISSUES+=("task_mismatch")
    else
        pass "Task match: $BASE_TASK"
    fi

    # Check 2: Different builds
    if [ "$BASE_SHA" = "$HEAD_SHA" ]; then
        warn "Base and head have same SHA: $BASE_SHA (not a real A/B)"
        ISSUES+=("same_build")
    else
        pass "Different builds: ${BASE_SHA:0:8} vs ${HEAD_SHA:0:8}"
    fi

    # Check 3: Valid snapshot IDs
    if [ "$BASE_SNAPSHOT" = "PLACEHOLDER_SNAPSHOT_ID" ] || [ "$BASE_SNAPSHOT" = "null" ]; then
        fail "Base snapshot ID not populated"
        VALIDATION_PASS=false
        ISSUES+=("base_snapshot_missing")
    else
        pass "Base snapshot: $BASE_SNAPSHOT"
    fi

    if [ "$HEAD_SNAPSHOT" = "PLACEHOLDER_SNAPSHOT_ID" ] || [ "$HEAD_SNAPSHOT" = "null" ]; then
        fail "Head snapshot ID not populated"
        VALIDATION_PASS=false
        ISSUES+=("head_snapshot_missing")
    else
        pass "Head snapshot: $HEAD_SNAPSHOT"
    fi

    # Check 4: Run metadata (simulated — would query platform API)
    warn "Platform run validation not yet implemented"
    warn "Expected: Query run $RUN_ID metadata, verify it references both snapshot IDs"

    # Write validation result
    mkdir -p "$(dirname "$OUTPUT")"
    cat > "$OUTPUT" <<EOF
{
  "run_id": "$RUN_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "base_receipt": "$BASE_RECEIPT",
  "head_receipt": "$HEAD_RECEIPT",
  "base": {
    "task": "$BASE_TASK",
    "agent_build_sha": "$BASE_SHA",
    "task_snapshot_id": "$BASE_SNAPSHOT"
  },
  "head": {
    "task": "$HEAD_TASK",
    "agent_build_sha": "$HEAD_SHA",
    "task_snapshot_id": "$HEAD_SNAPSHOT"
  },
  "validation": {
    "strict_comparable": $([ "$VALIDATION_PASS" = true ] && echo "true" || echo "false"),
    "issues": $(printf '%s\n' "${ISSUES[@]}" | jq -R . | jq -s .)
  }
}
EOF

    info "Validation result written to: $OUTPUT"

    if [ "$VALIDATION_PASS" = true ]; then
        pass "A/B pair validation PASSED"
        return 0
    else
        fail "A/B pair validation FAILED"
        return 1
    fi
}

# ── generate-frozen-seed ──────────────────────────────────────────────
generate_frozen_seed() {
    section "Generate Frozen Seed from Reference Run"

    if [ -z "$RUN_ID" ]; then
        fail "Missing --run-id <id>"
        return 1
    fi

    local DEFAULT_OUTPUT="evidence/arc-bench/frozen-seeds/${RUN_ID}-seed.json"
    OUTPUT="${OUTPUT:-$DEFAULT_OUTPUT}"

    info "Reference Run: $RUN_ID"
    info "Output: $OUTPUT"

    local RUN_DIR="evidence/arc-bench/runs/$RUN_ID"
    if [ ! -d "$RUN_DIR" ]; then
        fail "Run directory not found: $RUN_DIR"
        return 1
    fi

    warn "Seed extraction not yet implemented"
    warn "Expected steps:"
    warn "  1. Read manifest.json from $RUN_DIR"
    warn "  2. Extract initial task state (DB fixtures, seed data)"
    warn "  3. Normalize and write to frozen-seeds/"

    mkdir -p "$(dirname "$OUTPUT")"
    cat > "$OUTPUT" <<EOF
{
  "source_run_id": "$RUN_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "seed_version": "v2",
  "note": "Seed extraction not yet implemented — this is a template",
  "tasks": {
    "bookstack": {
      "initial_db_state": "PLACEHOLDER",
      "fixture_data": "PLACEHOLDER"
    },
    "keep": {
      "initial_db_state": "PLACEHOLDER",
      "fixture_data": "PLACEHOLDER"
    }
  }
}
EOF

    info "Seed template written to: $OUTPUT"
    warn "Manual extraction required to populate actual seed data"

    return 1
}

# ── Main ──────────────────────────────────────────────────────────────
case "$COMMAND" in
    upload-and-bind)
        upload_and_bind
        ;;
    validate-ab-pair)
        validate_ab_pair
        ;;
    generate-frozen-seed)
        generate_frozen_seed
        ;;
    ""|--help|-h)
        sed -n '2,23p' "$0" | sed 's/^# //'
        exit 0
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Use: upload-and-bind, validate-ab-pair, or generate-frozen-seed"
        exit 1
        ;;
esac
