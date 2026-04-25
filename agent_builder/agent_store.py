import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path


DB_FILE = "agents.db"
AGENTS_DIR = "saved_agents"


def init_db():
    """Initialize SQLite database for agents."""
    if not os.path.exists(AGENTS_DIR):
        os.makedirs(AGENTS_DIR)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS agents
                 (agent_name TEXT PRIMARY KEY,
                  display_name TEXT,
                  department TEXT,
                  task TEXT,
                  trigger TEXT,
                  output_type TEXT,
                  created_at TEXT,
                  run_count INTEGER,
                  agent_dir TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS agent_memory
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  agent_name TEXT,
                  task TEXT,
                  output TEXT,
                  created_at TIMESTAMP,
                  FOREIGN KEY(agent_name) REFERENCES agents(agent_name))''')
                  
    conn.commit()
    conn.close()


def save_agent(spec: dict, agent_dir: str = None) -> dict:
    """Save agent metadata to database and create agent directory."""
    init_db()
    
    agent_name = spec.get("agent_name")
    
    # Create agent directory if not provided
    if not agent_dir:
        agent_dir = os.path.join(AGENTS_DIR, agent_name)
        if not os.path.exists(agent_dir):
            os.makedirs(agent_dir)
    
    agent_data = {
        **spec,
        "created_at": datetime.utcnow().isoformat(),
        "agent_dir": agent_dir
    }
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO agents 
                 (agent_name, display_name, department, task, trigger, output_type, created_at, run_count, agent_dir)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (agent_name, spec.get("display_name"), spec.get("department"),
               spec.get("task"), spec.get("trigger"), spec.get("output_type"),
               agent_data["created_at"], 0, agent_dir))
    conn.commit()
    conn.close()
    
    return agent_data


def load_all_agents() -> str:
    """Load all agents and return formatted list for prompt injection."""
    init_db()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT display_name, department, task FROM agents')
    agents = c.fetchall()
    conn.close()
    
    if not agents:
        return "No agents saved yet."
    
    agents_list = []
    for display_name, department, task in agents:
        agents_list.append(f"• {display_name}: {task} (for {department})")
    
    return "\n".join(agents_list)


def get_agent(agent_name: str) -> dict:
    """Get agent metadata by name."""
    init_db()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM agents WHERE agent_name = ?', (agent_name,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "agent_name": row[0],
        "display_name": row[1],
        "department": row[2],
        "task": row[3],
        "trigger": row[4],
        "output_type": row[5],
        "created_at": row[6],
        "run_count": row[7],
        "agent_dir": row[8]
    }


def increment_run(agent_name: str) -> None:
    """Increment run count for an agent."""
    init_db()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE agents SET run_count = run_count + 1 WHERE agent_name = ?', (agent_name,))
    conn.commit()
    conn.close()


def delete_agent(agent_name: str) -> bool:
    """Delete an agent from DB and filesystem."""
    try:
        init_db()
        
        # Get agent dir
        agent = get_agent(agent_name)
        if agent and agent.get("agent_dir") and os.path.exists(agent.get("agent_dir")):
            import shutil
            shutil.rmtree(agent.get("agent_dir"))

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM agents WHERE agent_name = ?', (agent_name,))
        c.execute('DELETE FROM agent_memory WHERE agent_name = ?', (agent_name,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting agent: {e}")
        return False



def get_all_agents_list() -> list:
    """Get list of all agents."""
    init_db()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM agents')
    rows = c.fetchall()
    conn.close()
    
    agents = []
    for row in rows:
        agents.append({
            "agent_name": row[0],
            "display_name": row[1],
            "department": row[2],
            "task": row[3],
            "trigger": row[4],
            "output_type": row[5],
            "created_at": row[6],
            "run_count": row[7],
            "agent_dir": row[8]
        })
    
    return agents


def save_agent_code(agent_name: str, agent_py: str, config_py: str, readme_md: str, requirements_txt: str) -> str:
    """Save generated agent code to directory."""
    agent_dir = os.path.join(AGENTS_DIR, agent_name)
    if not os.path.exists(agent_dir):
        os.makedirs(agent_dir)
    
    with open(os.path.join(agent_dir, "agent.py"), "w") as f:
        f.write(agent_py)
    
    with open(os.path.join(agent_dir, "config.py"), "w") as f:
        f.write(config_py)
    
    with open(os.path.join(agent_dir, "README.md"), "w") as f:
        f.write(readme_md)
    
    with open(os.path.join(agent_dir, "requirements.txt"), "w") as f:
        f.write(requirements_txt)
    
    return agent_dir

# ========== LONG TERM MEMORY ==========

def append_agent_memory(agent_name: str, task: str, output: str):
    """Append a new memory entry regarding execution result to SQLite."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # Insert into agent_memory table
        c.execute('''
            INSERT INTO agent_memory (agent_name, task, output, created_at)
            VALUES (?, ?, ?, ?)
        ''', (agent_name, task, output, timestamp))
        
        conn.commit()
        conn.close()
        print(f"✅ Memory saved to DB for {agent_name}")
    except Exception as e:
        print(f"Error saving memory to DB: {e}")

def load_agent_memory(agent_name: str, limit: int = 5) -> str:
    """Load recent memory string for prompt context from SQLite."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Get last N memories for this agent
        c.execute('''
            SELECT task, output, created_at 
            FROM agent_memory 
            WHERE agent_name = ? 
            ORDER BY id DESC 
            LIMIT ?
        ''', (agent_name, limit))
        
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return ""
            
        # Reverse rows to show chronological order (oldest first) in prompt
        # rows are (task, output, created_at)
        rows.reverse()
        
        context_str = "\n===== LONG-TERM MEMORY (PREVIOUS RUNS) =====\n"
        for i, row in enumerate(rows):
            task_text = row[0]
            output_text = row[1]
            ts = row[2]
            
            # Format timestamp for readability
            if ts:
                ts = ts[:16].replace("T", " ")
            
            # Truncate very long outputs to save context
            out_preview = output_text
            if len(out_preview) > 500:
                out_preview = out_preview[:500] + "..."
                
            context_str += f"[RUN {-(len(rows)-i)}] {ts}\nTASK: {task_text}\nRESULT: {out_preview}\n---\n"
        
        context_str += "============================================\n"
        
        return context_str
    except Exception as e:
        print(f"Error reading memory from DB: {e}")
        return ""

