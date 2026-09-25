#!/usr/bin/env bash
# ARC-Bench Reproduction Matrix — Noise isolation for timing-sensitive requirements
# Usage: ./scripts/arc-bench-repro-matrix.sh [options]
#
# Options:
#   --req <id>              : Requirement ID (e.g., REQ-8.1)
#   --seed <path>           : Path to frozen seed JSON
#   --iterations <n>        : Number of independent runs (default: 10)
#   --discard-extremes <n>  : Discard N fastest + N slowest (default: 1)
#   --task <name>           : bookstack or keep (default: from seed)
#   --output <dir>          : Output directory (default: evidence/arc-bench/repro-matrix/)
#   --threshold <ratio>     : Confirmation threshold (default: 0.75, i.e., 6/8 after discarding)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REQ_ID=""
SEED_PATH=""
ITERATIONS=10
DISCARD_EXTREMES=1
TASK=""
OUTPUT=""
THRESHOLD=0.75

for arg in "$@"; do
    case "$arg" in
        --req)
            shift
            REQ_ID="${1:-}"
            shift || true
            ;;
        --seed)
            shift
            SEED_PATH="${1:-}"
            shift || true
            ;;
        --iterations)
            shift
            ITERATIONS="${1:-10}"
            shift || true
            ;;
        --discard-extremes)
            shift
            DISCARD_EXTREMES="${1:-1}"
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
        --threshold)
            shift
            THRESHOLD="${1:-0.75}"
            shift || true
            ;;
        --help|-h)
            sed -n '2,13p' "$0" | sed 's/^# //'
            exit 0
            ;;
    esac
done

