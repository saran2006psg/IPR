param(
    [switch]$InstallFrontendDeps
)

$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$venvActivate = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"

if (-not (Test-Path $venvActivate)) {
    Write-Error "Virtual environment not found at: $venvActivate"
}

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    Write-Error "Frontend folder missing or invalid: $frontendDir"
}

if ($InstallFrontendDeps -or -not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $frontendDir
    npm install
    Pop-Location
}

Write-Host "Starting model server terminal..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "& '$venvActivate'; Set-Location '$backendDir'; python .\model_server.py"
)

Start-Sleep -Seconds 1

Write-Host "Starting backend API terminal..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "& '$venvActivate'; Set-Location '$backendDir'; python .\api.py"
)

Start-Sleep -Seconds 1

Write-Host "Starting frontend terminal..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "Set-Location '$frontendDir'; npm run dev"
)

Write-Host "All services launched in separate terminals."
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend API: http://localhost:8000"
Write-Host "Model Server: http://127.0.0.1:9000/health"
