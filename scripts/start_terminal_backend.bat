@echo off
setlocal

cd /d "%~dp0..\terminal-app"
call npm run server
