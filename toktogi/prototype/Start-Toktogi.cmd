@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
  echo Python 3.11 or later is required. See README.md.
  pause
  exit /b 1
)
python -c "import pygame; from PIL import Image, ImageMath" >nul 2>&1
if errorlevel 1 (
  echo Run: python -m pip install -r requirements.txt
  pause
  exit /b 1
)
python main.py %*
if errorlevel 1 pause
