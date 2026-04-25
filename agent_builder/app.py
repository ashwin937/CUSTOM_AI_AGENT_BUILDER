"""
AI Agent Builder - Multi-Page with Auto-Opening Agent Pages
Features:
- Build custom AI agents with individual interfaces
- Each agent opens in its own auto-opened page
- Unique links for each agent
- Separate agent viewer interface
"""

import json
import re
import os
import sys
import logging
import uuid
import webbrowser
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
import gradio as gr

# Load environment variables
try:
    from dotenv import load_dotenv
    # Robust .env loading
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")
    else:
        load_dotenv() # Fallback
except ImportError:
    print("⚠️ python-dotenv not installed. Run: pip install python-dotenv")

# Import custom modules
from prompts import get_system_prompt
from agent_store import load_all_agents, save_agent, get_all_agents_list, increment_run, get_agent, delete_agent
from rag_handler import process_uploaded_files, create_rag_prompt, load_knowledge_base
from ui_generator import UIGenerator
from gmail_automation import get_gmail_automation
from integrations import LinkedInIntegration, InstagramIntegration
from scheduler_manager import SchedulerManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== AGENTS REGISTRY ==========
AGENTS_REGISTRY = {}
AGENT_LINKS = {}
NEW_AGENT_CREATED = None

def load_agent_links():
    """Load agent links from file."""
    global AGENT_LINKS
    if os.path.exists("agent_links.json"):
        try:
            with open("agent_links.json", "r") as f:
                AGENT_LINKS = json.load(f)
        except:
            AGENT_LINKS = {}
    else:
        AGENT_LINKS = {}

def save_agent_links():
    """Save agent links to file."""
    with open("agent_links.json", "w") as f:
        json.dump(AGENT_LINKS, f, indent=2)

def generate_agent_link(agent_name: str) -> str:
    """Generate unique link for agent."""
    if agent_name not in AGENT_LINKS:
        AGENT_LINKS[agent_name] = str(uuid.uuid4())[:8]
        save_agent_links()
    return AGENT_LINKS[agent_name]

load_agent_links()

# ========== CREDENTIALS CHECK ==========

def verify_credentials():
    """Check if credentials are configured."""
    required_vars = {
        "GMAIL_CLIENT_ID": "Gmail OAuth Client ID",
        "GMAIL_CLIENT_SECRET": "Gmail OAuth Client Secret",
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"❌ {description}")
    
    if missing:
        logger.warning("⚠️  Missing credentials:")
        for item in missing:
            logger.warning(item)
        return False
    
    logger.info("✅ Gmail credentials configured")
    return True

verify_credentials()

# ========== INITIALIZE CLIENTS & GMAIL ==========

