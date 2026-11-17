@echo off
setlocal
set "TOKTOGI_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%TOKTOGI_PYTHON%" (
  echo Missing .venv. Follow README.md installation steps.
  exit /b 1
)
"%TOKTOGI_PYTHON%" "%~dp0main.py" %*
exit /b %errorlevel%
