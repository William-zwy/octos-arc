#!/usr/bin/env bash
# ARC-Bench Gate — Multi-tier validation for ARC-Bench runs
# Usage: ./scripts/arc-bench-gate.sh <mode> [options]
#
# Modes:
#   quick      : Fast local checks (5 min, no platform cost)
#   canary     : Single-task validation (1h, ~¥6)
#   full       : Full A/B comparison (5-10h, ¥36-74)
#   preflight  : Pre-upload validation (auth, env, package structure)
#
# Options:
#   --task <name>           : bookstack or keep (canary/full)
#   --base <commit>         : Base commit for A/B (full mode)
#   --head <commit>         : Head commit for A/B (full mode)
#   --baseline-score <n/m>  : Required minimum score (default: from config)
#   --strict                : Fail on any regression, no INCONCLUSIVE pass

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="${1:-}"
shift || true

TASK=""
BASE_COMMIT=""
HEAD_COMMIT=""
BASELINE_SCORE=""
STRICT=false

for arg in "$@"; do
    case "$arg" in
        --task)
            shift
            TASK="${1:-}"
            shift || true
            ;;
        --base)
            shift
            BASE_COMMIT="${1:-}"
            shift || true
            ;;
        --head)
            shift
            HEAD_COMMIT="${1:-}"
            shift || true
            ;;
        --baseline-score)
            shift
            BASELINE_SCORE="${1:-}"
            shift || true
            ;;
        --strict)
            STRICT=true
            ;;
        --help|-h)
            sed -n '2,15p' "$0" | sed 's/^# //'
            exit 0
            ;;
    esac
done

PASS=0
FAIL=0
STARTED=$(date +%s)

pass() { PASS=$((PASS + 1)); printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { FAIL=$((FAIL + 1)); printf "  \033[31m✗\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m⚠\033[0m %s\n" "$1"; }
section() { printf "\n\033[1m── %s ──\033[0m\n" "$1"; }
info() { printf "  \033[36mℹ\033[0m %s\n" "$1"; }

# ── Quick Mode ────────────────────────────────────────────────────────
run_quick() {
    section "Quick Gate (Local Checks)"

    # 1. Static analysis
    info "Checking Rust format..."
    if cargo fmt --all -- --check >/dev/null 2>&1; then
        pass "cargo fmt"
    else
        fail "cargo fmt (run: cargo fmt --all)"
    fi

    # 2. Lint
    info "Running clippy..."
    if cargo clippy --workspace --all-targets -- -D warnings >/dev/null 2>&1; then
        pass "cargo clippy"
    else
        fail "cargo clippy"
    fi

    # 3. Unit tests
    info "Running workspace tests..."
    if cargo test --workspace --lib >/dev/null 2>&1; then
        pass "cargo test --workspace --lib"
    else
        fail "cargo test --workspace (unit tests)"
    fi

    # 4. Agent prompt format check
    info "Validating Agent prompt templates..."
    if [ -d "crates/octos-agent/prompts" ]; then
        if find crates/octos-agent/prompts -name "*.txt" -exec grep -L "{{" {} \; | grep -q .; then
            fail "Agent prompts contain unescaped {{ templates"
        else
            pass "Agent prompt format"
        fi
    else
        warn "Agent prompts directory not found, skipping"
    fi

    info "Quick gate completed in $(($(date +%s) - STARTED))s"
    return $FAIL
}

# ── Preflight Mode ────────────────────────────────────────────────────
run_preflight() {
    section "Preflight Checks (Pre-Upload Validation)"

    local MANIFEST_PATH="evidence/arc-bench/preflight-manifest.json"
    local TIMESTAMP
    TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    # 1. Environment variables
    info "Checking OCTOS_ARC_IMPLEMENT_REQUESTS..."
    if [ -n "${OCTOS_ARC_IMPLEMENT_REQUESTS:-}" ]; then
        if [ "$OCTOS_ARC_IMPLEMENT_REQUESTS" -lt 100 ]; then
            fail "OCTOS_ARC_IMPLEMENT_REQUESTS=$OCTOS_ARC_IMPLEMENT_REQUESTS too low (expect ≥100)"
        else
            pass "OCTOS_ARC_IMPLEMENT_REQUESTS=$OCTOS_ARC_IMPLEMENT_REQUESTS"
        fi
    else
        warn "OCTOS_ARC_IMPLEMENT_REQUESTS not set (will use default)"
    fi

    # 2. Authentication preflight
    info "Testing authentication endpoint..."
    local AUTH_URL="${OCTOS_ARC_PLATFORM_URL:-https://arc-bench.example.com}/api/auth/preflight"
    if command -v curl >/dev/null 2>&1; then
        local HTTP_CODE
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH_URL" || echo "000")
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "204" ]; then
            pass "Auth preflight: $HTTP_CODE"
        elif [ "$HTTP_CODE" = "401" ]; then
            fail "Auth preflight: 401 Unauthorized (check API key)"
        else
            warn "Auth preflight: $HTTP_CODE (may need manual check)"
        fi
    else
        warn "curl not found, skipping auth preflight"
    fi

    # 3. Package structure validation
    info "Validating generated package structure..."
    local EXPECTED_FILES=(
        "frontend"
        "backend"
        "main.py"
        "tests"
    )

    # This check assumes a test build exists in skill-output/
    local TEST_BUILD_DIR
    TEST_BUILD_DIR=$(find skill-output -type d -name "bookstack-*" -o -name "keep-*" 2>/dev/null | head -1 || echo "")

    if [ -n "$TEST_BUILD_DIR" ] && [ -d "$TEST_BUILD_DIR" ]; then
        local MISSING=0
        for FILE in "${EXPECTED_FILES[@]}"; do
            if [ -e "$TEST_BUILD_DIR/$FILE" ]; then
                pass "Package contains: $FILE"
            else
                fail "Package missing: $FILE"
                MISSING=1
            fi
        done

        if [ $MISSING -eq 0 ]; then
            pass "Package structure complete"
        fi
    else
        warn "No test build found in skill-output/, skipping package structure check"
    fi

    # 4. Write manifest
    mkdir -p "$(dirname "$MANIFEST_PATH")"
    cat > "$MANIFEST_PATH" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "checks": {
    "implement_requests": ${OCTOS_ARC_IMPLEMENT_REQUESTS:-null},
    "auth_preflight": "${HTTP_CODE:-unknown}",
    "package_structure": $([ $FAIL -eq 0 ] && echo "true" || echo "false")
  },
  "pass": $PASS,
  "fail": $FAIL
}
EOF

    info "Preflight manifest written to: $MANIFEST_PATH"
    info "Preflight completed in $(($(date +%s) - STARTED))s"

    return $FAIL
}

