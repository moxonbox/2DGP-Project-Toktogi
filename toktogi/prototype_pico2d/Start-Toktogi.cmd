@echo off
setlocal
set "TOKTOGI_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%TOKTOGI_PYTHON%" (
  echo Missing .venv. Follow README.md installation steps.
  pause
  exit /b 1
)
"%TOKTOGI_PYTHON%" "%~dp0main.py" %*
set "TOKTOGI_EXIT=%errorlevel%"
if not "%TOKTOGI_EXIT%"=="0" pause
exit /b %TOKTOGI_EXIT%
