
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("Start", "Stop", "Status")]
    [string]$Action = "Start",

    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$PidFile = Join-Path $ProjectRoot ".pega-app.pid"
$LogFile = Join-Path $ProjectRoot "pega-app.log"
$Url = "http://127.0.0.1:$Port/"

function Get-AppProcess {
    if (-not (Test-Path $PidFile)) {
        return $null
    }

    try {
        $processId = [int](Get-Content -Path $PidFile -Raw).Trim()

        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue

        if ($null -eq $process) {
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            return $null
        }

        return $process
    }
    catch {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return $null
    }
}

function Start-App {

    if (-not (Test-Path $Python)) {
        throw "Python virtual environment not found: $Python"
    }

    $existingProcess = Get-AppProcess

    if ($null -ne $existingProcess) {
        Write-Host "Application is already running (PID $($existingProcess.Id))." -ForegroundColor Yellow
        Write-Host "Dashboard: $Url"
        return
    }

    Write-Host "Starting PEGA application..." -ForegroundColor Cyan

    $process = Start-Process `
        -FilePath $Python `
        -ArgumentList @(
            "-m",
            "uvicorn",
            "webapp.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "$Port"
        ) `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError "$LogFile.err" `
        -PassThru

    Set-Content -Path $PidFile -Value $process.Id -NoNewline

    Start-Sleep -Seconds 2

    $runningProcess = Get-Process -Id $process.Id -ErrorAction SilentlyContinue

    if ($null -eq $runningProcess) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        throw "Application failed to start. Check $LogFile and $LogFile.err"
    }

    Write-Host "Application started successfully!" -ForegroundColor Green
    Write-Host "PID: $($process.Id)"
    Write-Host "Dashboard: $Url"
    Write-Host "Logs: $LogFile"
}

function Stop-App {

    $process = Get-AppProcess

    if ($null -eq $process) {
        Write-Host "Application is not running." -ForegroundColor Yellow
        return
    }

    Write-Host "Stopping application (PID $($process.Id))..." -ForegroundColor Cyan

    Stop-Process -Id $process.Id -Force

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue

    Write-Host "Application stopped successfully." -ForegroundColor Green
}

function Show-Status {

    $process = Get-AppProcess

    if ($null -eq $process) {
        Write-Host "Application is stopped." -ForegroundColor Red
        return
    }

    Write-Host "Application is running." -ForegroundColor Green
    Write-Host "PID: $($process.Id)"
    Write-Host "Dashboard: $Url"
}

switch ($Action) {
    "Start"  { Start-App }
    "Stop"   { Stop-App }
    "Status" { Show-Status }
}
