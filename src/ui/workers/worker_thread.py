"""
Worker thread for background processing tasks.
"""
import logging
from typing import Callable, Any
from PySide6.QtCore import QThread, Signal

class Worker(QThread):
    """
    Worker thread for running background tasks.
    """
    # Signals for communication
    finished = Signal(object, str)  # Result, task_name
    error = Signal(str)             # Error message
    progress = Signal(int)          # Progress value (0-100)
    status = Signal(str)            # Status message
    
    def __init__(self, task_func: Callable, task_name: str, *args, **kwargs):
        """
        Initialize the worker thread.
        
        Args:
            task_func: The function to run in the background
            task_name: Name of the task for identification
            *args: Arguments to pass to the task function
            **kwargs: Keyword arguments to pass to the task function
        """
        super().__init__()
        self.task_func = task_func
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs
        self.is_interrupted = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def run(self):
        """
        Run the task function in the background.
        """
        result = None
        try:
            self.logger.info(f"Starting task: {self.task_name}")
            
            # Run the task function
            result = self.task_func(*self.args, **self.kwargs)
            self.logger.info(f"Task completed: {self.task_name}")
        except Exception as e:
            self.logger.exception(f"Error in task {self.task_name}: {e}")
            self.error.emit(str(e))
            result = None
        finally:
            # Emit the result
            self.finished.emit(result, self.task_name)
            
    def interrupt(self):
        """
        Signal the task to interrupt if possible.
        """
        self.is_interrupted = True
        self.logger.info(f"Task {self.task_name} interrupted")
    
    # --- Signal proxy methods ---
    def status_update(self, message):
        """Proxy for status_update signal"""
        self.status.emit(message)
    
    def warning(self, title, message):
        """Proxy for warning signal"""
        self.logger.warning(f"{title}: {message}")
    
    def caption_ready(self, caption):
        """Proxy for caption_ready signal"""
        self.logger.info(f"Caption ready: {caption[:50]}...")
    
    def show_toast(self, message):
        """Proxy for show_toast signal"""
        self.logger.info(f"Toast: {message}") 