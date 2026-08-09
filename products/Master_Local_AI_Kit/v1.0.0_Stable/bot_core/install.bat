@echo off
title Antigravity Telegram Bot - Installer
color 0A
echo.
echo  ================================================
echo   Antigravity Telegram Bot - Instalasi Dependensi
echo  ================================================
echo.

:: Cek Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan!
    echo         Download dari https://python.org
    pause
    exit /b 1
)

echo [OK] Python ditemukan
echo.
echo [*] Menginstall python-telegram-bot...
pip install python-telegram-bot --upgrade

if errorlevel 1 (
    echo.
    echo [ERROR] Instalasi gagal. Coba jalankan sebagai Administrator.
    pause
    exit /b 1
)

echo.
echo  ================================================
echo   [SUKSES] Instalasi selesai!
echo  ================================================
echo.
echo  Langkah selanjutnya:
echo  1. Buka config.json dengan Notepad
echo  2. Isi "bot_token" dengan token dari @BotFather
echo  3. (Opsional) Isi "allowed_users" dengan Telegram ID kamu
echo  4. Jalankan run_bot.bat untuk memulai bot
echo.
pause
