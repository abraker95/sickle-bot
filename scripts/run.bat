@echo off

if "%VIRTUAL_ENV%" == "" (
    py -m venv venv
    venv\\Scripts\\activate.bat
)

py run.py
