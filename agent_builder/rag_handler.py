"""
RAG (Retrieval-Augmented Generation) handler for agents.
Manages knowledge base creation and retrieval for uploaded files.
"""

import os
import json
import shutil
from pathlib import Path


def process_uploaded_files(agent_dir: str, files) -> dict:
    """Process uploaded files and create knowledge base."""
    if not files:
        return {"status": "no_files", "files_count": 0}
    
    # Create knowledge_base directory
    kb_dir = os.path.join(agent_dir, "knowledge_base")
    os.makedirs(kb_dir, exist_ok=True)
    
    processed_files = []
    knowledge_base_content = []
    
    # Handle multiple files
    file_list = files if isinstance(files, list) else [files]
    
    for file_obj in file_list:
        try:
            # Get file path and name
            file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
            file_name = os.path.basename(file_path)
            
            # Copy to knowledge base
            dest_path = os.path.join(kb_dir, file_name)
            shutil.copy(file_path, dest_path)
            
            # Read content for text files
            if file_name.endswith(('.txt', '.md', '.csv', '.json')):
                with open(dest_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    knowledge_base_content.append({
                        "file": file_name,
                        "content": content[:5000]  # First 5000 chars
                    })
            
            processed_files.append(file_name)
        
        except Exception as e:
            print(f"Error processing file: {e}")
    
    # Create knowledge_base.json
    kb_data = {
        "files": processed_files,
        "content": knowledge_base_content,
        "created_at": str(Path(agent_dir).stat().st_mtime)
    }
    
    with open(os.path.join(kb_dir, "metadata.json"), "w") as f:
        json.dump(kb_data, f, indent=2)
    
    return {
        "status": "success",
        "files_count": len(processed_files),
        "files": processed_files
    }


def create_rag_prompt(agent_task: str, user_input: str, kb_content: list) -> str:
    """Create enhanced prompt with RAG context."""
    
    context = ""
    if kb_content:
        context = "\n\n**Reference Information:**\n"
        for item in kb_content:
            context += f"\nFrom {item.get('file')}:\n{item.get('content', '')[:1000]}\n"
    
    return f"""You are an AI agent. Your job is to {agent_task}.

{context}

User Request: {user_input}

Based on the reference information above (if provided), answer the user's request. 
If information is not in the reference materials, use your general knowledge.
Always be clear and professional."""


def load_knowledge_base(agent_dir: str) -> list:
    """Load knowledge base content for an agent."""
    kb_file = os.path.join(agent_dir, "knowledge_base", "metadata.json")
    
    if not os.path.exists(kb_file):
        return []
    
    try:
        with open(kb_file, 'r') as f:
            data = json.load(f)
            return data.get("content", [])
    except:
        return []
