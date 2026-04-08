@echo off
setlocal

set PYTHON=%~dp0venv\Scripts\python.exe
"%PYTHON%" -m agent %*
