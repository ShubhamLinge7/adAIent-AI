# adAIent - Prerequisites & Automatic Installation

## Overview

The installer scripts have been enhanced to **automatically download and install ALL required components** if they are not already present on the system.

---

## What Gets Installed AUTOMATICALLY

### ✅ **Python 3.11** (if not installed)
- **Action**: Installer detects if Python is missing
- **Automatic Install**: Downloads Python 3.11.7 from python.org
- **Time**: ~3-5 minutes
- **Requirements**: Internet connection on target machine

### ✅ **Ollama** (if not installed)
- **Action**: Installer checks if Ollama is available
- **Automatic Install**: Downloads OllamaSetup.exe from ollama.ai
- **Time**: ~5-10 minutes
- **Includes**: Ollama runtime and service

### ✅ **LLM Model - llama3.2:3b** (if not available)
- **Action**: Installer pulls model into Ollama
- **Automatic Install**: Uses `ollama pull llama3.2:3b`
- **Time**: ~10-15 minutes (first run)
- **Size**: ~2GB
- **Cache**: Cached after first installation

### ✅ **Python Dependencies**
- **Packages**: FastAPI, Uvicorn, PyTorch, FAISS, Sentence Transformers, etc.
- **Install Method**: `pip install -r requirements.txt`
- **Time**: ~3-5 minutes
- **Location**: Stored in Python's site-packages

### ✅ **Windows Service** (NSSM)
- **Service Name**: `adAIent`
- **Features**: Auto-start, auto-restart on crash
- **Port**: 8000
- **Startup**: Automatic on Windows boot

### ✅ **Windows Firewall Rules**
- **Rule Name**: `adAIent Port 8000`
- **Effect**: Allows port 8000 access
- **Scope**: All profiles (Domain, Private, Public)

---

## What Does NOT Require Installation

- ✅ Project files (copied during install)
- ✅ Configuration files (uses defaults)
- ✅ Database (created automatically on first run)
- ✅ Encryption keys (generated automatically)

---

## Installation Steps (Automated)

### Step 1: Python Installation
```
[1/7] Checking Python installation...
→ If not found: Downloads and installs Python 3.11.7
→ If found: Skips to step 2
```

### Step 2: Ollama Installation
```
[2/7] Checking Ollama installation...
→ If not found: Downloads and installs Ollama
→ If found: Skips to step 3
```

### Step 3: LLM Model Download
```
[3/7] Ensuring llama3.2:3b model is available...
→ If not available: Pulls model (~2GB)
→ If available: Skips to step 4
```

### Steps 4-7: Project Setup
```
[4/7] Creating installation directory (C:\adAIent)
[5/7] Installing Python dependencies (pip)
[6/7] Creating data directories
[7/7] Setting up Windows Service
```

**Total Time**: 20-40 minutes (first installation with all downloads)

---

## Installation Requirements

### System Requirements
- **OS**: Windows 10 / Windows Server 2016+
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 10GB free space minimum (for model cache)
- **Internet**: Required for downloading Python, Ollama, and LLM model

### Network Requirements
- Internet access to:
  - `python.org` (Python installer)
  - `ollama.ai` (Ollama installer)
  - `huggingface.co` (Optional - for alternative models)

### Administrator Access
- **Required**: Yes
- Reason: Windows Service installation requires admin privileges
- Solution: Run installer as Administrator

---

## How to Install

### Option 1: PowerShell (Recommended)
```powershell
# Right-click PowerShell and select "Run as Administrator"
cd C:\path\to\adAIent_v1.0_clean
.\install.ps1
```

### Option 2: Batch File
```cmd
# Right-click Command Prompt and select "Run as Administrator"
cd C:\path\to\adAIent_v1.0_clean
install.bat
```

---

## Troubleshooting

### Problem: "Python installation failed"
**Solution**: 
1. Install Python manually from https://python.org
2. Select **"Add Python to PATH"** during installation
3. Run installer again

### Problem: "Ollama installation failed"
**Solution**:
1. Install Ollama manually from https://ollama.ai
2. Run installer again
3. It will detect Ollama and continue

### Problem: "Could not download Python/Ollama"
**Solution**:
1. Check internet connection
2. Try manual installation from official websites
3. Run installer again

### Problem: "Model download taking too long"
**Solution**:
1. Model download (~2GB) takes 5-15 minutes on typical internet
2. Check download speed: `ollama pull llama3.2:3b` (standalone)
3. Switch to faster internet connection if available

### Problem: "Permission denied when creating service"
**Solution**:
1. Run installer as Administrator
2. Right-click install.ps1 or install.bat
3. Select "Run as administrator"

---

## What If Ollama Is Already Running?

The installer automatically detects and reuses an existing Ollama installation:

1. **Ollama service running**: ✅ Detected automatically
2. **Model available**: ✅ Installer skips re-downloading
3. **Different port**: ⚠️ Update `config.py` OLLAMA_BASE_URL if needed
4. **Custom model**: ⚠️ Update `config.py` OLLAMA_MODEL setting

---

## Post-Installation Verification

### Check if adAIent is running
```cmd
# Command Prompt as Administrator
sc query adAIent
```

Expected output:
```
SERVICE_NAME: adAIent
        TYPE               : 10  INTERACTIVE  WIN32_OWN_PROCESS
        STATE              : 4  RUNNING
        WIN32_EXIT_CODE    : 0  (0x0)
```

### Access adAIent
- **Local**: http://127.0.0.1:8000
- **Network**: http://[HOSTNAME]:8000

### First Login
- Superadmin credentials are shared out-of-band. Rotate immediately after first login.

---

## Uninstallation

To remove adAIent:
```cmd
# Right-click Command Prompt as Administrator
cd C:\adAIent
uninstall.bat
```

This will:
- Stop the Windows Service
- Remove service registration
- Delete project files
- Remove Firewall rules
- **Note**: Does NOT remove Python or Ollama (allows reuse for other projects)

---

## Advanced Configuration

### Change Installation Path
```powershell
# PowerShell
.\install.ps1 -InstallPath "C:\Custom\Path"
```

### Change Ollama URL (if using remote Ollama)
Edit `config.py` after installation:
```python
OLLAMA_BASE_URL = "http://ollama-server:11434"  # Remote Ollama
```

### Change Model
Edit `config.py`:
```python
OLLAMA_MODEL = "mistral"  # or any other available model
```

Then restart service:
```cmd
net stop adAIent
net start adAIent
```

---

## Summary

| Component | Auto-Install | Time | Size |
|-----------|--------------|------|------|
| Python 3.11 | ✅ Yes | 5 min | 100MB |
| Ollama | ✅ Yes | 10 min | 500MB |
| LLM Model | ✅ Yes | 10 min | 2GB |
| Dependencies | ✅ Yes | 5 min | 2GB |
| Windows Service | ✅ Yes | 2 min | — |
| **TOTAL** | **✅ YES** | **30-40 min** | **~5GB** |

**Key Point**: Everything is fully automated. Just run the installer and it handles all prerequisites!
