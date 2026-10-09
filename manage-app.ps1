[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("Start", "Stop", "Status")]
    [string]$Action = "Start",

    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$PidFile = Join-Path $ProjectRoot ".pega-app.pid"
$Url = "http://127.0.0.1:$Port/"

function Get-AppProcess {
    if (-not (Test-Path $PidFile)) {
        return $null
    }

    $processId = [int](Get-Content -Path $PidFile -Raw).Trim()
    try {
        return Get-Process -Id $processId -ErrorAction Stop
    }
    catch [System.ArgumentException] {
        Remove-Item -Path $PidFile -Force
        return $null
    }
}

function Start-App {
    if (-not (Test-Path $Python)) {
        throw "Virtual environment Python was not found at $Python"
    }

    $existingProcess = Get-AppProcess
    if ($null -ne $existingProcess) {
        Write-Host "Application is already running (PID $($existingProcess.Id))."
        Write-Host "Dashboard: $Url"
        return
    }

    Write-Host "Starting PEGA application..."
    Write-Host "Console output from uvicorn will appear below. Press Ctrl+C to stop this console."

    $process = Start-Process `
        -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "webapp.main:app", "--host", "127.0.0.1", "--port", "$Port") `
        -WorkingDirectory $ProjectRoot `
        -NoNewWindow `
        -PassThru

    Set-Content -Path $PidFile -Value $process.Id -NoNewline
    Write-Host "Application started (PID $($process.Id))."
    Write-Host "Dashboard: $Url"
}

function Stop-App {
    $process = Get-AppProcess
    if ($null -eq $process) {
        Write-Host "Application is not running."
        return
    }

    Write-Host "Stopping application (PID $($process.Id))..."
    Stop-Process -Id $process.Id
    Remove-Item -Path $PidFile -Force
    Write-Host "Application stopped."
}

function Show-Status {
    $process = Get-AppProcess
    if ($null -eq $process) {
        Write-Host "Application is stopped."
        return
    }

    Write-Host "Application is running (PID $($process.Id))."
    Write-Host "Dashboard: $Url"
}

switch ($Action) {
    "Start"  { Start-App }
    "Stop"   { Stop-App }
    "Status" { Show-Status }
}
.\manage-app.ps1 -Action Start
.\manage-app.ps1 -Action Stop
.\manage-app.ps1 -Action Status