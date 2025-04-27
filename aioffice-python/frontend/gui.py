pass
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime
from src.agents import BossAgent
from src.database import Database

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Agent Task Manager")
        self.root.geometry("800x600")

        # Initialize database and agent
        self.db = Database()
        self.boss_agent = BossAgent()

        # Create menu
        self.create_menu()

        # Create main frames
        self.create_ui()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Display Tasks", command=self.display_tasks)
        view_menu.add_command(label="View Logs", command=self.view_logs)

        feedback_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Feedback", menu=feedback_menu)
        feedback_menu.add_command(label="Submit Feedback", command=self.show_feedback_form)

    def create_ui(self):
        # Main frame for content
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Response area
        self.response_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
        self.response_text.grid(row=0, column=0, padx=5, pady=5)

        # Button to process tasks
        ttk.Button(main_frame, text="Process Pending Tasks", command=self.process_tasks).grid(row=1, column=0, pady=5)

    def display_tasks(self):
        tasks = self.db.get_pending_tasks()
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, "Pending Tasks:\n" + "\n".join(tasks))

    def view_logs(self):
        with open("logs/activity.log", "r") as f:
            logs = f.read()
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, "Activity Logs:\n" + logs)

    def show_feedback_form(self):
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title("Submit Feedback")
        feedback_window.geometry("400x200")

        ttk.Label(feedback_window, text="Your Feedback:").grid(row=0, column=0, padx=5, pady=5)
        feedback_entry = ttk.Entry(feedback_window, width=40)
        feedback_entry.grid(row=1, column=0, padx=5, pady=5)

        def submit_feedback():
            feedback = feedback_entry.get()
            if feedback:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"{timestamp} - Feedback: {feedback}\n"
                with open("logs/activity.log", "a") as f:
                    f.write(log_entry)
                messagebox.showinfo("Success", "Feedback submitted!")
                feedback_window.destroy()
            else:
                messagebox.showwarning("Warning", "Please enter feedback.")

        ttk.Button(feedback_window, text="Submit", command=submit_feedback).grid(row=2, column=0, pady=5)

    def process_tasks(self):
        def worker():
            self.boss_agent.assign_tasks()
            self.display_tasks()

        thread = threading.Thread(target=worker)
        thread.start()

    def run(self):
        self.root.mainloop()