chat_client = OpenAI(base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"), api_key="ollama")

# Initialize Scheduler
scheduler = SchedulerManager(client=chat_client)
scheduler.start()

# Initialize Integrations
gmail = None
try:
    gmail = get_gmail_automation()
except Exception as e:
    logger.warning(f"⚠️ Gmail initialization deferred: {e}")
    gmail = None

linkedin = None
try:
    # Requires an access token typically, if you have one it can be passed or managed by OAuth manager 
    # Here we instantiate it; but the actual oauth flow is needed
    from oauth_manager import OAuthManager
    oauth_mgr = OAuthManager()
    token_data = oauth_mgr.get_token('linkedin')
    if token_data and isinstance(token_data, dict):
         linkedin_token = token_data.get('access_token')
    elif token_data and isinstance(token_data, str):
         linkedin_token = token_data
    else:
         linkedin_token = None

    linkedin = LinkedInIntegration(access_token=linkedin_token) if linkedin_token else LinkedInIntegration()
except Exception as e:
    logger.warning(f"⚠️ LinkedIn initialization deferred: {e}")
    linkedin = None

instagram = None
try:
    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    instagram = InstagramIntegration(access_token=ig_token) if ig_token else InstagramIntegration()
except Exception as e:
    logger.warning(f"⚠️ Instagram initialization deferred: {e}")
    instagram = None

user_context = {
    "pending_agent_spec": None,
    "uploaded_files": None,
    "current_agent": None,
    "last_output": None,
}

# ========== RESPONSE PROCESSING ==========

def extract_json(text: str, marker: str) -> Optional[Dict]:
    """Extract JSON from response."""
    try:
        start = text.find(marker)
        if start == -1:
            return None
        start += len(marker)
        brace_start = text.find("{", start)
        if brace_start == -1:
            return None
        
        depth = 0
        for i, char in enumerate(text[brace_start:]):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    json_str = text[brace_start:brace_start+i+1]
                    return json.loads(json_str)
        return None
    except:
        return None

def process_response(raw_response: str, user_message: str) -> tuple:
    """Process LLM response. Returns (response_text, agent_name_if_created)."""
    global NEW_AGENT_CREATED
    
    # Check for agent building
    spec_json = extract_json(raw_response, "<<<SPEC>>>")
    if spec_json:
        agent_name = spec_json.get("agent_name", "agent")
        display_name = spec_json.get("display_name", agent_name)
        
        # Save agent
        save_agent(spec_json, f"agents/{agent_name}")
        AGENTS_REGISTRY[agent_name] = spec_json
        
        # Schedule Job if required
        start_msg = ""
        if spec_json.get("trigger") == "scheduled" and spec_json.get("schedule"):
            try:
                # Default to daily at 9am if parsing fails
                
                s_type = "daily"
                s_time = "09:00"
                s_raw = str(spec_json.get("schedule")).lower()

                if "hour" in s_raw:
                    s_type = "hourly"
                    s_time = "1"
                elif "minute" in s_raw:
                    s_type = "interval"
                    # Try to find number
                    m = re.search(r'\d+', s_raw)
                    s_time = m.group(0) if m else "60"
                elif "daily" in s_raw:
                    # Try to find time
                    m = re.search(r'\d{1,2}:\d{2}', s_raw)
                    if m:
                         s_time = m.group(0)
                
                jid = scheduler.add_job(agent_name, spec_json.get("task"), s_type, s_time)
                start_msg = f"\n🕒 **Scheduled Job**: Active ({s_type} @ {s_time})"
            except Exception as e:
                logger.error(f"Scheduling failed: {e}")
        
        # Generate link
        link_id = generate_agent_link(agent_name)
        NEW_AGENT_CREATED = agent_name
        
        # Auto-open agent page if running locally
        # This solves: "move to the new page with created agent... look like an automation"
        webbrowser.open(f"http://127.0.0.1:7861/?agent={link_id}")
        
        # Clean response
        clean_response = re.sub(r'<<<SPEC>>>.*?$', '', raw_response, flags=re.DOTALL).strip()
        
        separator = "=" * 70
        deployment_msg = (
            f"\n\n{separator}\n"
            f"✅ **AGENT CREATED SUCCESSFULLY**\n"
            f"{separator}\n"
            f"🤖 Agent: **{display_name}**\n"
            f"🔗 Link ID: `{link_id}`\n"
            f"📋 Department: {spec_json.get('department', 'N/A')}\n"
            f"⚡ Trigger: {spec_json.get('trigger', 'N/A')}\n"
            f"✨ Status: **READY TO USE**{start_msg}\n"
            f"{separator}\n\n"
            f"[🔗 Click here to open {display_name} in new page](http://127.0.0.1:7861/?agent={link_id})"
        )
        
        return clean_response + deployment_msg, agent_name
    
    return raw_response, None

# ========== CHAT FUNCTION ==========

def chat(message: str, history, uploaded_files=None, context_mode="builder"):
    """Main chat function."""
    try:
        if uploaded_files:
            user_context["uploaded_files"] = uploaded_files
            # Convert list to string but clean it up
            files_str = ", ".join(uploaded_files) if isinstance(uploaded_files, list) else str(uploaded_files)
            message += f"\n\n[SYSTEM] User has uploaded the following files: {files_str}. If asked to post an image, use one of these exact local file paths for the 'Image:' field. Do NOT wrap path in brackets or quotes."
        
        # Prevent building agents in Viewer mode
        if context_mode == "viewer":
            builder_triggers = ["build", "create", "generate", "make"]
            if any(t in message.lower() for t in builder_triggers) and "agent" in message.lower():
                return "🚫 **Action Restricted**: You cannot build new agents here. Please go to the **AI Agent Builder** tab to create new agents."

        user_msg_lower = message.lower()
        
        # === 1. Duplicate Prevention (Builder Mode) ===
        if context_mode == "builder" and any(w in user_msg_lower for w in ["build", "create", "make"]) and "agent" in user_msg_lower:
            existing_agents = get_all_agents_list()
            # Keywords to check for duplicates
            keywords = ["email", "instagram", "linkedin", "coding", "finance", "support", "sales", "marketing"]
            for k in keywords:
                if k in user_msg_lower:
                    # Find agent with this keyword in name or task
                    match = next((a for a in existing_agents if k in a.get("agent_name", "").lower() or k in a.get("task", "").lower()), None)
                    if match:
                         # Don't block if user is specific (e.g. "Create a NEW email agent"), but warn
                         if "new" not in user_msg_lower:
                             link_id = generate_agent_link(match.get("agent_name"))
                             return f"⚠️ **Duplicate Prevention**: You already have a **{k}** agent named **{match.get('display_name')}**.\n\n[🔗 Open Existing Agent](http://127.0.0.1:7861/?agent={link_id})\n\nIf you really want a new one, please specify a unique name (e.g., 'Cold Outreach Agent')."

        # === 2. Specialized Routing (Email/Social) ===
        special_instruction = ""
        user_msg_lower = message.lower() # ensure fresh lower
        
        # Check for Email Queries and route to Email Agent if exists
        if any(w in user_msg_lower for w in ["email", "gmail", "send message"]):
             existing_agents = get_all_agents_list()
             email_agent = next((a for a in existing_agents if "email" in a.get("agent_name", "").lower() or "mail" in a.get("task", "").lower()), None)
             if email_agent:
                 special_instruction += f"\n\n[SYSTEM] A specialized agent '{email_agent.get('display_name')}' exists for handling emails. Its predefined task is: '{email_agent.get('task')}'. Use its style and instructions to handle this request."

        saved_agents = load_all_agents()
        system_prompt = get_system_prompt(saved_agents) + special_instruction
        
        # Check for GitHub token queries
        user_msg_lower = message.lower()
        if "github token" in user_msg_lower or "how to get github" in user_msg_lower:
            return """
### 🔑 How to Get Your GitHub Personal Access Token (PAT)

1.  Log in to your **GitHub** account.
2.  Go to **Settings** (click your profile picture > Settings).
3.  Scroll down to **Developer settings** (bottom left).
4.  Click **Personal access tokens** > **Tokens (classic)**.
5.  Click **Generate new token** > **Generate new token (classic)**.
6.  **Note**: Give it a name like "AI Agent Builder".
7.  **Select Scopes**:
    *   `repo` (Full control of private repositories)
    *   `workflow` (Update GitHub Action workflows)
8.  Click **Generate token**.
9.  **COPY IT IMMEDIATELY** (you won't see it again).
10. Update your `.env` file with:
    `GITHUB_ACCESS_TOKEN=your_token_here`
    `GITHUB_USERNAME=your_username`
"""
        # Check for Instagram token queries
        if "instagram token" in user_msg_lower or "how to get instagram" in user_msg_lower:
            return """
### 📸 How to Get Instagram Credentials

1.  **Meta Developer Console**: Go to [developers.facebook.com](https://developers.facebook.com/).
2.  **Create App**: Select "Business" type.
3.  **Add Instagram Graph API**: Add this product to your app.
4.  **Connect Page**: Link your Facebook Page to your Instagram Business Account.
5.  **Get Token**: Use Graph API Explorer to generate a User Token with `instagram_basic` and `instagram_content_publish` permissions.
6.  **Get Account ID**: Query `me/accounts` in the explorer to find your Page, then `?fields=instagram_business_account`.
7.  **Update .env**:
    `INSTAGRAM_ACCESS_TOKEN=your_token_here`
    `INSTAGRAM_ACCOUNT_ID=your_account_id_here`
"""
        
        # Try to grab "deploy [agent_name]"
        match = re.search(r"deploy\s+(?:the\s+)?([a-zA-Z0-9_\-]+)(?:\s+agent)?", user_msg_lower)
        if match:
             agent_query = match.group(1)
             # Find agent
             from agent_store import get_agent
             from integrations import GitHubIntegration
             
             # Basic fuzzy match or exact match from store
             agent_data = get_agent(agent_query)
             
             if not agent_data:
                 return f"❌ I couldn't find an agent named **{agent_query}**. Check your list of built agents."
             
             github_token = os.getenv("GITHUB_ACCESS_TOKEN")
             if not github_token:
                 return "⚠️ **GitHub Token Missing.** ask me: 'How do I get a GitHub token?'"
                 
             gh = GitHubIntegration(access_token=github_token)
             
             repo_name = f"agent-{agent_query.lower()}"
             
             # Create Repo
             res = gh.create_repo(repo_name, description=agent_data.get('task', 'AI Agent'))
             if "error" in res:
                 return f"❌ Deployment Failed: {res['error']}"
                 
             repo_url = res['repo']['html_url']
             
             # Deploy files
             reqs = "openai\npython-dotenv\nrequests\n"
             gh.upload_file(repo_name, "requirements.txt", reqs, "Add dependencies")
             
             code = f"""import os
from openai import OpenAI

# Agent: {agent_data.get('display_name')}
# Task: {agent_data.get('task')}

client = OpenAI()

def run_agent(input_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {{'role': 'system', 'content': 'You are a helpful AI agent.'}},
            {{'role': 'user', 'content': input_text}}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    print("Agent {agent_data.get('display_name')} is running...")
"""
             gh.upload_file(repo_name, "main.py", code, "Add main agent code")
             
             return f"""### 🚀 Agent Deployed Successfully!

**{agent_data.get('display_name')}** is now on GitHub.

*   📂 **Repo:** [{repo_name}]({repo_url})
*   📄 **Files:** `main.py`, `requirements.txt` pushed.

You can now clone this or connect it to a hosting service!"""

        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in history:
            if isinstance(msg, dict):
                messages.append(msg)
            else:
                messages.append({"role": msg[0], "content": msg[1]})

        



        if any(word in user_msg_lower for word in ["email", "gmail", "send message"]):
            message += """

CRITICAL INSTRUCTION FOR EMAIL SENDING:
If the user is asking you to send an email or draft one to a specific entity, you MUST format your response exactly like this to trigger the email engine:
To: example@email.com (make up a plausible one if you don't have it, e.g., info@google.com)
Subject: [Your Subject]
Body:
[The full email message...]
"""
        elif any(word in user_msg_lower for word in ["linkedin", "post a job", "post something", "job offer"]):
             message += """

CRITICAL INSTRUCTION FOR LINKEDIN POSTING:
If the user is asking you to post a job opening or post something on LinkedIn, analyze their request. If requirements are not present, make reasonable professional assumptions.
You MUST format your output exactly like this to trigger the LinkedIn posting engine:
LinkedIn Post:
[The full job offer or post content including relevant hashtags...]
"""
        elif any(word in user_msg_lower for word in ["instagram", "post photo", "share image"]):
             message += """

CRITICAL INSTRUCTION FOR INSTAGRAM POSTING:
If the user is asking you to post a photo or image to Instagram, analyze their request. You need a local image file path or a public image URL and a caption.
You MUST format your output exactly like this to trigger the Instagram posting engine:
Instagram Post:
Image: [The full local file path OR public URL of the image]
Caption: [The caption including hashtags]
"""

        messages.append({"role": "user", "content": message})

        response = chat_client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "qwen3:4b"),
            messages=messages,
            temperature=0.7,
        )

        raw_response = response.choices[0].message.content
        final_response, agent_name = process_response(raw_response, message)
        
        # Auto-send email if triggered
        try:
            user_msg_lower = message.lower()
            if any(word in user_msg_lower for word in ["email", "gmail", "send message", "compose", "draft"]):
                # import re (Removed local import)
                to_match = re.search(r'(?:to:|recipient:)\s*([^\n]+?)(?:\n|$)', final_response, re.IGNORECASE)
                subject_match = re.search(r'(?:subject:|re:)\s*([^\n]+?)(?:\n|$)', final_response, re.IGNORECASE)
                body_match = re.search(r'(?:body:|message:|content:)\s*([\s\S]+?)(?:\n\nProof|\n\n✅|\n\n❌|$)', final_response, re.IGNORECASE)

                if to_match and subject_match:
                    to_email = to_match.group(1).strip().strip("'\"").strip("<>")
                    subject = subject_match.group(1).strip().strip("'\"")
                    body = body_match.group(1).strip() if body_match else final_response
                    
                    if gmail and gmail.is_authenticated():
                        result = gmail.send_email(to_email, subject, body)
                        if result:
                            final_response += f"\n\n✅ **Email successfully sent to {to_email}!**\n\n**Proof of Delivery:**\n- **To:** {to_email}\n- **Subject:** {subject}\n- **Status:** Sent successfully via Gmail Integration."
                        else:
                            final_response += f"\n\n❌ **Failed to send email to {to_email}.** Check logs."
                    else:
                        final_response += f"\n\n⚠️ **Could not send email:** Gmail is not authenticated or not initialized. Please run authorize_gmail() or check your tokens."
            
            # Auto-post to LinkedIn if triggered
            if any(word in user_msg_lower for word in ["linkedin", "post a job", "post something", "job offer"]):
                # import re (Removed local import)
                post_match = re.search(r'LinkedIn Post:\s*([\s\S]+?)(?:\n\nProof|\n\n✅|\n\n❌|$)', final_response, re.IGNORECASE)
                
                if post_match:
                    post_content = post_match.group(1).strip()
                    
                    if linkedin and linkedin.access_token:
                        result = linkedin.share_post(content=post_content)
                        if result.get("success"):
                            post_url = result.get("url", "Check your profile")
                            final_response += f"\n\n✅ **Successfully posted to LinkedIn!**\n\n**Proof of Delivery:**\n- **Status:** Shared successfully to your professional network.\n- **View Post:** [Click here to view on LinkedIn]({post_url})"
                        else:
                            final_response += f"\n\n❌ **Failed to post to LinkedIn.** Error: {result.get('error', 'Unknown')}"
                    else:
                        final_response += f"\n\n⚠️ **Could not post to LinkedIn:** LinkedIn is not authenticated. Please ensure valid LinkedIn Client ID and Secret are provided and authorized."

            # Auto-post to Instagram if triggered
            if any(word in user_msg_lower for word in ["instagram", "post photo", "share image"]):
                # import re (Removed local import)
                # Match both URLs and local file paths (greedy match until newline)
                img_match = re.search(r"Image:\s*([^\n]+)", final_response)
                cap_match = re.search(r"Caption:\s*([\s\S]+?)(?:\n\nProof|\n\n✅|\n\n❌|$)", final_response)
                
                if img_match:
                    if instagram is None:
                         final_response += "\n\n⚠️ **Instagram not initialized.** Check dependencies."
                    else:
                        # Attempt post (will use Selenium if API token is missing)
                        img_path_or_url = img_match.group(1).strip().strip('"').strip("'")
                        caption = cap_match.group(1).strip() if cap_match else "AI Generated Post"
                        
                        res = instagram.post_photo(img_path_or_url, caption)
                        if res.get("success"):
                            post_id = res.get("post_id", "N/A")
                            final_response += f"\n\n✅ **Successfully posted to Instagram!**\n\n**Post ID:** {post_id}"
                        else:
                            error_msg = res.get('error')
                            final_response += f"\n\n❌ **Failed to post to Instagram.** Error: {error_msg}"
                            if "Authentication" in str(error_msg) or "Selenium skipped" in str(error_msg):
                                final_response += "\n\n(Tip: Ensure INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD are in your .env file)"
                elif not img_match:
                     final_response += "\n\n⚠️ **Instagram Error:** Could not find a valid image URL in the response."

        except Exception as e:
            logger.info(f"Automation execution error: {e}")
        
        return final_response
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return f"❌ Error: {str(e)}"

