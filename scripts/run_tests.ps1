# =============================================================
# NexaSupport AI — Test & Evaluation Runner
# =============================================================
# Usage:
#   .\scripts\run_tests.ps1            # Run all unit tests
#   .\scripts\run_tests.ps1 -Eval      # Also run offline RAG evaluation
#   .\scripts\run_tests.ps1 -Coverage  # Generate HTML coverage report
# =============================================================

param(
    [switch]$Eval,
    [switch]$Coverage
)

$PYTHON = ".\venv\Scripts\python.exe"
$PYTEST  = ".\venv\Scripts\pytest.exe"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  NexaSupport AI — Test Runner" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Unit + API Tests ──────────────────────────────────────
Write-Host "Running test suite..." -ForegroundColor Yellow

if ($Coverage) {
    & $PYTHON -m pytest tests/ `
        --cov=app `
        --cov-report=html:htmlcov `
        --cov-report=term-missing `
        -v
} else {
    & $PYTEST tests/ -v --tb=short
}

$TestExit = $LASTEXITCODE

if ($TestExit -eq 0) {
    Write-Host ""
    Write-Host "  All tests passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  Some tests failed (exit code $TestExit)" -ForegroundColor Red
}

# ── 2. Optional RAG Evaluation ───────────────────────────────
if ($Eval) {
    Write-Host ""
    Write-Host "Running offline RAG evaluation..." -ForegroundColor Yellow
    & $PYTHON evaluation\evaluate_rag.py
    $EvalExit = $LASTEXITCODE
    if ($EvalExit -eq 0) {
        Write-Host "  Evaluation passed!" -ForegroundColor Green
    } else {
        Write-Host "  Evaluation detected failures (exit $EvalExit)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
exit $TestExit
