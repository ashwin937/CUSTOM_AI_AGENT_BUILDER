# 🤖 Custom AI Agent Builder

A powerful, feature-rich platform for building, managing, and deploying custom AI agents with multi-channel integrations. Create intelligent automation workflows without extensive coding.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

## 🌟 Features

### Core Capabilities
- **🧠 Custom AI Agents** - Build intelligent agents with customizable behaviors and tasks
- **📱 Multi-Channel Integration** - Connect with Gmail, LinkedIn, Instagram, and more
- **🎯 RAG (Retrieval-Augmented Generation)** - Upload and leverage custom knowledge bases
- **📅 Automated Scheduling** - Schedule agent tasks with cron-like flexibility
- **💾 Persistent Storage** - SQLite database for agent metadata and execution history
- **🌐 Web UI** - Beautiful Gradio-based interface for managing agents
- **🔗 Unique Agent Links** - Generate shareable links for individual agents
- **📊 Execution Tracking** - Monitor agent runs and performance metrics

### Integration Features
- **📧 Gmail Automation**
  - Send emails programmatically
  - OAuth2 authentication
  - Email template support

- **💼 LinkedIn Integration**
  - Post updates
  - Schedule content
  - Multi-profile support

- **📸 Instagram Integration**
  - Post photos and captions
  - Story publishing
  - Graph API support

- **🔄 Scheduler**
  - Background task scheduling
  - Recurring job support
  - Job persistence

## 📋 Prerequisites

- Python 3.8 or higher
- pip or conda
- Environment variables configured (see Setup)

### API Credentials Required
- Gmail OAuth Client ID & Secret
- LinkedIn Client ID & Secret (optional)
- Instagram/Meta Graph API Token (optional)
- GitHub Personal Access Token (optional)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/ashwin937/CUSTOM_AI_AGENT_BUILDER.git
cd CUSTOM_AI_AGENT_BUILDER/agent_builder
```

### 2. Create Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Gmail Configuration
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret

# LinkedIn Configuration (optional)
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

# Instagram Configuration (optional)
INSTAGRAM_ACCESS_TOKEN=your_instagram_token

# GitHub Token (optional)
GITHUB_TOKEN=your_github_token
```

### 5. Run the Application
```bash
python app.py
```

The application will automatically open in your default browser at `http://localhost:7860`

## 📁 Project Structure

```
agent_builder/
├── app.py                      # Main Gradio application
├── app.py                      # Primary entry point
├── agent_store.py              # SQLite agent persistence layer
├── rag_handler.py              # RAG implementation and knowledge base management
├── integrations.py             # Third-party service integrations
├── gmail_automation.py         # Gmail OAuth and automation
├── scheduler_manager.py        # Background job scheduling
├── oauth_manager.py            # OAuth token management
├── ui_generator.py             # Dynamic UI component generation
├── prompts.py                  # System prompts and templates
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── agents.db                   # SQLite database (auto-created)
├── agent_links.json            # Agent URL mapping
├── saved_agents/               # Agent configuration storage
├── templates/                  # Jinja2 templates for prompts
└── scratch/                    # Development scripts and demos
```

## 🔧 Configuration

### Gmail Setup
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop application)
4. Add credentials to `.env`

### Instagram Setup
Detailed setup instructions available in [INSTAGRAM_SETUP.md](./INSTAGRAM_SETUP.md)

For Instagram integration:
1. Create a Meta Developer App
2. Generate access tokens via Graph API Explorer
3. Configure page and account permissions
4. Add token to `.env`

