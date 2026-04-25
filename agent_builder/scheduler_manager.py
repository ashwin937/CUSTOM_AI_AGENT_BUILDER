import schedule
import time
import threading
import logging
import json
import os
from datetime import datetime
import re
from openai import OpenAI
from gmail_automation import get_gmail_automation
from integrations import LinkedInIntegration, InstagramIntegration
from agent_store import load_agent_memory, append_agent_memory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File to store persistent jobs
JOBS_FILE = "scheduled_jobs.json"

class SchedulerManager:
    def __init__(self, run_interval=1, client=None):
        self.run_interval = run_interval
        self.stop_event = threading.Event()
        self.thread = None
        self.jobs = []
        self.client = client
        self.load_jobs()
            
    def load_jobs(self):
        """Load jobs from persistent storage."""
        if os.path.exists(JOBS_FILE):
            try:
                with open(JOBS_FILE, 'r') as f:
                    self.jobs = json.load(f)
                logger.info(f"Loaded {len(self.jobs)} scheduled jobs.")
            except Exception as e:
                logger.error(f"Failed to load jobs: {e}")

    def save_jobs(self):
        """Save current jobs to file."""
        try:
            with open(JOBS_FILE, 'w') as f:
                json.dump(self.jobs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")

    def add_job(self, agent_name, task, schedule_type, time_value, params=None):
        """Add a new scheduled job."""
        
        # Check if job already exists for this agent
        existing = next((j for j in self.jobs if j["agent"] == agent_name), None)
        if existing:
            # Update existing job
            existing.update({
                "function": task,
                "type": schedule_type,
                "time": time_value,
                "params": params or {},
                "active": True
            })
            self.save_jobs()
            self._schedule_job_internal(existing)
            logger.info(f"Updated scheduled job: {existing['id']}")
            return existing['id']
            
        job_id = f"{agent_name}_{int(time.time())}"
        job_data = {
            "id": job_id,
            "agent": agent_name,
            "function": task,
            "type": schedule_type,  # 'daily', 'hourly', 'interval'
            "time": time_value,     # '09:00', '1' (hour), '30' (minutes)
            "params": params or {},
            "active": True,
            "last_run": None,
            "last_output": None
        }
        self.jobs.append(job_data)
        self.save_jobs()
        self._schedule_job_internal(job_data)
        logger.info(f"Scheduled job added: {job_id}")
        return job_id
    
    def process_actions(self, output: str):
        """Parse output and perform actions like Email, LinkedIn, Instagram."""
        try:
             # EMAIL
             if "To:" in output and "Subject:" in output and "Body:" in output:
                 logger.info("Found Email Action in output.")
                 try:
                     to_match = re.search(r"To:\s*(.+)", output)
                     sub_match = re.search(r"Subject:\s*(.+)", output)
                     body_match = re.search(r"Body:\s*(.+)", output, re.DOTALL)
                     
                     if to_match and sub_match:
                         to_addr = to_match.group(1).strip()
                         subject = sub_match.group(1).strip()
                         body = body_match.group(1).strip() if body_match else output
                         
                         gmail = get_gmail_automation()
                         if gmail and gmail.is_authenticated():
                             result = gmail.send_email(to_addr, subject, body)
                             if result:
                                 logger.info(f"✅ Scheduled Email sent to {to_addr}")
                             else:
                                 logger.error(f"❌ Failed to send email to {to_addr}: send_email returned False")
                         else:
                             logger.error(f"❌ Gmail not authenticated. Cannot send email to {to_addr}")
                 except Exception as ex:
                     logger.error(f"Failed to send email: {ex}")

             # LINKEDIN
             if "LinkedIn Post:" in output:
                 logger.info("Found LinkedIn Action in output.")
                 try:
                     li = LinkedInIntegration() # Requires token in env or cache
                     post_content = output.split("LinkedIn Post:", 1)[1].strip()
                     li.post_update(post_content)
                     logger.info("Scheduled LinkedIn post created.")
                 except Exception as ex:
                     logger.error(f"Failed to post to LinkedIn: {ex}")

             # INSTAGRAM
             if "Instagram Post:" in output or "Instagram:" in output:
                 logger.info("Found Instagram Action in output.")
                 try:
                     ig = InstagramIntegration() # Uses updated logic with Selenium support
                     # Handle Markdown bolding or plain text (e.g. **Image:** or Image:)
                     img_match = re.search(r"(?:\*\*Image\*\*|Image|File):\s*(.+)", output, re.IGNORECASE)
                     cap_match = re.search(r"(?:\*\*Caption\*\*|Caption):\s*(.+)", output, re.IGNORECASE)
                     
                     if img_match:
                         img_path = img_match.group(1).strip()
                         caption = cap_match.group(1).strip() if cap_match else ""
                         
                         logger.info(f"Attempting to post to Instagram: {img_path}")
                         res = ig.post_photo(img_path, caption)
                         
                         if isinstance(res, dict) and "success" in res:
                             logger.info("Scheduled Instagram post created successfully.")
                         elif isinstance(res, dict) and "error" in res:
                             logger.error(f"Instagram Post Failed: {res['error']}")
                         else:
                             logger.info(f"Instagram Post Result: {res}")
                     else:
                         logger.warning("Instagram action found but local image path/url could not be extracted.")
                 except Exception as ex:
                     logger.error(f"Failed to post to Instagram: {ex}")

        except Exception as e:
            logger.error(f"Error processing actions: {e}")

    def execute_agent_task(self, job_data):
        """
        Execute the agent logic.
        """
        agent_name = job_data['agent']
        task = job_data['function']
        logger.info(f"Running scheduled job: {job_data['id']} for agent {agent_name}")
        
        try:
            if not self.client:
                 logger.error("No OpenAI client available for scheduler.")
                 return

            # Retrieve Memory
            memory_context = load_agent_memory(agent_name)
            
            system_msg = (f"You are an automated AI agent named {agent_name}. "
                          f"Your scheduled task is: {task}.\n"
                          f"{memory_context}\n"
                          f"Use the memory above to avoid repeating yourself or to continue where you left off.\n"
                          f"If the task requires sending an email, use this format:\n"
                          f"To: [email]\nSubject: [subject]\nBody: [body]\n"
                          f"If posting to LinkedIn, use: LinkedIn Post: [content]\n"
                          f"If posting to Instagram, use: Instagram Post:\nImage: [url]\nCaption: [caption]")
            
            user_msg = "Please execute your scheduled task now."
            
            # Using qwen3:4b as seen in app.py or fallback
            model = os.getenv("LLM_MODEL", "qwen3:4b") 
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )
            
            output = response.choices[0].message.content
            logger.info(f"Agent {agent_name} output: {output}")
            
            # Save run details
            job_data['last_run'] = datetime.now().isoformat()
            job_data['last_output'] = output
            self.save_jobs()
            
            # Update Memory
            append_agent_memory(agent_name, task, output)
            
            # Process Actions
            self.process_actions(output)
                
        except Exception as e:
            logger.error(f"Error executing job {job_data['id']}: {e}")


    def _schedule_job_internal(self, job_data):
        """Internal method to register a job with the schedule library."""
        if not job_data.get("active"):
            return

        def job_wrapper():
            self.execute_agent_task(job_data)

        try:
            val = job_data['time']
            if job_data['type'] == 'daily':
                schedule.every().day.at(val).do(job_wrapper)
            elif job_data['type'] == 'hourly':
                schedule.every().hour.do(job_wrapper)
            elif job_data['type'] == 'interval':
                minutes = int(val)
                schedule.every(minutes).minutes.do(job_wrapper)
        except Exception as e:
            logger.error(f"Error scheduling job {job_data['id']}: {e}")

    def start(self):
        """Start the scheduler loop in a background thread."""
        if self.thread and self.thread.is_alive():
            logger.warning("Scheduler already running.")
            return

        # Register all loaded jobs
        schedule.clear()
        for job in self.jobs:
            self._schedule_job_internal(job)

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Scheduler started.")

    def stop(self):
        """Stop the scheduler loop."""
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        logger.info("Scheduler stopped.")

    def _run_loop(self):
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(self.run_interval)
