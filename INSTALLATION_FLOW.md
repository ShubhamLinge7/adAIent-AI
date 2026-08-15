# Installation Flow Diagram

## Complete Automatic Installation Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    Start Installation                           │
│              (Run install.ps1 as Administrator)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │  Check Python Installation      │
        └────────────────┬────────────────┘
                         │
         ┌───────────────┴────────────────┐
         │                                │
    Python Found?                    Python NOT Found?
         │                                │
         │                                ▼
         │                    ┌──────────────────────┐
         │                    │ Download Python 3.11 │
         │                    │ from python.org      │
         │                    │ (~100MB, 5 min)      │
         │                    └──────────────────────┘
         │                                │
         ├────────────────┬───────────────┤
         │                │
         ▼                ▼
      ┌──────────────────────────────┐
      │  Check Ollama Installation   │
      └────────────────┬─────────────┘
                       │
       ┌───────────────┴─────────────┐
       │                             │
   Ollama Found?              Ollama NOT Found?
       │                             │
       │                             ▼
       │               ┌─────────────────────┐
       │               │ Download Ollama     │
       │               │ from ollama.ai      │
       │               │ (~500MB, 10 min)    │
       │               └─────────────────────┘
       │                             │
       ├─────────────┬──────────────┤
       │             │
       ▼             ▼
    ┌────────────────────────────┐
    │ Verify LLM Model Available │
    │   (llama3.2:3b)            │
    └────────────────┬───────────┘
                     │
     ┌───────────────┴────────────┐
     │                            │
  Model Available?          Model NOT Available?
     │                            │
     │                            ▼
     │            ┌──────────────────────────┐
     │            │ Pull Model from Ollama   │
     │            │ ollama pull llama3.2:3b  │
     │            │ (~2GB, 10-15 min)        │
     │            └──────────────────────────┘
     │                            │
     ├─────────────┬──────────────┤
     │             │
     ▼             ▼
  ┌──────────────────────────────────┐
  │  Create Installation Directory   │
  │  (C:\adAIent by default)         │
  │  Copy project files              │
  └────────────────┬─────────────────┘
                   │
                   ▼
  ┌──────────────────────────────────┐
  │ Install Python Dependencies      │
  │ pip install -r requirements.txt  │
  │ (~5 min)                         │
  └────────────────┬─────────────────┘
                   │
                   ▼
  ┌──────────────────────────────────┐
  │ Create Data Directories          │
  │ - C:\adAIent\logs                │
  │ - C:\adAIent\data\manuals        │
  │ - C:\adAIent\data\indexes        │
  └────────────────┬─────────────────┘
                   │
                   ▼
  ┌──────────────────────────────────┐
  │ Setup Windows Service            │
  │ - Install NSSM                   │
  │ - Create 'adAIent' service       │
  │ - Set auto-start on boot         │
  │ - Set auto-restart on crash      │
  │ - Start service                  │
  └────────────────┬─────────────────┘
                   │
                   ▼
  ┌──────────────────────────────────┐
  │ Configure Windows Firewall       │
  │ - Add rule for port 8000         │
  │ - Allow all profiles             │
  └────────────────┬─────────────────┘
                   │
                   ▼
  ┌──────────────────────────────────┐
  │  ✅ INSTALLATION COMPLETE!       │
  │                                  │
   │  Access: http://localhost:8000   │
   │  Use superadmin creds (shared)   │
   │  Rotate password immediately     │
  └──────────────────────────────────┘
```

---

## Installation Timeline (First Run)

```
Time    Activity                                      Duration
────────────────────────────────────────────────────────────
0:00    Start installer                                    -
0:05    Python download (if needed)                        5 min
0:10    Python installation (if needed)                    5 min
0:20    Ollama download (if needed)                       10 min
0:30    LLM model download (if needed)                   10 min
0:40    Python dependencies installation                   5 min
0:45    Create directories                                1 min
0:46    Setup Windows Service                             2 min
0:48    Configure Firewall                                1 min
0:50    ✅ COMPLETE                                      Total: 50 min

Note: Times vary based on:
- Internet speed (model download is slowest)
- Disk speed
- What's already installed
```

---

## Installation Timeline (Subsequent Run)

```
Time    Activity                                      Duration
────────────────────────────────────────────────────────────
0:00    Start installer                                    -
0:00    Python found (skip)                               -
0:00    Ollama found (skip)                               -
0:00    Model found (skip)                                -
0:05    Python dependencies                               5 min
0:06    Create directories                                1 min
0:07    Setup Windows Service                             2 min
0:09    Configure Firewall                                1 min
0:10    ✅ COMPLETE                                      Total: 10 min
```

---

## What Gets Installed Where

```
Directory Structure After Installation:

C:\adAIent\                          ← Installation root
├── app/                             ← Application code
│   ├── auth/                        ← Authentication module
│   ├── api/                         ← API endpoints
│   ├── rag/                         ← RAG (Retrieval-Augmented Generation)
│   └── main.py                      ← FastAPI application
├── data/
│   ├── manuals/                     ← User uploads manuals here
│   └── indexes/                     ← FAISS index files (auto-generated)
├── logs/                            ← Application logs (auto-created)
├── config.py                        ← Configuration settings
├── requirements.txt                 ← Python dependencies
├── admin.html                       ← Admin dashboard
├── index_adaient.html               ← Chat interface
├── login.html                       ← Login page
└── [database files]                 ← SQLite database (auto-created)

Windows Registry:
├── HKLM\SYSTEM\CurrentControlSet\Services\adAIent
│   └── Service parameters (port, startup, restart policy)

Firewall:
├── Rule: "adAIent Port 8000"
│   └── Allow inbound TCP port 8000
```

---

## Pre-Installation vs Post-Installation

### Before Installation
```
Company Server (Clean)
├── Windows 10/11 or Server 2016+
├── Administrator access
├── 10GB free disk space
└── Internet connection
```

### After Installation
```
Company Server (Ready to Use)
├── Python 3.11
├── Ollama (service running)
├── llama3.2:3b model (~2GB)
├── adAIent application (C:\adAIent\)
├── Windows Service (auto-start enabled)
├── Firewall rule (port 8000 open)
├── SQLite database (auto-created)
├── Superadmin account ready (credentials shared out-of-band)
└── Application ready at http://localhost:8000
```

---

## Error Recovery During Installation

```
┌─ Python Download Fails
│  → Installer prompts user
│  → Option 1: Retry (installer retries)
│  → Option 2: Manual install (user installs from python.org)
│  → Option 3: Cancel
│
├─ Ollama Download Fails
│  → Installer prompts user
│  → Option 1: Retry
│  → Option 2: Manual install
│  → Option 3: Continue anyway (may fail later)
│
├─ Model Download Fails
│  → Installer prompts user
│  → Option 1: Retry
│  → Option 2: Model will pull on app startup
│
├─ Dependency Installation Fails
│  → Installer stops with error
│  → Check: Internet connection, disk space, permissions
│  → Retry: Run installer again
│
└─ Service Creation Fails
   → Check: Administrator privileges
   → Check: Windows version (must be Server 2016+)
   → Retry: Run installer as Administrator
```

---

## One-Liner Reference

**To remember:**
```
Run installer → Wait 30-40 min → Access http://localhost:8000
Everything else is automatic!
```

**That's it!** 🎯
