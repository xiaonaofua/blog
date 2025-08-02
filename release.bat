@echo off
echo Starting blog deployment...
echo.

echo Building static site...
python build.py
if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo Adding files to git...
git add .

echo Committing changes...
git commit -m "new update"

echo Pushing to GitHub...
git push origin main

echo.
echo Deployment complete!
pause