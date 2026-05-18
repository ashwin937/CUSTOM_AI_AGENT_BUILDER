# 🤖 QuintSync — AI Agent Builder

> **"Zapier for AI Agents"** — Build, deploy, and automate AI agents without writing a single line of code.

---

## 📌 About This Project

**QuintSync AI Agent Builder** is a no-code/low-code platform that empowers anyone — from non-technical users to seasoned developers — to create, configure, and deploy intelligent AI agents through a simple, conversational chat interface.

Powered by locally-running large language models (via **Ollama**), the platform requires **no cloud API keys** and runs entirely on your machine, giving you full privacy, zero cost, and complete control.

Simply describe what you want your agent to do — in plain English — and the system will build it, give it a unique shareable link, and open it in a dedicated interface automatically.

---

## ✨ Key Features

| Feature | Description |
|--------|-------------|
| 🗣️ **Chat-to-Agent** | Describe any agent in plain language — it gets built instantly |
| 🔗 **Unique Agent Links** | Every created agent receives its own unique shareable URL |
| 📂 **Agent Directory** | Browse, manage, and delete all your agents from a unified dashboard |
| 📅 **Scheduler** | Schedule agents to run automatically (hourly, daily, interval-based) |
| 📧 **Gmail Automation** | Send emails autonomously via OAuth-authenticated Gmail API |
| 💼 **LinkedIn Integration** | Auto-publish professional posts and job offers to LinkedIn |
| 📸 **Instagram Automation** | Post photos with captions using Selenium-based automation |
| 🐙 **GitHub Deployment** | Deploy agents as code directly to GitHub repositories |
| 🧠 **RAG Knowledge Base** | Upload files to give agents custom knowledge (PDF, TXT, etc.) |
| 🔒 **Local-First LLM** | Runs entirely offline using Ollama (no OpenAI dependency) |
| 🛡️ **Duplicate Prevention** | Smart detection prevents accidentally creating duplicate agents |
| 🔄 **Persistent Memory** | Agent history and data saved to SQLite for continuity |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Browser (UI Layer)                  │
│   http://127.0.0.1:7860  ──  Builder Interface       │
│   http://127.0.0.1:7861  ──  Agent Viewer Pages      │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│              Gradio Web Framework (Python)            │
│   - Chat Interface     - File Upload                 │
│   - State Management   - Multi-Tab Layout            │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│               Backend Services (Python)              │
│   - Chat Handler          - Agent Store (SQLite)     │
│   - Response Processor    - Integrations Manager     │
│   - RAG Handler           - Scheduler Manager        │
│   - OAuth Manager         - UI Generator             │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│                  External Services                   │
│   - Ollama (Qwen3:4b / Mistral / LLaMA2)            │
│   - Gmail API (OAuth2)    - LinkedIn API             │
│   - Instagram (Selenium)  - GitHub REST API          │
└──────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend UI** | Gradio (Python) |
| **Backend** | Python 3.13 |
| **LLM Engine** | Ollama (Local — Qwen3:4b, Mistral 7B, LLaMA2 7B) |
| **Database** | SQLite (Agent Store + OAuth Tokens) |
| **Knowledge Base** | RAG (Retrieval-Augmented Generation) |
| **Email** | Gmail API (OAuth2) via `google-auth` |
| **Social Media** | LinkedIn REST API + Instagram Selenium |
| **Scheduling** | APScheduler (background job scheduler) |
| **Deployment** | GitHub REST API |
| **Auth** | OAuth 2.0 with persistent token storage |
| **Environment** | python-dotenv |

---

## 🤖 LLM Models Supported

| Model | Parameters | Status |
|-------|-----------|--------|
| **qwen3:4b** *(default)* | 4B | ✅ Active |
| mistral:latest | 7.2B | ✅ Available |
| llama2:latest | 7B | ✅ Available |
| nomic-embed-text | 137M | ✅ (Embeddings) |

> All models run **100% locally** on CPU via Ollama. No data leaves your machine.

---

## 🔌 Integrations

