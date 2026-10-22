# 사내 LAN 웹서비스 3개를 Windows 시작 시 자동 실행되도록 작업 스케줄러에 등록합니다.
# 반드시 "관리자 권한으로 실행"한 PowerShell에서 실행해주세요.
# 이미 등록된 작업은 -Force로 덮어써서 다시 등록되므로, 여러 번 실행해도 안전합니다.

$ErrorActionPreference = "Stop"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "이 스크립트는 관리자 권한이 필요합니다." -ForegroundColor Red
    Write-Host "PowerShell을 마우스 우클릭 -> '관리자 권한으로 실행' 한 뒤, 이 스크립트를 다시 실행해주세요." -ForegroundColor Yellow
    exit 1
}

$services = @(
    @{
        Name = "MK_WorkLog_WebServer"
        Bat  = "E:\이재호\AI프로젝트\개발ing\MK 업무기록 프로그램 v1.1.1\webapp\run_server.bat"
        Dir  = "E:\이재호\AI프로젝트\개발ing\MK 업무기록 프로그램 v1.1.1\webapp"
        Port = 8003
    },
    @{
        Name = "DesignDocs_Automation_Hub_WebServer"
        Bat  = "E:\이재호\AI프로젝트\개발ing\설계 서류업무 자동화\webapp\run_server.bat"
        Dir  = "E:\이재호\AI프로젝트\개발ing\설계 서류업무 자동화\webapp"
        Port = 8001
    },
    @{
        Name = "Formtec_LabelDesigner_WebServer"
        Bat  = "E:\이재호\AI프로젝트\개발ing\폼텍 라벨지 디자인 편집기 v1.1.0\run_server.bat"
        Dir  = "E:\이재호\AI프로젝트\개발ing\폼텍 라벨지 디자인 편집기 v1.1.0"
        Port = 8002
    },
    @{
        Name = "FileTree_Generator_WebServer"
        Bat  = "E:\이재호\AI프로젝트\개발ing\파일트리 자동생성기 v1.1.0\WEBAPP\run_server.bat"
        Dir  = "E:\이재호\AI프로젝트\개발ing\파일트리 자동생성기 v1.1.0\WEBAPP"
        Port = 8004
    },
    @{
        Name = "LabelSafetySign_Design_WebServer"
        Bat  = "E:\이재호\AI프로젝트\개발ing\라벨 및 안전표지 디자인\webapp\run_server.bat"
        Dir  = "E:\이재호\AI프로젝트\개발ing\라벨 및 안전표지 디자인\webapp"
        Port = 8005
    },
    @{
        Name = "StorageManager_WebServer"
        Bat  = "E:\이재호\AI프로젝트\개발ing\저장공간 관리 프로그램 v1.1.0\webapp\run_server.bat"
        Dir  = "E:\이재호\AI프로젝트\개발ing\저장공간 관리 프로그램 v1.1.0\webapp"
        Port = 8006
    }
)

foreach ($svc in $services) {
    Write-Host "등록 중: $($svc.Name) (포트 $($svc.Port)) ..." -ForegroundColor Cyan

    $action = New-ScheduledTaskAction -Execute $svc.Bat -WorkingDirectory $svc.Dir
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit (New-TimeSpan -Days 0)

    Register-ScheduledTask -TaskName $svc.Name -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings -Force | Out-Null

    Write-Host "  -> 등록 완료" -ForegroundColor Green
}

Write-Host ""
Write-Host "모두 등록되었습니다. 지금 바로 켜려면 아래 명령을 실행하세요:" -ForegroundColor Green
foreach ($svc in $services) {
    Write-Host "  Start-ScheduledTask -TaskName '$($svc.Name)'"
}

