@echo off
setlocal enabledelayedexpansion

echo.
echo ===============================================
echo Blog Deployment System
echo ===============================================
echo.

REM Theme selection
echo Select Blog Theme:
echo.
echo 1. Minimal Theme (Default) - Elegant modern minimal style
echo 2. Pixel Theme - Cyberpunk terminal style  
echo 3. Interactive Selection (choose during build)
echo.
echo Press 1, 2, or 3 to select theme (Default: 1 in 3 seconds)

REM Wait for single keypress with timeout
set theme_choice=1
choice /c 123 /t 3 /d 1 /n >nul
set theme_choice=%errorlevel%

REM Process theme choice
if "%theme_choice%"=="1" (
    set BLOG_THEME=minimal
    set theme_name=Minimal Theme
) else if "%theme_choice%"=="2" (
    set BLOG_THEME=pixel
    set theme_name=Pixel Theme
) else if "%theme_choice%"=="3" (
    set THEME_INTERACTIVE=true
    set theme_name=Interactive Selection
) else (
    echo Invalid option, using default theme
    set BLOG_THEME=minimal
    set theme_name=Minimal Theme
)

echo.
echo Selected: !theme_name!
echo.

echo ===============================================
echo Building static website...
echo ===============================================

REM Set environment variables and build
if defined BLOG_THEME (
    echo Using theme: !theme_name! 
    python build.py --theme !BLOG_THEME!
) else (
    echo Using interactive theme selection
    python build.py
)

if errorlevel 1 (
    echo.
    echo Build failed!
    echo Please check error messages and try again
    pause
    exit /b 1
)

echo.
echo ===============================================
echo Preparing deployment to GitHub Pages...
echo ===============================================

REM Check for changes
git status --porcelain >nul 2>&1
if errorlevel 1 (
    echo Git not initialized or error occurred
    pause
    exit /b 1
)

echo.
echo Adding files to Git...
git add .

echo.
echo Committing changes...
git commit -m "Deploy with !theme_name! theme - %date% %time%"

echo.
echo Pushing to GitHub...
git push origin main

if errorlevel 1 (
    echo.
    echo Push failed!
    echo Please check network connection and Git settings
    pause
    exit /b 1
)

echo.
echo ===============================================
echo Deployment Complete!
echo ===============================================
echo.
echo Website: https://xiaonaofua.github.io/blog
echo Theme: !theme_name!
echo Deploy Time: %date% %time%
echo.
pause