| Service | Method | Status |
|---------|--------|--------|
| **Gmail** | OAuth2 + Google API | ✅ Configured |
| **LinkedIn** | REST API + OAuth2 | ✅ Configured |
| **Instagram** | Selenium Browser Automation | ✅ Configured |
| **GitHub** | Personal Access Token (PAT) | ✅ Configured |

---

## 🚀 What You Can Build

Here are some agents you can create just by chatting:

- 📧 **Email Writing Assistant** — Composes and auto-sends professional emails
- 💼 **LinkedIn Post Agent** — Publishes job offers and posts to your network
- 📸 **Instagram Content Agent** — Posts photos with AI-generated captions
- 💻 **Code Generation Agent** — Writes, explains, and debugs code on demand
- 📊 **Data Analysis Agent** — Reads CSVs and generates insights
- 🗓️ **Scheduled Digest Agent** — Delivers daily summaries at a set time
- 🤖 **Customer Support Agent** — Answers FAQs using your uploaded knowledge base

---

## ⚡ How to Run

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A pulled model: `ollama pull qwen3:4b`

### Start the App

```bash
# 1. Clone the repository
git clone https://github.com/ashwin937/CUSTOM_AI_AGENT_BUILDER.git
cd CUSTOM_AI_AGENT_BUILDER

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r agent_builder/requirements.txt

# 4. Configure environment
cp agent_builder/.env.example agent_builder/.env
# Edit .env with your API credentials

# 5. Start Ollama (in a separate terminal)
ollama serve

# 6. Launch the application
cd agent_builder
python app.py
```

### Access the App
- 🏗️ **Builder UI:** http://127.0.0.1:7860
- 🤖 **Agent Pages:** http://127.0.0.1:7861

---

## ⚙️ Environment Configuration

```env
# LLM
LLM_MODEL=qwen3:4b

# Gmail OAuth
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret

# LinkedIn
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token

# Instagram
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# GitHub
GITHUB_ACCESS_TOKEN=your_personal_access_token
GITHUB_USERNAME=your_username
```

---

## 📁 Project Structure

```
quintsync/
├── agent_builder/
│   ├── app.py                  # Main Gradio application
│   ├── agent_store.py          # SQLite agent persistence
│   ├── integrations.py         # Gmail, LinkedIn, Instagram, GitHub
│   ├── gmail_automation.py     # Gmail OAuth + send logic
│   ├── oauth_manager.py        # Token storage & refresh
│   ├── rag_handler.py          # Knowledge base / RAG
│   ├── scheduler_manager.py    # APScheduler job management
│   ├── ui_generator.py         # Dynamic UI generation
│   ├── prompts.py              # LLM system prompts
│   ├── .env                    # API credentials (private)
│   └── .env.example            # Credential template
├── DEMO_RUN.md                 # Live demo test cases
├── ABOUT.md                    # This file
└── requirements.txt
```

---

## 📈 Performance

| Task Type | Estimated Time |
|-----------|---------------|
| Simple Q&A | 5–15 seconds |
| Code generation | 30–90 seconds |
| Complex reasoning | 60–180 seconds |
| Email sending | ~60–120 seconds |
| Agent creation | ~60–90 seconds |

> ⚠️ Performance depends on hardware. The default model runs on CPU. Adding a GPU dramatically improves speed.

---

## 🔒 Privacy & Security

- ✅ **100% Local** — All LLM inference runs on your machine via Ollama
- ✅ **No Cloud Dependency** — No OpenAI, Anthropic, or external API calls for the core LLM
- ✅ **Token Encryption** — OAuth tokens stored securely in local SQLite database
- ✅ **Environment Variables** — All credentials managed via `.env` (never hardcoded)

---

## 👨‍💻 Developer

**GitHub:** [@ashwin937](https://github.com/ashwin937)
**Repository:** [CUSTOM_AI_AGENT_BUILDER](https://github.com/ashwin937/CUSTOM_AI_AGENT_BUILDER)

---

## 📄 License

This project is open-source and available for personal and commercial use.

---

*Built with ❤️ using Python, Gradio, and Ollama — No cloud. No limits. Just intelligence.*