### LinkedIn Setup
1. Create an application at [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Request partner access if needed
3. Add credentials to `.env`

## 💻 Usage Guide

### Creating an Agent

1. **Navigate to Agent Builder Tab**
   - Fill in agent name, display name, and department
   - Define the main task/prompt
   - Set trigger conditions
   - Choose output type (text, file, etc.)

2. **Configure Knowledge Base (Optional)**
   - Upload PDF, TXT, MD, CSV, or JSON files
   - Agent will use uploaded documents for context

3. **Add Integrations (Optional)**
   - Enable Gmail for email automation
   - Enable LinkedIn for social sharing
   - Enable Instagram for visual content

4. **Set Schedule (Optional)**
   - Configure cron expressions for recurring tasks
   - Agent will execute automatically

5. **Save and Deploy**
   - Click "Create Agent"
   - Get unique agent link
   - Share with team members

### Running an Agent

#### Via Web UI
1. Select agent from "View Agents"
2. Input required parameters
3. Click "Run Agent"
4. View results and execution history

#### Via Unique Agent Link
- Each agent has a unique shareable link
- Open link to access dedicated agent interface
- Run agent without accessing main dashboard

#### Programmatically
```python
from agent_store import get_agent, load_all_agents
from app import execute_agent

# Get agent configuration
agent = get_agent("my_agent_name")

# Execute agent
result = execute_agent(agent, input_data)
print(result)
```

## 🛠️ Development

### Adding New Integrations

1. Create integration class in `integrations.py`:
```python
class CustomIntegration:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def authenticate(self):
        """Implement OAuth flow"""
        pass
    
    def execute_action(self, action, params):
        """Execute specific action"""
        pass
```

2. Register in `OAuthConfig.SERVICES`

3. Add to agent configuration UI

### Custom Prompts

Edit system prompts in `templates/system_prompt.jinja2`:
```jinja2
You are {{ agent_name }}, a specialized AI assistant.
Department: {{ department }}
Task: {{ task }}
```

### Adding RAG Support

Knowledge bases are automatically processed. Supported formats:
- `.txt` - Plain text
- `.md` - Markdown
- `.pdf` - PDF documents
- `.csv` - Comma-separated values
- `.json` - JSON data

## 📊 Database Schema

### Agents Table
```sql
CREATE TABLE agents (
    agent_name TEXT PRIMARY KEY,
    display_name TEXT,
    department TEXT,
    task TEXT,
    trigger TEXT,
    output_type TEXT,
    created_at TEXT,
    run_count INTEGER,
    agent_dir TEXT
)
```

### Agent Memory Table
```sql
CREATE TABLE agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT,
    task TEXT,
    output TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY(agent_name) REFERENCES agents(agent_name)
)
```

## 🔐 Security Considerations

- **Never commit `.env` files** - Use `.env.example` template instead
- **Store credentials securely** - Use environment variables or secret management systems
- **Rotate tokens regularly** - OAuth tokens should be refreshed periodically
- **Use HTTPS** - For production deployments
- **Validate inputs** - All user inputs are sanitized
- **Limit agent permissions** - Grant minimal necessary scopes to APIs

## 🐛 Troubleshooting

### Gmail OAuth Issues
```python
# Run diagnosis script
python diagnose_gmail.py
```

### Agent Not Executing
1. Check agent configuration in `agents.db`
2. Verify all required environment variables set
3. Check `app.log` for error messages
4. Ensure dependencies installed: `pip install -r requirements.txt`

### Port Already in Use
```bash
# Run on different port
python -m gradio app.py --server-port 7861
```

### Knowledge Base Not Loading
- Verify file format is supported
- Check file permissions
- Ensure knowledge_base directory exists in agent folder

## 📝 Logging

Logs are saved to `app.log` and `app_output.log`. Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Production Deployment

### Using Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Using systemd
Create `/etc/systemd/system/ai-agent.service`:
```ini
[Unit]
Description=Custom AI Agent Builder
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-agent-builder
ExecStart=/opt/ai-agent-builder/venv/bin/python app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 📦 Dependencies

### Core
- `gradio` - Web UI framework
- `python-dotenv` - Environment variable management
- `ollama` - Local LLM support

### APIs & Authentication
- `google-auth-oauthlib` - Gmail OAuth
- `google-api-python-client` - Gmail API
- `requests` - HTTP requests

### Automation
- `selenium` - Browser automation
- `webdriver-manager` - WebDriver management
- `undetected-chromedriver` - Anti-detection driver
- `schedule` - Job scheduling

## 📚 Examples

### Example 1: Email Marketing Agent
```python
Agent Configuration:
- Name: Email Marketing Bot
- Task: Send personalized emails to lead list
- Integration: Gmail
- Trigger: Daily at 9 AM
- Output: Delivery report
```

### Example 2: Social Media Scheduler
```python
Agent Configuration:
- Name: Social Media Manager
- Task: Post updates across platforms
- Integrations: LinkedIn, Instagram
- Trigger: Scheduled posts
- Output: Performance metrics
```

### Example 3: Knowledge Assistant
```python
Agent Configuration:
- Name: Documentation Assistant
- Task: Answer questions about company docs
- Knowledge Base: Uploaded PDFs and wikis
- Trigger: User query
- Output: Answer with citations
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues, questions, or suggestions:
- Open an [Issue](https://github.com/ashwin937/CUSTOM_AI_AGENT_BUILDER/issues)
- Check [Discussions](https://github.com/ashwin937/CUSTOM_AI_AGENT_BUILDER/discussions)
- Review [Documentation](./INSTAGRAM_SETUP.md)

## 🙏 Acknowledgments

- Built with [Gradio](https://gradio.app/)
- OAuth implementations from official SDKs
- Inspiration from modern automation platforms

## 📞 Contact

**Developer**: Ashwin Kumar  
**GitHub**: [@ashwin937](https://github.com/ashwin937)

---

**Last Updated**: May 18, 2026  
**Version**: 1.0.0

⭐ If you find this project useful, please consider giving it a star!
