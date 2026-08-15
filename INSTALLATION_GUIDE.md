# adAIent v1.0 - Installation & Deployment Guide

## Quick Start (Windows)

### Option 1: Fully Automated Installation (Recommended)

**The installer automatically downloads and installs:**
- ✅ Python 3.11 (if not installed)
- ✅ Ollama (if not installed)
- ✅ LLM Model - llama3.2:3b (~2GB)
- ✅ Python dependencies via pip
- ✅ Windows Service for auto-start
- ✅ Firewall rules

**Installation Steps:**

1. Extract the package to any location
2. Right-click `install.ps1` → Select "Run with PowerShell"
3. Confirm Administrator prompt when asked
4. Wait for automatic installation (~30-40 minutes first time)
5. Open browser: `http://localhost:8000`

**Alternatively with Batch:**
```cmd
# Right-click Command Prompt as Administrator
cd C:\adAIent
install.bat
```

**First Login:**
- Superadmin credentials are provided out-of-band. Rotate them immediately after first login.

### Option 2: Manual Installation

**If you prefer manual control:**

**Prerequisites:**
- Windows 10/11 or Windows Server 2019+
- Python 3.10+ (install from python.org if needed)
- Ollama (install from ollama.ai if needed)
- Admin access

**Steps:**

```powershell
# 1. Extract project
cd C:\adAIent

# 2. Pull LLM model (if Ollama installed)
ollama pull llama3.2:3b

# 3. Create virtual environment (optional)
python -m venv venv
.\venv\Scripts\Activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Access:**
- Local: http://127.0.0.1:8000
- Network: http://<SERVER_IP>:8000

---

## Automatic Installation Details

### What Gets Installed

| Component | Auto-Install | Time | Details |
|-----------|--------------|------|---------|
| Python 3.11 | ✅ If missing | 5 min | From python.org |
| Ollama | ✅ If missing | 10 min | From ollama.ai |
| LLM Model | ✅ If missing | 10-15 min | llama3.2:3b (~2GB) |
| Dependencies | ✅ Always | 5 min | FastAPI, PyTorch, FAISS, etc. |
| Windows Service | ✅ Always | 2 min | Auto-start on boot |
| Firewall Rules | ✅ Always | 1 min | Port 8000 access |

**Total First Installation**: 30-40 minutes (with all downloads)

### Internet Requirements

The installer requires internet access to download:
- **python.org** - Python installer (100MB)
- **ollama.ai** - Ollama installer (500MB)
- **ollama.ai** - LLM model (2GB)

If your server doesn't have direct internet, see "Offline Installation" section below.

### Offline Installation

If your company server doesn't have internet:

1. **Pre-install on internet-connected machine:**
   ```powershell
   # On machine WITH internet
   .\install.ps1 -InstallPath "C:\offline-package"
   ```

2. **Copy entire folder** to company server

3. **Run on company server:**
   ```powershell
   # Copy Python/Ollama cache files (optional)
   # Or just run installer - it will skip already-installed components
   .\install.ps1
   ```

---

## First Time Setup

### Initial Login
- Use the superadmin credentials shared out-of-band by the deployment owner.
- Change the superadmin password immediately after first login.

### Emergency Recovery
- Recovery access exists for emergencies; credentials are provided out-of-band only.

### Create Company Accounts

1. Login with the superadmin account
2. Go to Admin Panel → Users
3. Click "Add User"
4. Create company-specific admin account(s)
5. Create technician accounts for operators

---

## Configuration

### Edit Settings

File: `config.py`

```python
# LLM Settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TIMEOUT = 300  # seconds

# Server Settings (default: localhost:8000)
HOST = "0.0.0.0"
PORT = 8000

# Session Settings (hardcoded in auth_service.py)
SESSION_TIMEOUT = 15  # minutes
```

### Upload Company Manuals

1. Login as admin/master
2. Go to Admin Panel → Manuals
3. Click "Upload Manual"
4. Select PDF files
5. Wait for indexing (2-5 minutes per manual)
6. Chat will become available for that manual

---

## Windows Service Management

### Start/Stop Service

```powershell
# Start
net start adAIent

# Stop
net stop adAIent

# Restart
net stop adAIent
net start adAIent

# Check status
Get-Service adAIent
```

### View Logs

```powershell
# Open logs folder
explorer C:\adAIent\logs

