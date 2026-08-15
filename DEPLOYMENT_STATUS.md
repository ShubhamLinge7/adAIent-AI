# adAIent v1.0 - Deployment Guide

## Phase Summary
You have successfully completed:

### **Phase D: Polish Features** ✅
- [x] Auto-open chat after login
- [x] DNS setup guide (adient.ai.local)

### **Phase B: Protect & Package** 🔄
- [x] B1: Master password system (superadmin account with recovery capability)
- [x] B2: Multiple Ollama - Deferred (using single llama3.2:3b)
- [x] B3: Cleanup unnecessary files (removed 30+ MB of test data)
- [x] B4: PyInstaller packaging (In progress)
  - [x] PyInstaller installed
  - [x] Spec file created
  - [x] Clean installation folder ready
  - [ ] .exe building (takes 10-15 minutes)
  - [ ] NSIS installer creation
  - [ ] Code obfuscation

---

## Clean Installation Package Location
**Path:** `C:\adAIent_v1.0_clean\`

**Contents:**
- ✅ All app code (`app/` folder)
- ✅ All HTML UI files
- ✅ Empty data folder (will auto-create on first run)
- ✅ Empty manuals folder (company uploads their own)
- ✅ config.py with correct settings
- ✅ requirements.txt with all dependencies

**First Run Behavior:**
- Creates fresh database with superadmin and default helper accounts
- Generates encryption key
- Creates admin and demo accounts
- Ready for company deployment

---

## Master Account Details

- Superadmin account is pre-provisioned and protected (cannot be deleted)
- Default credentials are **not documented** in this repository; share them out-of-band and rotate on first login
- Recovery access exists for emergencies; credentials are handled out-of-band only

---

## Next Steps for Deployment

### **Manual Deployment (Without Installer):**
1. Copy `C:\adAIent_v1.0_clean` to company server
2. Install Python 3.10+
3. Run: `pip install -r requirements.txt`
4. Run: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Create Windows Service for auto-start

### **Automated Deployment (With Installer):**
1. Complete PyInstaller build → adAIent.exe
2. Create NSIS installer → adAIent_Setup_v1.0.exe
3. Installer handles:
   - Python bundling
   - Dependency installation
   - Windows Service registration
   - Firewall rule creation
   - Desktop shortcut

---

## Security Features Implemented

✅ **Session Management:**
- 15-minute idle timeout
- Client-side activity tracking
- 2-minute warning before logout
- Master password recovery option

✅ **Authentication:**
- Password encryption (AES-256)
- Brute-force protection (5 attempts)
- Session validation without extension
- Audit logging of all auth events

✅ **Authorization:**
- Role-based access control (SUPERADMIN, ADMIN, TECHNICIAN)
- Admin can only manage technicians
- Superadmin protected accounts
- Master account cannot be deleted

✅ **Error Handling:**
- Graceful LLM failure handling
- Retry mechanism with toast notifications
- Message restoration on error

---

## Configuration

**Edit:** `config.py`

```python
# Ollama settings
LLM_PROVIDER = "ollama"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TIMEOUT = 300

# Retrieval settings
TOP_K_CHUNKS = 5
MIN_SIMILARITY_SCORE = 0.3

# Server settings
HOST = "0.0.0.0"
PORT = 8000
```

---

## Files Deleted (Safe to Remove)

**Documentation:**
- 17 .md files (development notes)
- README.md (old version)

**Test Files:**
- Sample PDFs (4 demo manuals)
- Old database (auth.db with test users)
- Old HTML versions (index.html, index_new.html)

**Development Scripts:**
- Reindex scripts
- Startup scripts
- Migration scripts (8 .ps1/.bat files)

**Cache:**
- __pycache__/ folders
- FAISS indexes (auto-regenerated)

**Impact:** NONE - All removed files were test/development only

---

## Performance Specifications

- **Startup time:** ~30 seconds
- **First manual indexing:** ~2 minutes
- **LLM response time:** 5-30 seconds (depending on query)
- **Database size:** ~5MB
- **Typical installation size:** 
  - Without dependencies: 50MB
  - With dependencies (Python+PyTorch): 3-4GB
- **RAM requirement:** 8GB minimum, 16GB recommended

---

## Troubleshooting

**Server won't start:**
- Check port 8000 is available
- Ensure Ollama is running
- Check firewall rules

**LLM not responding:**
- Verify Ollama service running: `ollama serve`
- Check model exists: `ollama list`
- Verify model is llama3.2:3b

**Database errors:**
- Delete `data/auth.db` to reset
- Encryption key auto-regenerates

**Login fails:**
- Use superadmin credentials shared out-of-band; rotate immediately

---

## Next Implementation Phases

### **Phase C: Documentation** 📚
- Complete README.md
- Code explanation files
- Project report (academic)
- GitHub setup

### **Phase A: Deployment** 🖥️
- Installation package creation
- IT deployment guide
- Server configuration
- Testing & validation

---

**Status:** Phase B (Packaging) - 70% complete
**Last Updated:** January 24, 2026
**Version:** 1.0 (Clean Installation)