# ========== BUILDER INTERFACE ==========

def create_builder():
    """Create the main builder interface."""
    with gr.Blocks(theme=gr.themes.Soft(), title="AI Agent Builder") as builder:
        gr.Markdown("# 🚀 AI Agent Builder")
        gr.Markdown("**Build agents. Get unique links. Open in new page.**")
        gr.Markdown("---")
        
        # State to track context
        mode = gr.State("builder")
        
        with gr.Tabs():
            
            # ===== BUILDER TAB =====
            with gr.TabItem("🏗️ Builder - Create Agents"):
                gr.Markdown("# 🤖 Agent Builder")
                gr.Markdown("**Describe what you need. Agent will be built with unique link.**")
                gr.Markdown("**A new page will open automatically!**")
                gr.Markdown("---")
                
                uploaded = gr.File(label="📁 Upload Files (Optional)", file_count="multiple", type="filepath")
                # Chat UI (gr.ChatInterface removed/changed in Gradio 6.x)
                chatbot = gr.Chatbot()
                textbox = gr.Textbox(placeholder="Build me an email writing agent...", scale=7)
                send_btn = gr.Button("Send")
                hist_state = gr.State([])

                def _submit_message(message, history, uploaded_files, mode_val):
                    """Submit handler that calls the chat() function and updates the chat history.

                    Inputs:
                    - message: str
                    - history: list of messages (Gradio 6.x format)
                    - uploaded_files: uploaded file paths or None
                    - mode_val: 'builder' or 'viewer'

                    Returns: (updated_history, clear_textbox)
                    """
                    try:
                        if not message:
                            return history or [], ""
                        history = history or []
                        # Call existing chat function
                        resp = chat(message, history, uploaded_files=uploaded_files, context_mode=mode_val)
                        # Ensure string
                        if isinstance(resp, tuple):
                            resp_text = resp[0]
                        else:
                            resp_text = resp
                        # Gradio 6.x format: list of tuples or dicts
                        history.append((message, resp_text))
                        return history, ""
                    except Exception as e:
                        # On error, append error message
                        history = history or []
                        history.append((message, f"❌ Error: {e}"))
                        return history, ""

                # Wire up submit and button
                textbox.submit(_submit_message, inputs=[textbox, hist_state, uploaded, mode], outputs=[chatbot, textbox])
                send_btn.click(_submit_message, inputs=[textbox, hist_state, uploaded, mode], outputs=[chatbot, textbox])
            
            # ===== AGENT DIRECTORY =====
            with gr.TabItem("� Agent Directory"):
                gr.Markdown("# 📑 Your Agents")
                gr.Markdown("**All agents with their unique links**")
                gr.Markdown("---")
                
                def get_agents_display():
                    agents = get_all_agents_list()
                    
                    if not agents:
                        return "### No agents yet. Build one in the Builder tab! 🚀"
                    
                    display = f"### You have {len(agents)} agent(s)\n\n"
                    for agent in agents:
                        name = agent.get("agent_name", "unknown")
                        display_name = agent.get("display_name", name)
                        task = agent.get("task", "No description")
                        link_id = generate_agent_link(name)
                        
                        display += f"""
**{display_name}**
- 🔗 Link: `{link_id}`
- 📋 Task: {task}
- 🎯 Department: {agent.get('department', 'N/A')}

[🔗 Open Agent](http://127.0.0.1:7861/?agent={link_id})

"""
                    return display
                
                agents_display = gr.Markdown(get_agents_display())
                
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Refresh", variant="primary")
                
                gr.Markdown("### 🗑️ Manage Agents")
                with gr.Row():
                    delete_dropdown = gr.Dropdown(label="Select Agent to Delete", choices=[], interactive=True)
                    delete_btn = gr.Button("❌ Delete Selected Agent", variant="stop")
                
                delete_msg = gr.Markdown(visible=False)

                def update_delete_dropdown():
                    agents = get_all_agents_list()
                    return gr.Dropdown(choices=[(a.get("display_name", a.get("agent_name")), a.get("agent_name")) for a in agents])

                def on_delete_agent(agent_name):
                    if not agent_name:
                        return "⚠️ Please select an agent."
                    
                    if delete_agent(agent_name):
                        return f"✅ Agent '{agent_name}' deleted successfully. Refresh list to see changes."
                    else:
                        return f"❌ Failed to delete agent '{agent_name}'."
                
                refresh_btn.click(lambda: get_agents_display(), outputs=agents_display)
                refresh_btn.click(update_delete_dropdown, outputs=delete_dropdown)
                
                # Load initial choices
                builder.load(update_delete_dropdown, outputs=delete_dropdown)
                
                delete_btn.click(on_delete_agent, inputs=delete_dropdown, outputs=delete_msg)
                delete_btn.click(lambda: gr.update(visible=True), outputs=delete_msg)
                delete_btn.click(lambda: get_agents_display(), outputs=agents_display) # Auto refresh list
                delete_btn.click(update_delete_dropdown, outputs=delete_dropdown) # Auto refresh dropdown
            
            # ===== GUIDE TAB =====
            with gr.TabItem("❓ Guide"):
                gr.Markdown("""
# 🎯 How to Use

## Step 1: Build Agent
- Go to **Builder** tab
- Describe what agent you need
- Click send

## Step 2: Auto-Open
- **New page opens automatically** with your agent
- Agent page shows at http://127.0.0.1:7861
- Full chat interface for your agent

## Step 3: Find Agents
- Go to **Agent Directory**
- See all your agents with links
- Click any link to open agent page

## Features

✅ **Auto-Open** - New agent pages open automatically
✅ **Unique Links** - Every agent gets unique link ID
✅ **Direct Access** - Open agents from links
✅ **Full Interface** - Each agent has chat for interaction

## Example

**Request**: "Build me an email agent"
**Result**: 
- Email Agent created with link ID
- New page opens automatically
- Use agent on new page
""")
    
    return builder

