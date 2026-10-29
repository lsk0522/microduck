@echo off
rem Shared environment for Microduck .bat files. Do not run directly.
chcp 65001 >nul
for %%I in ("%~dp0..") do set "MD_ROOT=%%~fI"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
cd /d "%MD_ROOT%"
where uv >nul 2>nul
if errorlevel 1 (
  echo [!] uv is not installed yet. Run "bat\00_setup.bat" first.
  exit /b 1
)
if not exist "%MD_ROOT%\.venv" (
  echo [!] Python environment not found. Run "bat\00_setup.bat" first.
  exit /b 1
)
exit /b 0