pass() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m⚠\033[0m %s\n" "$1"; }
section() { printf "\n\033[1m── %s ──\033[0m\n" "$1"; }
info() { printf "  \033[36mℹ\033[0m %s\n" "$1"; }

# ── Validation ────────────────────────────────────────────────────────
section "Reproduction Matrix Setup"

if [ -z "$REQ_ID" ]; then
    fail "Missing --req <id>"
    exit 1
fi

if [ -z "$SEED_PATH" ]; then
    fail "Missing --seed <path>"
    exit 1
fi

if [ ! -f "$SEED_PATH" ]; then
    fail "Seed file not found: $SEED_PATH"
    exit 1
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEFAULT_OUTPUT="evidence/arc-bench/repro-matrix/${REQ_ID}-${TIMESTAMP}"
OUTPUT="${OUTPUT:-$DEFAULT_OUTPUT}"

info "Requirement: $REQ_ID"
info "Seed: $SEED_PATH"
info "Iterations: $ITERATIONS"
info "Discard extremes: $DISCARD_EXTREMES (fastest + slowest)"
info "Threshold: $THRESHOLD ($(echo "$THRESHOLD * ($ITERATIONS - 2 * $DISCARD_EXTREMES)" | bc) / $((ITERATIONS - 2 * DISCARD_EXTREMES)) required)"
info "Output: $OUTPUT"

mkdir -p "$OUTPUT"

# ── Execution Loop ────────────────────────────────────────────────────
section "Running Iterations"

RESULTS=()
DURATIONS=()
FAILED_COUNT=0
PASSED_COUNT=0

for i in $(seq 1 "$ITERATIONS"); do
    ITER_DIR="$OUTPUT/iteration-$(printf '%03d' "$i")"
    mkdir -p "$ITER_DIR"

    info "Iteration $i/$ITERATIONS..."

    # Simulate test execution (actual implementation would run the skill)
    # For now, create a placeholder result

    warn "Test execution not yet implemented"
    warn "Expected: Run skill with frozen seed, record pass/fail + duration"

    # Placeholder: random result for demonstration
    SIMULATED_RESULT="unknown"
    SIMULATED_DURATION="unknown"

    echo "$SIMULATED_RESULT" > "$ITER_DIR/result.txt"
    echo "$SIMULATED_DURATION" > "$ITER_DIR/duration.txt"

    cat > "$ITER_DIR/metadata.json" <<EOF
{
  "iteration": $i,
  "req_id": "$REQ_ID",
  "seed": "$SEED_PATH",
  "result": "$SIMULATED_RESULT",
  "duration_seconds": "$SIMULATED_DURATION",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "note": "Simulated run — actual execution not implemented"
}
EOF

    RESULTS+=("$SIMULATED_RESULT")
    DURATIONS+=("$SIMULATED_DURATION")

    if [ "$SIMULATED_RESULT" = "pass" ]; then
        PASSED_COUNT=$((PASSED_COUNT + 1))
    elif [ "$SIMULATED_RESULT" = "fail" ]; then
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
done

# ── Analysis ──────────────────────────────────────────────────────────
section "Analysis (After Discarding Extremes)"

# Note: Actual implementation would:
# 1. Sort DURATIONS, remove fastest N and slowest N
# 2. Count consistent pass/fail in remaining samples
# 3. Calculate noise ratio (range / median)

RETAINED_COUNT=$((ITERATIONS - 2 * DISCARD_EXTREMES))
CONFIRMATION_THRESHOLD=$(echo "$THRESHOLD * $RETAINED_COUNT" | bc | awk '{print int($1 + 0.5)}')

warn "Discard logic not yet implemented"
info "Would retain: $RETAINED_COUNT samples"
info "Would require: $CONFIRMATION_THRESHOLD consistent results for confirmation"

# Determine verdict (placeholder logic)
VERDICT="unknown"
NOISE_RATIO="N/A"

if [ "$FAILED_COUNT" -ge "$CONFIRMATION_THRESHOLD" ]; then
    VERDICT="confirmed"
    pass "Verdict: CONFIRMED (reproduces consistently)"
elif [ "$PASSED_COUNT" -ge "$CONFIRMATION_THRESHOLD" ]; then
    VERDICT="false_alarm"
    warn "Verdict: FALSE ALARM (passes consistently after retry)"
else
    VERDICT="timing_sensitive"
    warn "Verdict: TIMING SENSITIVE (inconsistent results)"
fi

# ── Summary ───────────────────────────────────────────────────────────
section "Matrix Summary"

cat > "$OUTPUT/matrix-summary.json" <<EOF
{
  "req_id": "$REQ_ID",
  "seed": "$SEED_PATH",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "config": {
    "iterations": $ITERATIONS,
    "discard_extremes": $DISCARD_EXTREMES,
    "retained_count": $RETAINED_COUNT,
    "confirmation_threshold": $CONFIRMATION_THRESHOLD
  },
  "results": {
    "total": $ITERATIONS,
    "passed": $PASSED_COUNT,
    "failed": $FAILED_COUNT,
    "verdict": "$VERDICT",
    "noise_ratio": "$NOISE_RATIO"
  },
  "note": "Execution not yet implemented — this is a simulation"
}
EOF

info "Summary written to: $OUTPUT/matrix-summary.json"

# ── Recommendations ───────────────────────────────────────────────────
section "Recommendations"

case "$VERDICT" in
    confirmed)
        info "✓ This issue is CONFIRMED and can proceed to Agent implementation"
        info "  Next step: Create minimal Agent slice for $REQ_ID"
        ;;
    false_alarm)
        warn "⚠ This appears to be a FALSE ALARM (transient or fixed)"
        info "  Next step: Update decision register to exclude $REQ_ID"
        ;;
    timing_sensitive)
        warn "⚠ Results are TIMING SENSITIVE (inconsistent)"
        info "  Next step: Increase iterations or isolate timing source"
        info "  Consider: Add trace logging, check for async race conditions"
        ;;
    *)
        warn "⚠ Unable to determine verdict (execution not implemented)"
        ;;
esac

echo ""
info "Full results in: $OUTPUT"
info "Review individual iterations in: $OUTPUT/iteration-*/"

exit 0
