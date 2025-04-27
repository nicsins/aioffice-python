import logging
from frontend.gui import App
import tkinter as tk

# Configure logging
logging.basicConfig(
    filename="logs/activity.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = App(root)
        logging.info("Application started")
        app.run()
    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        raise