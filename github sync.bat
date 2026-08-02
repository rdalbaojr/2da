@echo off
echo =========================================
echo       Starting GitHub Auto-Update...
echo =========================================

:: Ensure we are in the correct directory
cd C:\Today.ph

echo.
echo [1/3] Staging all new and modified files...
git add .

echo.
echo [2/3] Committing changes...
:: This automatically uses the current date and time as the commit message
git commit -m "Automated update on %date% at %time%"

echo.
echo [3/3] Pushing to GitHub...
git push

echo.
echo =========================================
echo        GitHub Update Complete!
echo =========================================
pause