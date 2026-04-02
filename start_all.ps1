param(
    [switch]$InstallFrontendDeps
)

$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$venvActivate = Join-Path $repoRoot "venv\Scripts\Activate.ps1"
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

Write-Host "Starting backend API terminal..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "& '$venvActivate'; Set-Location '$backendDir'; python .\api.py"
)

Start-Sleep -Seconds 1

$healthUrl = "http://127.0.0.1:8000/health"
$maxWaitSec = 45
$elapsedSec = 0

Write-Host "Waiting for backend readiness at $healthUrl ..."
while ($elapsedSec -lt $maxWaitSec) {
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 2
        if ($health.api -eq "ready") {
            Write-Host "Backend is ready (llm_provider=$($health.llm_provider), llm_status=$($health.model_server))."
            break
        }
        Write-Host "Backend health status=$($health.status), waiting..."
    }
    catch {
        Write-Host "Backend not reachable yet, waiting..."
    }

    Start-Sleep -Seconds 1
    $elapsedSec += 1
}

if ($elapsedSec -ge $maxWaitSec) {
    Write-Warning "Backend did not become ready in $maxWaitSec seconds. Frontend will still start."
}

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
