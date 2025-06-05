"""
Worker signal classes used for background processing and communication.
"""
import logging
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap

class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    finished = Signal(object)
    error = Signal(str, str)
    warning = Signal(str, str)
    info = Signal(str, str)
    status_update = Signal(str)
    progress = Signal(int)
    processing_state = Signal(bool)
    preview_ready = Signal(QPixmap, object, bool)
    caption_ready = Signal(str)
    context_list_ready = Signal(list)
    sold_out_list_ready = Signal(list)
    instructions_ready = Signal(str, bool)
    single_file_uploaded_for_preview = Signal(str)
    library_update_needed = Signal()
    show_toast = Signal(str)  # Signal to show toast notification
    log = Signal(str) 