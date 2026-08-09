@echo off
echo Menginstall Antigravity AI Bridge...
:: Setup venv, requirements, dll.
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo Setup Selesai.
