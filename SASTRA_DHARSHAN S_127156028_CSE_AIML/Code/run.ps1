# ============================================================
# Automotive Engineering AI Assistant - Windows PowerShell Runner
# ============================================================

param (
    [string]$Mode = "ui"  # options: 'ui', 'api', 'all', 'test', 'eval'
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Automotive Engineering AI Assistant: AUTOSAR HLD Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Ensure sample files exist
if (-not (Test-Path "sample_data\AUTOSAR_Powertrain_Domain_HLD_v1.0.pdf")) {
    Write-Host "[1/3] Generating synthetic benchmark AUTOSAR PDFs..." -ForegroundColor Yellow
    python sample_data\generate_sample_pdfs.py
}

if ($Mode -eq "test") {
    Write-Host "Running automated test suite..." -ForegroundColor Green
    python -m pytest tests/ -v
}
elseif ($Mode -eq "eval") {
    Write-Host "Running RAG evaluation benchmark..." -ForegroundColor Green
    python evaluation\evaluate_rag.py
}
elseif ($Mode -eq "api") {
    Write-Host "Starting FastAPI REST Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
    python app.py --mode api
}
elseif ($Mode -eq "ui") {
    Write-Host "Starting Streamlit UI on http://localhost:8501 ..." -ForegroundColor Green
    python app.py --mode ui
}
elseif ($Mode -eq "all") {
    Write-Host "Starting both FastAPI and Streamlit services..." -ForegroundColor Green
    python app.py --mode all
}
else {
    Write-Host "Invalid mode. Choose: 'ui', 'api', 'all', 'test', or 'eval'." -ForegroundColor Red
}
