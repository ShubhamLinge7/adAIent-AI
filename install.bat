@echo off
REM adAIent Installation Script - Batch Version
REM Automatically installs prerequisites including Python and Ollama

setlocal enabledelayedexpansion
set INSTALL_PATH=C:\adAIent

echo.
echo ============================================================
echo  adAIent - Industrial Troubleshooting Assistant Installer
echo ============================================================
echo.

REM Check admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This installer must be run as Administrator!
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo [1/7] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Downloading Python 3.11...
    
    REM Download Python (requires internet connection)
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%TEMP%\python-installer.exe'}" 2>nul
    
    if exist "%TEMP%\python-installer.exe" (
        echo Installing Python...
        "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        timeout /t 5
        python --version >nul 2>&1
        if !errorlevel! equ 0 (
            echo Python installed successfully
        ) else (
            echo WARNING: Python installation failed
            echo Please install Python manually from https://python.org
            pause
            exit /b 1
        )
    ) else (
        echo WARNING: Could not download Python
        echo Please install Python 3.10+ manually from https://python.org
        pause
        exit /b 1
    )
)

echo [2/7] Checking Ollama installation...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama not found. Downloading Ollama...
    
    REM Download Ollama
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://ollama.ai/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe'}" 2>nul
    
    if exist "%TEMP%\OllamaSetup.exe" (
        echo Installing Ollama...
        "%TEMP%\OllamaSetup.exe" /quiet
        timeout /t 10
        echo Ollama installed
    ) else (
        echo WARNING: Could not download Ollama automatically
        echo Please install Ollama manually from https://ollama.ai
        set /p CONTINUE="Continue anyway? (y/n): "
        if /i not "!CONTINUE!"=="y" exit /b 1
    )
)

echo [3/7] Ensuring llama3.2:3b model is available...
ollama list 2>nul | findstr "llama3.2:3b" >nul
if %errorlevel% neq 0 (
    echo Downloading llama3.2:3b model (^~2GB, may take 5-10 minutes)...
    ollama pull llama3.2:3b
) else (
    echo Model llama3.2:3b already available
)

echo [4/7] Creating installation directory...
if exist "%INSTALL_PATH%" (
    set /p OVERWRITE="Directory exists. Overwrite? (y/n): "
    if /i not "!OVERWRITE!"=="y" (
        echo Installation cancelled.
        exit /b 0
    )
    rmdir /s /q "%INSTALL_PATH%"
)

mkdir "%INSTALL_PATH%"
xcopy . "%INSTALL_PATH%\" /e /y /q >nul
echo Installation directory: %INSTALL_PATH%

echo [5/7] Installing Python dependencies...
cd /d "%INSTALL_PATH%"
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
python -m pip install -r requirements.txt >nul

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [6/7] Creating directories...
mkdir "%INSTALL_PATH%\logs" 2>nul
mkdir "%INSTALL_PATH%\data\manuals" 2>nul
mkdir "%INSTALL_PATH%\data\indexes" 2>nul
echo Directories created

echo [7/7] Setting up Windows Service...
python -m pip install nssm >nul 2>&1

echo Creating service 'adAIent'...

REM Use absolute path to python
for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%i

REM Create service
nssm install adAIent "%PYTHON_EXE%" "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" >nul 2>&1
nssm set adAIent AppDirectory "%INSTALL_PATH%" >nul 2>&1
nssm set adAIent AppStdout "%INSTALL_PATH%\logs\stdout.log" >nul 2>&1
nssm set adAIent AppStderr "%INSTALL_PATH%\logs\stderr.log" >nul 2>&1
nssm start adAIent >nul 2>&1

echo Windows Service created

echo Configuring Windows Firewall...
netsh advfirewall firewall add rule name="adAIent Port 8000" dir=in action=allow protocol=tcp localport=8000 >nul 2>&1
echo Firewall rule added

echo.
echo ============================================================
echo  Installation Complete!
echo ============================================================
echo.
echo Access adAIent at:
echo   Local:    http://127.0.0.1:8000
echo   Network:  http://!COMPUTERNAME!:8000
echo.
echo First Login:
echo   Username: master
echo   Password: Master@Adient2026
echo.
echo Installation Path: %INSTALL_PATH%
echo Ollama Service: Must be running (started automatically)
echo Note: Allow 30-60 seconds for server to fully start
echo.
pause
