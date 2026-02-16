#!/usr/bin/env bash
# End-to-end validation: report output dir and backend readiness.
# Run from project root: ./scripts/validate-e2e.sh

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$PROJECT_ROOT/out/web_runs"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "=== E2E validation ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# 1. Check report output directory
if [[ ! -d "$OUT_DIR" ]]; then
  echo "FAIL: out/web_runs not found. Create a report (New Report) first so Python/Java can write CSVs."
  exit 1
fi
echo "OK: out/web_runs exists"

# 2. List run IDs that have report data (so user can open one and see data)
RUNS_WITH_CSV=()
for d in "$OUT_DIR"/[0-9]* "$OUT_DIR"/run_*; do
  if [[ -d "$d" && -f "$d/inventory_report.csv" ]]; then
    RUNS_WITH_CSV+=("$(basename "$d")")
  fi
done

if [[ ${#RUNS_WITH_CSV[@]} -eq 0 ]]; then
  echo "No run folders with inventory_report.csv found. Generate a report (New Report) first."
else
  echo "OK: ${#RUNS_WITH_CSV[@]} run(s) with report data: ${RUNS_WITH_CSV[*]}"
  echo "   → Open one of these in the app to see data (e.g. /runs/${RUNS_WITH_CSV[0]})"
fi

# 3. Backend must run from backend/ so output-dir = \${user.dir}/../out/web_runs
echo ""
echo "Backend: start from backend/ so output-dir points here:"
echo "   cd $BACKEND_DIR && mvn spring-boot:run"
echo ""

# 4. Optional: health check
if command -v curl &>/dev/null; then
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null | grep -q 200; then
    echo "OK: Backend is running (GET /health 200)"
  else
    echo "Note: Backend not reachable on :8080. Start it to test report data in the UI."
  fi
fi

echo ""
echo "=== Validation done ==="
