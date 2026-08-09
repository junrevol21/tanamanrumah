@echo off
echo ========================================================
echo   Pemasangan Antigravity Telegram Bot ke Task Scheduler
echo ========================================================
echo.

set TASK_NAME=AntigravityTelegramBot
set VBS_PATH=C:\Users\ASUS\.gemini\antigravity\telegram_bot\run_bot_background.vbs

echo [1/2] Membuat tugas di Task Scheduler Windows (At Startup / Logon)...
schtasks /create /tn "%TASK_NAME%" /tr "wscript.exe \"%VBS_PATH%\"" /sc ONLOGON /rl LIMITED /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUKSES] Task Scheduler '%TASK_NAME%' berhasil terpasang!
    echo Bot akan otomatis menyala di background setiap kali Windows dimula / login.
) else (
    echo.
    echo [INFO] Menjajal pendaftaran via PowerShell...
    powershell -Command "Register-ScheduledTask -TaskName '%TASK_NAME%' -Action (New-ScheduledTaskAction -Execute 'wscript.exe' -Argument '\"%VBS_PATH%\"') -Trigger (New-ScheduledTaskTrigger -AtLogOn) -Force"
)

echo.
echo [2/2] Menjalankan Bot sekarang...
schtasks /run /tn "%TASK_NAME%" 2>nul || wscript.exe "%VBS_PATH%"

echo.
echo selesai! Kamu bisa menutup jendela ini.
pause
