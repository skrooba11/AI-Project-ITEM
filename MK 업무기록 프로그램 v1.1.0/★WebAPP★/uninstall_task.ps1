# MK 업무기록 웹서버 자동 시작 작업을 제거합니다. 관리자 권한으로 실행해주세요.
$ErrorActionPreference = "Stop"
$taskName = "MK_WorkLog_WebServer"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "이 스크립트는 관리자 권한이 필요합니다." -ForegroundColor Red
    exit 1
}

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
Write-Host "제거 완료: '$taskName' 작업이 삭제되었습니다." -ForegroundColor Green
