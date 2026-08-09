@echo off
chcp 65001 >nul
title 🚀 Local AI Super-Agent Telegram Kit - Setup Wizard
echo.
echo ==================================================
echo    🚀 Local AI Super-Agent Telegram Kit
echo    Setup Wizard - v1.0
echo ==================================================
echo.
echo [1/4] Memeriksa Python...
python --version >nul 2>&1
if %errorlevel%==0 (echo   ✅ Python terinstall) else (echo   ❌ Python belum ada. Download di python.org dan ceklis "Add to PATH")

echo.
echo [2/4] Install library yang dibutuhkan...
python -m pip install --quiet python-telegram-bot httpx pyyaml reportlab 2>nul
echo   ✅ Library terinstall

echo.
echo [3/4] Konfigurasi token bot...
if not exist config.json (
    set /p TOKEN="   Masukkan token bot (dari @BotFather): "
    echo {"bot_token":"%TOKEN%","allowed_users":[],"default_model":"auto","agentapi_path":"","poll_interval_seconds":2} > config.json
    echo   ✅ Token disimpan
) else (
    echo   ✅ config.json sudah ada
)

echo.
echo [4/4] Aktifkan Auto-Start saat Windows boot...
schtasks /create /tn "Local_AI_Bot" /tr "\"%~dp0run_background.vbs\"" /sc onlogon /f >nul
echo   ✅ Auto-start aktif

echo.
echo ======================================
echo    🎉 SELESAI! Bot siap digunakan.
echo    Buka Telegram, chat bot kamu.
echo    Untuk start manual: python bot.py
echo ======================================
pause