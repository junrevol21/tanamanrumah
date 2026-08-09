@echo off
title Antigravity Telegram Bot
color 0B
echo.
echo  ================================================
echo   Antigravity Telegram Bot - Sedang Berjalan...
echo  ================================================
echo.

:: Pindah ke direktori bot
cd /d "%~dp0"

:: Cek config.json
if not exist config.json (
    echo [ERROR] config.json tidak ditemukan!
    echo         Jalankan install.bat terlebih dahulu.
    pause
    exit /b 1
)

:: Cek apakah token sudah diisi
findstr /c:"MASUKKAN_TOKEN" config.json >nul
if not errorlevel 1 (
    echo [ERROR] Bot token belum diisi di config.json!
    echo.
    echo         Langkah:
    echo         1. Buka Telegram, cari @BotFather
    echo         2. Ketik /newbot dan ikuti instruksi
    echo         3. Copy token yang diberikan
    echo         4. Buka config.json dengan Notepad
    echo         5. Ganti teks MASUKKAN_TOKEN_BOT_TELEGRAM_DISINI dengan token kamu
    echo.
    start notepad config.json
    pause
    exit /b 1
)

:: Cek python-telegram-bot
python -c "import telegram" >nul 2>&1
if errorlevel 1 (
    echo [!] python-telegram-bot belum terinstall.
    echo     Menjalankan install.bat...
    echo.
    call install.bat
)

echo [OK] Konfigurasi valid
echo [*] Menjalankan bot...
echo.
echo     Tekan Ctrl+C untuk menghentikan bot
echo.

python bot.py

echo.
echo [Bot berhenti]
pause
