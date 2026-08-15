# 🤖 adAIent

### AI-Powered Equipment Troubleshooting Assistant

**adAIent** is an AI-powered troubleshooting assistant designed to help technicians quickly find relevant information from equipment manuals using a Retrieval-Augmented Generation (RAG) workflow.

Instead of manually searching through large technical manuals, users can interact with adAIent and receive context-aware troubleshooting assistance based on the available equipment documentation.

---

## 🎯 Problem

Technicians often need to search through large equipment manuals to identify faults, procedures, and troubleshooting information.

This can be time-consuming, especially when the required information is buried across multiple pages or documents.

**adAIent aims to reduce this search effort by combining document retrieval with an AI-powered question-answering interface.**

---

## 💡 What adAIent Does

The system provides:

* 📚 Manual-based information retrieval
* 🤖 AI-assisted troubleshooting responses
* 🔎 Semantic search across equipment documentation
* 👥 Role-based user access
* 🔐 Authentication and session management
* 📋 Audit logging
* ⏱️ Session timeout and login-attempt protection
* 🛠️ Automated Windows installation
* 🖥️ Local deployment using a Windows service

The project also includes installation, deployment, testing, and troubleshooting documentation.

---

## 🧠 How It Works

At a high level, the system follows a RAG-based workflow:

```text
                 User Question
                       │
                       ▼
              ┌─────────────────┐
              │  adAIent API    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Query Processing│
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Document /      │
              │ Semantic Search │
              └────────┬────────┘
                       │
                       ▼
              Relevant Manual
                 Information
                       │
                       ▼
              ┌─────────────────┐
              │ AI / LLM Layer  │
              └────────┬────────┘
                       │
                       ▼
              Troubleshooting
                  Response
```

The application is structured around separate API, authentication, service, model, and utility components.

---

## 🏗️ Project Structure

```text
adAIent/
│
├── app/
│   ├── api/
│   │   ├── backup.py
│   │   ├── chat.py
│   │   ├── manuals.py
│   │   └── troubleshoot.py
│   │
│   ├── auth/
│   │   ├── auth_service.py
│   │   ├── dependencies.py
│   │   ├── models.py
│   │   └── routes.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── services/
│   │   ├── indexer.py
│   │   ├── llm.py
│   │   ├── llm_providers.py
│   │   ├── retriever.py
│   │   ├── semantic_validator.py
│   │   ├── session_store.py
│   │   └── validator.py
│   │
│   └── utils/
│       └── encryption.py
│
├── data/
│   └── manuals/
│
├── admin.html
├── index_adaient.html
├── login.html
├── config.py
├── requirements.txt
├── install.ps1
├── install.bat
└── README.md
```

> Private deployment data such as authentication databases, encryption keys, manuals, and generated indexes should not be committed to source control.

---

## 🔐 Security & Access Control

adAIent includes several application-level security features:

* Role-based access control
* Superadmin, admin, and technician roles
* Authentication and session management
* 15-minute session timeout
* Login-attempt rate limiting
* Audit logging
* Encryption for sensitive stored data

The project also provides separate installation and deployment documentation for administrators.

**Never commit production credentials, authentication databases, encryption keys, or proprietary manuals to a public repository.**

---

## ⚙️ Installation

adAIent provides automated Windows installation scripts.

### PowerShell — Recommended

Run:

```powershell
.\install.ps1
```

The installer is designed to:

* Detect and install Python when required
* Detect and install Ollama when required
* Pull the required LLM model when required
* Install Python dependencies
* Create the Windows service
* Configure the required firewall settings

### Batch Installer

Alternatively:

```cmd
install.bat
```

The project also includes:

```text
uninstall.bat
```

for removing the application service and associated configuration.

---

## 🖥️ Accessing the Application

After installation, the application is available locally at:

```text
http://localhost:8000
```

Use the appropriate credentials configured for the deployment.

**Do not publish deployment credentials in this repository.**

---

## 📋 Documentation

Detailed documentation is included in the repository.

| Document                  | Purpose                                    |
| ------------------------- | ------------------------------------------ |
| `QUICK_ANSWER.md`         | Quick installation overview                |
| `INSTALLATION_GUIDE.md`   | Complete installation and deployment guide |
| `PREREQUISITES.md`        | System requirements and dependencies       |
| `INSTALLATION_FLOW.md`    | Installation process and directory flow    |
| `AUTO_INSTALL_SUMMARY.md` | Automated installation overview            |
| `TEST_REPORT.md`          | Installation and verification results      |
| `DEPLOYMENT_STATUS.md`    | Deployment and implementation summary      |

### Recommended reading paths

**New user**

```text
QUICK_ANSWER.md
        ↓
INSTALLATION_GUIDE.md
```

**Administrator**

```text
PREREQUISITES.md
        ↓
INSTALLATION_GUIDE.md
        ↓
TEST_REPORT.md
```

**Developer**

```text
README.md
   ↓
Application source code
   ↓
Installation & deployment documentation
```

---

## 🧪 Testing

The project includes a dedicated test report covering **8 installation and verification scenarios**, with the current documentation reporting all scenarios as passed.

See:

```text
TEST_REPORT.md
```

for the detailed results.

---

## 🛠️ Technology Areas

The project is built around:

* **Python**
* **FastAPI / API backend**
* **SQLite**
* **RAG-based document retrieval**
* **Semantic search**
* **LLM integration**
* **HTML/CSS/JavaScript frontend**
* **Windows PowerShell / Batch automation**
* **Windows Service deployment**

---

## 🚀 Current Version

**adAIent v1.0**

The repository currently contains the application source code together with installation, deployment, testing, and troubleshooting documentation.

---

## ⚠️ Deployment & Security Notice

This project is intended for controlled/local deployment.

Before deploying in a real environment:

1. Configure secure credentials.
2. Keep authentication databases outside source control.
3. Keep encryption keys outside source control.
4. Do not commit proprietary equipment manuals.
5. Do not commit generated indexes containing proprietary information.
6. Review firewall and network exposure.
7. Rotate initial/default credentials before production use.

---

## 📌 Project Documentation

For complete deployment information, start with:

```text
QUICK_ANSWER.md
```

Then continue with:

```text
INSTALLATION_GUIDE.md
PREREQUISITES.md
TEST_REPORT.md
```

---

## 👨‍💻 Project

**adAIent — AI-Powered Equipment Troubleshooting Assistant**

Built as an engineering project focused on applying AI, RAG, document retrieval, authentication, and automated deployment to industrial troubleshooting workflows.
