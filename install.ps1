# adAIent Installation Script - PowerShell Version
# Automatically installs all prerequisites including Python and Ollama

param(
    [string]$InstallPath = "C:\adAIent"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "adAIent - Industrial Troubleshooting Assistant Installer" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = [Security.Principal.WindowsIdentity]::GetCurrent() | `
    ForEach-Object { [Security.Principal.WindowsPrincipal]::new($_).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) }

if (-not $isAdmin) {
    Write-Host "ERROR: This installer must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click and select 'Run as Administrator with PowerShell'" -ForegroundColor Red
    pause
    exit 1
}

# Step 1: Check/Install Python
Write-Host "[1/7] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Installing Python 3.11..." -ForegroundColor Yellow
    
    # Download Python installer
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    Write-Host "Downloading Python 3.11.7..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -ErrorAction Stop
        
        Write-Host "Installing Python..." -ForegroundColor Cyan
        & $pythonInstaller /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 | Out-Null
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Start-Sleep -Seconds 5
        $pythonVersion = python --version 2>&1
        Write-Host "Python installed: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Could not download Python automatically" -ForegroundColor Red
        Write-Host "Please install Python 3.10+ manually from https://python.org" -ForegroundColor Red
        Write-Host "Make sure to check 'Add Python to PATH'" -ForegroundColor Red
        pause
        exit 1
    }
}

# Step 2: Check/Install Ollama
Write-Host "[2/7] Checking Ollama installation..." -ForegroundColor Yellow
try {
    $ollamaVersion = ollama --version 2>&1
    Write-Host "Found: $ollamaVersion" -ForegroundColor Green
} catch {
    Write-Host "Ollama not found. Installing Ollama..." -ForegroundColor Yellow
    
    $ollamaUrl = "https://ollama.ai/download/OllamaSetup.exe"
    $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
    
    Write-Host "Downloading Ollama..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaInstaller -ErrorAction Stop
        
        Write-Host "Installing Ollama..." -ForegroundColor Cyan
        & $ollamaInstaller /quiet | Out-Null
        
        Start-Sleep -Seconds 10
        
        # Add Ollama to PATH if needed
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Host "Ollama installed" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Could not download Ollama automatically" -ForegroundColor Yellow
        Write-Host "Please install Ollama manually from https://ollama.ai" -ForegroundColor Yellow
        Write-Host "Or skip if Ollama is already running" -ForegroundColor Yellow
        
        $skipOllama = Read-Host "Continue anyway? (y/n)"
        if ($skipOllama -ne 'y') {
            exit 1
        }
    }
}

# Step 3: Pull required LLM model
Write-Host "[3/7] Ensuring llama3.2:3b model is available..." -ForegroundColor Yellow
try {
    $modelList = ollama list 2>&1
    if ($modelList -like "*llama3.2:3b*") {
        Write-Host "Model llama3.2:3b already available" -ForegroundColor Green
    } else {
        Write-Host "Downloading llama3.2:3b model (~2GB)..." -ForegroundColor Cyan
        Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
        ollama pull llama3.2:3b
        Write-Host "Model downloaded successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Could not verify/download LLM model" -ForegroundColor Yellow
    Write-Host "Model will be pulled when server starts" -ForegroundColor Yellow
}

# Step 4: Create installation directory
Write-Host "[4/7] Creating installation directory..." -ForegroundColor Yellow
if (Test-Path $InstallPath) {
    $overwrite = Read-Host "Directory exists. Overwrite? (y/n)"
    if ($overwrite -ne 'y') {
        Write-Host "Installation cancelled." -ForegroundColor Yellow
        exit 0
    }
    Remove-Item -Recurse -Force $InstallPath
}

New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
Copy-Item -Path ".\*" -Destination $InstallPath -Recurse -Force
Write-Host "Installation directory: $InstallPath" -ForegroundColor Green

# Step 5: Install Python dependencies
Write-Host "[5/7] Installing Python dependencies..." -ForegroundColor Yellow
Push-Location $InstallPath
python -m pip install --upgrade pip setuptools wheel | Out-Null
python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "Dependencies installed successfully" -ForegroundColor Green

# Step 6: Create logs directory
Write-Host "[6/7] Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$InstallPath\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "$InstallPath\data\manuals" -Force | Out-Null
New-Item -ItemType Directory -Path "$InstallPath\data\indexes" -Force | Out-Null
Write-Host "Directories created" -ForegroundColor Green

# Step 7: Install NSSM and create Windows Service
Write-Host "[7/7] Setting up Windows Service..." -ForegroundColor Yellow
python -m pip install nssm | Out-Null

$nssmPath = python -c "import nssm; import os; print(os.path.dirname(nssm.__file__))" 2>$null
if ($nssmPath) {
    $nssmExe = Join-Path $nssmPath "nssm.exe"
    if (Test-Path $nssmExe) {
        & $nssmExe install adAIent python "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" | Out-Null
        & $nssmExe set adAIent AppDirectory $InstallPath | Out-Null
        & $nssmExe set adAIent AppStdout "$InstallPath\logs\stdout.log" | Out-Null
        & $nssmExe set adAIent AppStderr "$InstallPath\logs\stderr.log" | Out-Null
        & $nssmExe start adAIent | Out-Null
        Write-Host "Windows Service 'adAIent' created and started" -ForegroundColor Green
    }
}

# Configure Firewall
Write-Host "Configuring Windows Firewall..." -ForegroundColor Yellow
netsh advfirewall firewall add rule name="adAIent Port 8000" `
    dir=in action=allow protocol=tcp localport=8000 | Out-Null
Write-Host "Firewall rule added" -ForegroundColor Green

Pop-Location

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access adAIent at:" -ForegroundColor Yellow
Write-Host "  Local:    http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "  Network:  http://$(hostname):8000" -ForegroundColor Green
Write-Host ""
Write-Host "First Login:" -ForegroundColor Yellow
Write-Host "  Username: master" -ForegroundColor Green
Write-Host "  Password: Master@Adient2026" -ForegroundColor Green
Write-Host ""
Write-Host "Installation Path: $InstallPath" -ForegroundColor Yellow
Write-Host "Ollama Service: Must be running (started automatically)" -ForegroundColor Yellow
Write-Host "Note: Allow 30-60 seconds for server to fully start" -ForegroundColor Yellow
Write-Host ""
pause
