@echo off
REM adAIent Uninstall Script

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo adAIent - Uninstaller
echo ============================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This uninstaller must be run as Administrator!
    pause
    exit /b 1
)

set INSTALL_PATH=C:\adAIent

echo Removing Windows Service...
where nssm >nul 2>&1
if not errorlevel 1 (
    nssm stop adAIent >nul 2>&1
    nssm remove adAIent confirm >nul 2>&1
    echo Service removed.
)

echo Removing Firewall rule...
netsh advfirewall firewall delete rule name="adAIent Port 8000" >nul 2>&1

echo Removing installation directory...
if exist "%INSTALL_PATH%" (
    rmdir /s /q "%INSTALL_PATH%"
    echo Installation directory removed.
)

echo.
echo ============================================================
echo Uninstallation Complete!
echo ============================================================
echo.
pause
