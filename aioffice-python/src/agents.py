import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from database import Database
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import os  # Ensure os is imported for file operations if needed
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(
    filename="logs/activity.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class GoogleDriveHandler:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self):
        self.service = self.authenticate()

    def authenticate(self):
        try:
            creds = None
            # Load credentials from token.json if it exists
            if Path('token.json').exists():
                creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            # If no valid credentials, prompt user to log in
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
                # Save credentials for next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            logging.error(f"Failed to authenticate Google Drive: {e}")
            raise

    def execute_task(self, params):
        try:
            local_path = params.get("local_path")
            folder_id = params.get("folder_id")  # Optional: Google Drive folder ID
            if not local_path or not Path(local_path).exists():
                raise ValueError("Valid local_path is required")

            file_name = Path(local_path).name
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(local_path)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            file_id = file.get('id')
            web_link = file.get('webViewLink')
            logging.info(f"Uploaded {file_name} to Google Drive, ID: {file_id}")
            return f"Uploaded {file_name} to Google Drive: {web_link}"
        except Exception as e:
            logging.error(f"Google Drive upload failed: {e}")
            return f"Error: {e}"

class BrowserHandler:
    def execute_task(self, params):
        try:
            # Example implementation for BrowserHandler
            url = params.get("url")
            if not url:
                raise ValueError("URL is required for browser tasks")

            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            page_title = driver.title
            driver.quit()

            logging.info(f"Browser task completed. Page title: {page_title}")
            return f"Page title: {page_title}"
        except Exception as e:
            logging.error(f"BrowserHandler task failed: {e}")
            return f"Error: {e}"

# ... (Previous BrowserHandler classes unchanged)

class FileHandler:
    def execute_task(self, params):
        try:
            file_path = params.get("file_path")
            if not file_path or not Path(file_path).exists():
                raise ValueError("Valid file_path is required")

            with open(file_path, 'r') as file:
                content = file.read()

            logging.info(f"FileHandler read file: {file_path}")
            return f"File content: {content}"
        except Exception as e:
            logging.error(f"FileHandler task failed: {e}")
            return f"Error: {e}"

class BossAgent:
    def __init__(self, max_workers=4):
        self.db = Database()
        self.max_workers = max_workers
        self.lock = threading.Lock()
        logging.info("BossAgent initialized")

    def assign_tasks(self):
        try:
            schedule_agent = ScheduleAgent()
            subtasks = schedule_agent.get_subtasks()
            if not subtasks:
                logging.info("No pending tasks to assign")
                return

                    # Ensure proper indentation or remove the line if unnecessary
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self.run_worker, task["id"], task["task_type"], task["requirements"], task["parameters"])
                    for task in subtasks
                ]
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"Worker task failed: {e}")
        except Exception as e:
            logging.error(f"Error in assign_tasks: {e}")

    def run_worker(self, task_id, task_type, requirements, parameters):
        worker = WorkerAgent(task_id, task_type, requirements, parameters, self.lock)
        worker.execute_task()

class ScheduleAgent:
    def __init__(self):
        self.db = Database()
        logging.info("ScheduleAgent initialized")

    def get_subtasks(self):
        try:
            tasks = self.db.get_pending_tasks_with_id()
            logging.info(f"Retrieved {len(tasks)} pending tasks")
            return [
                {
                    "id": task[0],
                    "task_type": task[1],
                    "requirements": task[2],  # Fixed index for requirements
                    "parameters": json.loads(task[3]) if task[3] else {}
                }
                for task in tasks
            ]
        except Exception as e:
            logging.error(f"Error retrieving subtasks: {e}")
            return []

class WorkerAgent:
    def __init__(self, task_id, task_type, requirements, parameters, db_lock):
        self.task_id = task_id
        self.task_type = task_type
        self.requirements = requirements
        self.parameters = parameters
        self.db = Database()
        self.db_lock = db_lock
        logging.info(f"WorkerAgent-{task_id} initialized for task {task_id} (type: {task_type})")

    def execute_task(self):
        try:
            logging.info(f"WorkerAgent-{self.task_id} executing {self.task_type} task: {self.requirements}")
            
            if self.task_type == "browser":
                handler = BrowserHandler()
                result = handler.execute_task(self.parameters)
            elif self.task_type == "file":
                handler = FileHandler()
                result = handler.execute_task(self.parameters)
            elif self.task_type == "gdrive":
                handler = GoogleDriveHandler()
                result = handler.execute_task(self.parameters)
            else:  # generic
                sleep(2)
                result = f"Completed generic task {self.task_id} with requirements {self.requirements}"

            with self.db_lock:
                self.db.update_task_status(self.task_id, "completed", result)
                        
            logging.info(f"WorkerAgent-{self.task_id} completed task")
        except Exception as e:
            error_result = f"Error: {e}"
            with self.db_lock:
                self.db.update_task_status(self.task_id, "failed", error_result)
            logging.error(f"WorkerAgent-{self.task_id} failed: {e}")