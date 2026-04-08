@echo off
setlocal

set PYTHON=%~dp0..\venv\Scripts\python.exe
set MAIN=%~dp0..\main.py

"%PYTHON%" "%MAIN%" %*
