"""
Dynamic UI Generator for AI Agents
Generates custom interfaces based on agent type and capabilities
"""

import gradio as gr
from typing import Callable, Dict, Any, List, Optional


class UIGenerator:
    """Generate custom UIs for different agent types."""
    
    # Agent type templates
    AGENT_TEMPLATES = {
        "email": {
            "type": "form",
            "fields": ["recipient", "subject", "tone"],
            "integrations": ["gmail", "linkedin"],
            "description": "Write professional emails"
        },
        "social": {
            "type": "form",
            "fields": ["content_type", "tone", "platform"],
            "integrations": ["linkedin", "whatsapp"],
            "description": "Create social media posts"
        },
        "documentation": {
            "type": "form",
            "fields": ["title", "format", "language"],
            "integrations": ["github"],
            "description": "Generate documentation"
        },
        "sales": {
            "type": "chat",
            "fields": [],
            "integrations": ["gmail", "linkedin", "whatsapp"],
            "description": "Sales pitch and outreach"
        },
        "support": {
            "type": "chat",
            "fields": [],
            "integrations": [],
            "description": "Customer support responses"
        },
        "analysis": {
            "type": "chat",
            "fields": [],
            "integrations": [],
            "description": "Data and content analysis"
        },
        "general": {
            "type": "chat",
            "fields": [],
            "integrations": [],
            "description": "General purpose assistant"
        }
    }
    
    @staticmethod
    def detect_agent_type(agent_task: str) -> str:
        """Detect agent type from task description."""
        task_lower = agent_task.lower()
        
        keywords = {
            "email": ["email", "mail", "send", "message", "compose"],
            "social": ["social", "post", "linkedin", "twitter", "instagram", "facebook"],
            "documentation": ["documentation", "doc", "readme", "guide", "manual", "write doc"],
            "sales": ["sales", "pitch", "outreach", "lead", "prospect"],
            "support": ["support", "help", "customer", "ticket", "issue"],
            "analysis": ["analyze", "analysis", "review", "evaluate", "assess"],
        }
        
        for agent_type, keywords_list in keywords.items():
            if any(keyword in task_lower for keyword in keywords_list):
                return agent_type
        
        return "general"
    
    @staticmethod
    def create_chat_interface(agent_name: str, agent_task: str, run_agent: Callable) -> gr.Blocks:
        """Create a chat-based interface for the agent."""
        with gr.Blocks(theme=gr.themes.Soft(), title=f"Agent: {agent_name}") as interface:
            gr.Markdown(f"# 🤖 {agent_name}")
            gr.Markdown(f"**Task:** {agent_task}")
            gr.Markdown("---")
            
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.ChatInterface(
                        fn=run_agent,
                        type="messages",
                        textbox=gr.Textbox(
                            placeholder=f"Ask me to help with: {agent_task}...",
                            scale=7
                        ),
                    )
                
                with gr.Column(scale=1):
                    gr.Markdown("### Info")
                    gr.Markdown(f"""
**Agent Name:** {agent_name}
**Status:** Active
**Type:** Chat-based

**What I can do:**
- Answer questions
- Generate content
- Provide assistance
                    """)
            
            return interface
    
    @staticmethod
    def create_form_interface(agent_name: str, agent_task: str, fields: List[str], 
                             integrations: List[str], run_agent: Callable) -> gr.Blocks:
        """Create a form-based interface for the agent."""
        with gr.Blocks(theme=gr.themes.Soft(), title=f"Agent: {agent_name}") as interface:
            gr.Markdown(f"# 📝 {agent_name}")
            gr.Markdown(f"**Task:** {agent_task}")
            gr.Markdown("---")
            
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### Input")
                    
                    inputs = {}
                    field_components = []
                    
                    # Create dynamic input fields based on agent requirements
                    for field in fields:
                        if field == "recipient":
                            inputs[field] = gr.Textbox(
                                label="Recipient Email",
                                placeholder="name@example.com",
                                type="email"
                            )
                        elif field == "subject":
                            inputs[field] = gr.Textbox(
                                label="Subject Line",
                                placeholder="e.g., Project Update - Q1 2026"
                            )
                        elif field == "tone":
                            inputs[field] = gr.Dropdown(
                                choices=["Professional", "Friendly", "Formal", "Casual"],
                                label="Tone",
                                value="Professional"
                            )
                        elif field == "content_type":
                            inputs[field] = gr.Dropdown(
                                choices=["Article", "Post", "Story", "Video Caption", "Announcement"],
                                label="Content Type",
                                value="Post"
                            )
                        elif field == "platform":
                            inputs[field] = gr.Dropdown(
                                choices=["LinkedIn", "Twitter", "Facebook", "Instagram"],
                                label="Platform",
                                value="LinkedIn"
                            )
                        elif field == "title":
                            inputs[field] = gr.Textbox(
                                label="Title",
                                placeholder="Enter the title"
                            )
                        elif field == "format":
                            inputs[field] = gr.Dropdown(
                                choices=["Markdown", "HTML", "Plain Text", "PDF"],
                                label="Format",
                                value="Markdown"
                            )
                        elif field == "language":
                            inputs[field] = gr.Dropdown(
                                choices=["English", "Spanish", "French", "German", "Chinese"],
                                label="Language",
                                value="English"
                            )
                        
                        field_components.append(inputs[field])
                    
                    # Integration buttons
                    if integrations:
                        gr.Markdown("### Quick Actions")
                        with gr.Row():
                            for integration in integrations[:2]:  # Show max 2 buttons
                                service_name = integration.title()
                                gr.Button(f"📤 Send to {service_name}", scale=1)
                    
                    # Generate button
                    generate_btn = gr.Button("✨ Generate Content", variant="primary", scale=1)
                
                with gr.Column(scale=2):
                    gr.Markdown("### Output")
                    output_text = gr.Textbox(
                        label="Generated Content",
                        lines=15,
                        interactive=False,
                        show_copy_button=True
                    )
                    
                    # Action buttons for output
                    with gr.Row():
                        copy_btn = gr.Button("📋 Copy", scale=1)
                        if integrations:
                            use_btn = gr.Button("✨ Use Content", scale=1)
                    
                    gr.Markdown("### Tips")
                    gr.Markdown("""
- Customize the tone and style
- Add specific details  
- Click 'Use Content' to send directly
- Refine if needed
                    """)
            
            # Connect generate button
            def generate_with_fields(**field_values):
                return run_agent(**field_values)
            
            generate_btn.click(
                fn=generate_with_fields,
                inputs=field_components,
                outputs=output_text
            )
            
            return interface
    
    @staticmethod
    def generate_agent_ui(agent_name: str, agent_task: str, agent_type: Optional[str] = None,
                         run_agent: Callable = None) -> gr.Blocks:
        """Generate the appropriate UI for an agent."""
        
        if run_agent is None:
            run_agent = lambda **kwargs: "Agent not yet configured"
        
        # Detect agent type if not provided
        if not agent_type:
            agent_type = UIGenerator.detect_agent_type(agent_task)
        
        template = UIGenerator.AGENT_TEMPLATES.get(agent_type, UIGenerator.AGENT_TEMPLATES["general"])
        
        if template["type"] == "chat":
            return UIGenerator.create_chat_interface(agent_name, agent_task, run_agent)
        else:
            return UIGenerator.create_form_interface(
                agent_name,
                agent_task,
                template["fields"],
                template["integrations"],
                run_agent
            )     

    @staticmethod
    def create_agent_dashboard(agents_dict: Dict[str, Dict]) -> gr.Blocks:
        """Create a dashboard page listing all agents."""
        with gr.Blocks(theme=gr.themes.Soft(), title="Agent Dashboard") as dashboard:
            gr.Markdown("# 🤖 Agent Dashboard")
            gr.Markdown("**All your saved AI agents in one place**")
            gr.Markdown("---")
            
            # Create agent cards
            with gr.Column():
                for agent_name, agent_info in agents_dict.items():
                    with gr.Group():
                        gr.Markdown(f"### {agent_info.get('display_name', agent_name)}")
                        
                        with gr.Row():
                            gr.Markdown(f"""
**Department:** {agent_info.get('department', 'General')}
**Task:** {agent_info.get('task', 'No description')}
**Status:** Active
**Runs:** {agent_info.get('run_count', 0)}
                            """)
                            
                            open_btn = gr.Button("🚀 Open Agent", scale=1)
                            edit_btn = gr.Button("✏️ Edit", scale=1)
                            delete_btn = gr.Button("🗑️ Delete", scale=1)
            
            return dashboard
