import os
from jinja2 import Environment, FileSystemLoader

# Initialize Jinja2 environment
_env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

def get_system_prompt(stored_agents_list: str) -> str:
    """Render the system prompt with stored agents."""
    template = _env.get_template('system_prompt.jinja2')
    return template.render(stored_agents_list=stored_agents_list)

def get_code_gen_prompt(agent_name: str, display_name: str, department: str, task: str, trigger: str, output_type: str) -> str:
    """Render the code generation prompt."""
    template = _env.get_template('code_gen_prompt.jinja2')
    return template.render(
        agent_name=agent_name,
        display_name=display_name,
        department=department,
        task=task,
        trigger=trigger,
        output_type=output_type
    )
