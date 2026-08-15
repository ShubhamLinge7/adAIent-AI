## Installation Summary - What Gets Installed Automatically

### ✅ FULLY AUTOMATIC

Your company server **does NOT need to have anything pre-installed**. The installer handles everything:

```
Installation Process Flow:
┌─────────────────────────────────────────────────────────────┐
│  1. Run install.ps1 (or install.bat)                       │
│     ↓                                                       │
│  2. Check Python - if missing → auto-download & install    │
│     ↓                                                       │
│  3. Check Ollama - if missing → auto-download & install    │
│     ↓                                                       │
│  4. Verify llama3.2:3b model - if missing → auto-pull      │
│     ↓                                                       │
│  5. Install Python packages (pip)                          │
│     ↓                                                       │
│  6. Create Windows Service (auto-start)                    │
│     ↓                                                       │
│  7. Open browser → http://localhost:8000                   │
│     ↓                                                       │
│  ✅ DONE! All automatic. No manual steps needed.           │
└─────────────────────────────────────────────────────────────┘
```

---

### Installation Checklist

**Before Installation:**
- [ ] Extract package to destination folder
- [ ] Have internet connection on target server
- [ ] Have 10GB free disk space
- [ ] Have Administrator access

**During Installation:**
- [ ] Run installer as Administrator
- [ ] Wait for automatic downloads (30-40 minutes)
- [ ] No manual steps required
- [ ] No configuration needed
- [ ] No prerequisites to install separately

**After Installation:**
- [ ] Open http://localhost:8000
- [ ] Use the superadmin credentials shared out-of-band
- [ ] Change the password immediately, then start using it

---

### What You DON'T Need to Do

❌ Don't need to:
- Install Python separately
- Install Ollama separately
- Download LLM model separately
- Configure anything manually
- Set up database manually
- Set up encryption keys manually
- Create Windows Service manually

---

### Time Breakdown

| Task | Duration | Notes |
|------|----------|-------|
| Python download & install | 5 min | Only if not installed |
| Ollama download & install | 10 min | Only if not installed |
| LLM Model download (~2GB) | 10-15 min | Only first time |
| Python dependencies | 5 min | Always |
| Windows Service setup | 2 min | Always |
| **Total (First Run)** | **30-40 min** | Subsequent installs: 5 min |

---

### System Requirements

- **OS**: Windows 10, 11, or Server 2016+
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 10GB free (5GB after installation)
- **Internet**: Yes (for downloads)
- **Admin Access**: Yes (required)

---

### FAQ

**Q: What if we don't have internet on the server?**
A: Pre-install on a machine WITH internet, then copy the folder. Or install Python and Ollama separately, then run the installer.

**Q: Can we use a different LLM model?**
A: Yes, after installation edit `config.py` and change OLLAMA_MODEL to any model installed in Ollama.

**Q: What if Python/Ollama is already installed?**
A: The installer detects this and skips those steps. Installation time: ~5 minutes.

**Q: Does it auto-start after reboot?**
A: Yes! Windows Service auto-starts adAIent on every boot.

**Q: How do I stop/start the service?**
```cmd
# Stop
net stop adAIent

# Start
net start adAIent

# Check status
sc query adAIent
```

**Q: What if the installer fails?**
A: Check INSTALLATION_GUIDE.md Troubleshooting section. Most issues are due to:
1. Not running as Administrator
2. No internet connection
3. Disk space full

---

### Next Steps After Installation

1. **First Login**
   - URL: http://localhost:8000
   - Use the superadmin credentials shared out-of-band
   - Change the password immediately

2. **Create User Accounts**
   - Login with the superadmin account after rotation
   - Go to Admin Dashboard
   - Add user accounts with appropriate roles

3. **Upload Manuals**
   - Go to "Upload Manuals" section
   - Upload equipment/system manuals
   - System automatically indexes them

4. **Test Troubleshooting**
   - Start new chat
   - Ask questions about uploaded manuals
   - System searches indexed manuals for answers

---

### Support

If you encounter issues:

1. Check **INSTALLATION_GUIDE.md** - Troubleshooting section
2. Check **PREREQUISITES.md** - Detailed prerequisite info
3. Check Windows Event Viewer for service errors
4. Review `C:\adAIent\logs\` for application logs

---

**Bottom Line**: 
🎯 The installer is **fully automatic**. No brain required after you press "Install"!
