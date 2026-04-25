import os
import json
import requests
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv()

# We use Ollama native API for simple completions
OLLAMA_URL = "http://localhost:11434/api/generate"

def analyze_intent(user_input):
    """
    Ask LLM to extract image path and caption from user input.
    """
    prompt = f"Extract 'image_path' and 'caption' from: '{user_input}'. Return ONLY valid JSON. If no image path is found, return empty JSON."
    payload = {
        "model": os.getenv("LLM_MODEL", "qwen3:4b"),
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "{}")
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "{}"

async def run_agent():
    # Start MCP Server as a subprocess
    server_params = StdioServerParameters(
        command="python",
        args=["ig_mcp_server.py"],
        env=os.environ
    )

    print("Connecting to Instagram MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            try:
                await session.initialize()
            except Exception as e:
                print(f"Failed to initialize MCP session: {e}")
                return

            print("\n--- Instagram Auto-Poster Ready ---")
            print("Commands: 'Post [image.jpg] with caption [text]', or 'exit'")
            
            # List tools for confirmation
            try:
                tools_result = await session.list_tools()
                # Use .tools attribute of the result object
                tool_names = [t.name for t in tools_result.tools] if tools_result else []
                print(f"Loaded tools: {tool_names}")
            except Exception as e:
                print(f"Warning: Could not list tools: {e}")

            while True:
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                    
                # 1. Analyze intent
                print("Thinking...")
                intent_raw = analyze_intent(user_input)
                
                # Cleanup markdown code blocks if present
                if "```" in intent_raw:
                    intent_raw = intent_raw.split("```")[1]
                    if intent_raw.startswith("json"):
                        intent_raw = intent_raw[4:]
                
                intent = {}
                try:
                    intent = json.loads(intent_raw)
                    print(f"Plan: {intent}")
                except:
                    print(f"Could not understand request. Raw intent: {intent_raw}")
                    continue
                
                # 2. Execute Action
                if intent.get("image_path") and intent.get("caption"):
                    image_path = intent["image_path"]
                    caption = intent["caption"]
                    
                    print(f"Executing: Upload '{image_path}'...")
                    
                    try:
                        # Call MCP Tool
                        # The tool expects 'post_photo(image_path, caption)'
                        result = await session.call_tool("post_photo", arguments={
                            "image_path": image_path,
                            "caption": caption
                        })
                        
                        # Handle result
                        # MCP results are usually a list of content items
                        if result and hasattr(result, 'content') and result.content:
                             print(f"\nSERVER RESPONSE:\n{result.content[0].text}")
                        else:
                             print(f"\nSERVER RESPONSE:\n{result}")

                    except Exception as e:
                        print(f"Error calling tool: {e}")
                else:
                    print("Please provide both an image path and a caption.")

if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\nGoodbye.")