# Check recent errors
Get-Content "C:\adAIent\logs\stderr.log" -Tail 50
```

### Change Startup Type

```powershell
# Auto-start on boot (default)
Set-Service adAIent -StartupType Automatic

# Manual start only
Set-Service adAIent -StartupType Manual

# Disabled
Set-Service adAIent -StartupType Disabled
```

---

## Network Configuration

### Local Network Access

1. Find server IP:
```powershell
ipconfig | Select-String "IPv4"
```

2. Users access: `http://<SERVER_IP>:8000`

### DNS Setup (Optional)

**Internal DNS (adient.ai.local):**

Contact IT to create DNS record:
```
adient.ai.local  →  <SERVER_IP>
```

Users then access: `http://adient.ai.local:8000`

---

## Troubleshooting

### Port 8000 Already in Use

**Solution 1: Change Port**
```powershell
# Edit config.py
PORT = 8001  # or another free port
```

**Solution 2: Find and Kill Process**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Server Won't Start

**Check:**
```powershell
# Is Python installed?
python --version

# Is port available?
netstat -ano | findstr :8000

# Are dependencies installed?
pip list | findstr "fastapi uvicorn"

# Is Ollama running?
tasklist | findstr ollama
```

### Ollama Not Responding

```powershell
# Verify Ollama service
ollama serve

# Check available models
ollama list

# Pull model if missing
ollama pull llama3.2:3b
```

### Database Errors

```powershell
# Reset database (WARNING: Deletes all users!)
del C:\adAIent\data\auth.db

# Encryption key will auto-regenerate on next start
del C:\adAIent\data\encryption.key

# Restart server - fresh database created
```

---

## Uninstallation

### Remove adAIent

```powershell
# Run as Administrator
C:\adAIent\uninstall.bat
```

**Or manually:**

```powershell
# Stop service
net stop adAIent

# Remove service
nssm remove adAIent confirm

# Remove firewall rule
netsh advfirewall firewall delete rule name="adAIent Port 8000"

# Delete folder
rmdir /s /q C:\adAIent
```

---

## Performance Tips

### Optimize for Large Manuals

```python
# In config.py - increase retrieval chunks
TOP_K_CHUNKS = 10  # Default: 5

# Increase similarity threshold (be more selective)
MIN_SIMILARITY_SCORE = 0.5  # Default: 0.3
```

### Enable Caching

Indexes are automatically cached after first run. To rebuild:

```powershell
# Delete old indexes
rmdir /s /q C:\adAIent\data\indexes

# Restart server - rebuilds automatically
```

### Monitor Resources

```powershell
# Check CPU/Memory
Get-Process python | Select-Object Name, CPU, Memory

# Check disk space for manuals
Get-Item C:\adAIent\data | Format-List
```

---

## Security

### Change Passwords

- For admin/technician accounts: use Admin Panel → Users → password icon.
- For the superadmin account: login with the out-of-band credentials and change the password immediately.

### Master Password

- Used for recovery access if the superadmin password is lost.
- Defined in `app/auth/auth_service.py`.
- Do not document the value in any shared files; rotate it before deployment.

### Session Timeout

- **Duration:** 15 minutes of inactivity
- **Warning:** 2 minutes before logout
- **Auto-logout:** Automatic after timeout
- **Edit in:** `app/auth/auth_service.py` line 23

### Audit Logging

All user actions logged to database:
- Admin Panel → Audit Logs
- Export to CSV
- Retained for 7 days

---

## Maintenance

### Regular Tasks

**Weekly:**
- Check logs for errors
- Verify backups (manual)
- Test login access

**Monthly:**
- Review audit logs
- Verify manual indexes working
- Check disk space

**Quarterly:**
- Update system packages
- Review security settings
- Performance optimization

### Database Backup

```powershell
# Manual backup
Copy-Item "C:\adAIent\data\auth.db" "C:\adAIent\backups\auth_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"

# Automatic backup script (run via Task Scheduler)
# See backup.ps1 for details
```

---

## Support

**Common Issues:**
- See Troubleshooting section above

**Documentation:**
- `DEPLOYMENT_STATUS.md` - Implementation progress
- `config.py` - Inline configuration comments
- Server logs: `C:\adAIent\logs\`

**Contact:**
- IT Department or adAIent development team

---

## Version Information

- **Product:** adAIent v1.0
- **Last Updated:** January 24, 2026
- **Python:** 3.10+
- **Tested on:** Windows 10, Windows 11, Windows Server 2019+