# ========== AGENT VIEWER INTERFACE ==========

def create_agent_viewer():
    """Create interface to view/use specific agent."""
    with gr.Blocks(theme=gr.themes.Soft(), title="AI Agent") as viewer:
        gr.Markdown("# 🤖 Agent Viewer")
        
        # State to track context
        mode = gr.State("viewer")
        
        # Hidden input to get agent link from URL
        agent_link_input = gr.Textbox(label="Agent Link", visible=False)
        agent_selector = gr.Dropdown(label="Select Agent", choices=[], interactive=True)
        
        def load_agents_list():
            agents = get_all_agents_list()
            choices = []
            for agent in agents:
                name = agent.get("agent_name", "unknown")
                display_name = agent.get("display_name", name)
                link_id = generate_agent_link(name)
                choices.append((f"{display_name} (ID: {link_id})", name))
            return choices
        
        def on_agent_select(agent_name):
            if not agent_name:
                return gr.update(visible=False)
            
            agent = get_agent(agent_name)
            if not agent:
                return gr.update(visible=False)
            
            display_name = agent.get("display_name", agent_name)
            link_id = generate_agent_link(agent_name)
            
            info = f"""
# 🤖 {display_name}

**Link ID:** `{link_id}`
**Task:** {agent.get('task', 'N/A')}
**Department:** {agent.get('department', 'N/A')}
**Trigger:** {agent.get('trigger', 'N/A')}

---
"""
            return gr.update(value=info, visible=True)
        
        agent_info = gr.Markdown(visible=False)
        
        agent_selector.choices = load_agents_list()
        agent_selector.change(on_agent_select, inputs=agent_selector, outputs=agent_info)
        
        def on_agent_load():
            agents = get_all_agents_list()
            if agents:
                first_agent = agents[0].get("agent_name", "unknown")
                return first_agent
            return None
        
        # On load, select first agent
        viewer.load(lambda: on_agent_load(), outputs=agent_selector)
        
        # Chat interface at bottom
        uploaded = gr.File(label="📁 Upload Files (Optional)", file_count="multiple", type="filepath")
        chatbot = gr.Chatbot()
        textbox = gr.Textbox(placeholder="Chat with agent...", scale=7)
        send_btn = gr.Button("Send")
        hist_state = gr.State([])

        def _submit_message_view(message, history, uploaded_files, mode_val):
            try:
                if not message:
                    return history or [], ""
                history = history or []
                resp = chat(message, history, uploaded_files=uploaded_files, context_mode=mode_val)
                if isinstance(resp, tuple):
                    resp_text = resp[0]
                else:
                    resp_text = resp
                history.append((message, resp_text))
                return history, ""
            except Exception as e:
                history = history or []
                history.append((message, f"❌ Error: {e}"))
                return history, ""

        textbox.submit(_submit_message_view, inputs=[textbox, hist_state, uploaded, mode], outputs=[chatbot, textbox])
        send_btn.click(_submit_message_view, inputs=[textbox, hist_state, uploaded, mode], outputs=[chatbot, textbox])
    
    return viewer

# ========== MAIN APP ==========

if __name__ == "__main__":
    # Create builder interface on port 7860
    builder = create_builder()
    
    # Create agent viewer interface on port 7861
    viewer = create_agent_viewer()
    
    # Launch builder (main)
    print("🚀 Starting AI Agent Builder...")
    print("📌 Builder: http://127.0.0.1:7860")
    print("📌 Agent Pages: http://127.0.0.1:7861")
    
    builder.queue()
    viewer.queue()
    
    # Use threading to run both interfaces
    import threading
    
    def run_builder():
        builder.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=True
        )
    
    def run_viewer():
        viewer.launch(
            server_name="127.0.0.1",
            server_port=7861,
            share=False,
            show_error=True,
            quiet=True
        )
    
    # Start both in threads
    t1 = threading.Thread(target=run_builder, daemon=True)
    t2 = threading.Thread(target=run_viewer, daemon=True)
    
    t1.start()
    t2.start()
    
    # Keep alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ App stopped")


