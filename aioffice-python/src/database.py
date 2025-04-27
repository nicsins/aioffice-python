from sqlite3 import Binary
import psycopg2
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="logs/activity.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class Database:
    def __init__(self):
        self.db_params = {
            "dbname": os.getenv("DB_NAME", "mydb"),
            "user": os.getenv("DB_USER", "myuser"),
            "password": os.getenv("DB_PASS", "mypass"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432")
        }
        self.connection = None
        self.connect()
        logging.info("Database initialized")

    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.db_params)
            logging.info("Database connection established")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise

    def get_pending_tasks_with_id(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id, requirements FROM tasks WHERE status='pending'")
                tasks = cursor.fetchall()
                return tasks
        except Exception as e:
            logging.error(f"Error fetching pending tasks: {e}")
            return []

    def get_pending_tasks(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT requirements FROM tasks WHERE status='pending'")
                tasks = [row[0] for row in cursor.fetchall()]
                return tasks
        except Exception as e:
            logging.error(f"Error fetching pending tasks: {e}")
            return []

    def update_task_status(self, task_id, status, result):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE tasks SET status=%s, result=%s WHERE id=%s",
                    (status, result, task_id)
                )
                self.connection.commit()
                logging.info(f"Updated task {task_id} to status {status}")
        except Exception as e:
            logging.error(f"Error updating task {task_id}: {e}")
            self.connection.rollback()

    def __del__(self):
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")