# MK 업무기록 웹서버를 Windows 시작 시 자동 실행되도록 작업 스케줄러에 등록합니다.
# 반드시 "관리자 권한으로 실행"한 PowerShell에서 실행해주세요.

$ErrorActionPreference = "Stop"

$taskName = "MK_WorkLog_WebServer"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $scriptDir "run_server.bat"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "이 스크립트는 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host "PowerShell을 마우스 우클릭 -> '관리자 권한으로 실행' 한 뒤, 이 스크립트를 다시 실행해주세요." -ForegroundColor Yellow
    exit 1
}

$action = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $scriptDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "등록 완료: '$taskName' 작업이 Windows 시작 시 자동 실행됩니다." -ForegroundColor Green
Write-Host "지금 바로 테스트하려면: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Cyan