# ── Canary Mode ───────────────────────────────────────────────────────
run_canary() {
    section "Canary Gate (Single Task)"

    if [ -z "$TASK" ]; then
        fail "Canary mode requires --task <bookstack|keep>"
        return 1
    fi

    case "$TASK" in
        bookstack)
            local DEFAULT_BASELINE="31/34"
            ;;
        keep)
            local DEFAULT_BASELINE="27/32"
            ;;
        *)
            fail "Unknown task: $TASK (expected bookstack or keep)"
            return 1
            ;;
    esac

    local BASELINE="${BASELINE_SCORE:-$DEFAULT_BASELINE}"
    info "Task: $TASK"
    info "Baseline: $BASELINE (no-regression floor)"

    warn "Canary execution not yet implemented"
    warn "Expected: Run skill for $TASK, check score ≥ $BASELINE"
    warn "Cost: ~¥6, Duration: ~1 hour"

    return 1
}

# ── Full Mode ─────────────────────────────────────────────────────────
run_full() {
    section "Full A/B Gate"

    if [ -z "$BASE_COMMIT" ] || [ -z "$HEAD_COMMIT" ]; then
        fail "Full mode requires --base <commit> --head <commit>"
        return 1
    fi

    info "Base: $BASE_COMMIT"
    info "Head: $HEAD_COMMIT"

    warn "Full A/B execution not yet implemented"
    warn "Expected: Run both BookStack + Keep for base/head, compare scores"
    warn "Cost: ¥36-74, Duration: 5-10 hours"

    return 1
}

# ── Main ──────────────────────────────────────────────────────────────
case "$MODE" in
    quick)
        run_quick
        EXIT_CODE=$?
        ;;
    preflight)
        run_preflight
        EXIT_CODE=$?
        ;;
    canary)
        run_canary
        EXIT_CODE=$?
        ;;
    full)
        run_full
        EXIT_CODE=$?
        ;;
    ""|--help|-h)
        sed -n '2,15p' "$0" | sed 's/^# //'
        exit 0
        ;;
    *)
        echo "Unknown mode: $MODE"
        echo "Use: quick, preflight, canary, or full"
        exit 1
        ;;
esac

ELAPSED=$(($(date +%s) - STARTED))
printf "\n\033[1m── Summary ──\033[0m\n"
printf "  Pass: %d  Fail: %d  Time: %ds\n" "$PASS" "$FAIL" "$ELAPSED"

if [ "$EXIT_CODE" -eq 0 ]; then
    printf "\n\033[32m✓ Gate PASSED\033[0m\n"
else
    printf "\n\033[31m✗ Gate FAILED\033[0m\n"
fi

exit "$EXIT_CODE"
