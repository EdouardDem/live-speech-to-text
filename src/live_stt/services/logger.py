"""Centralized logger — routes log records to the GUI and optionally to the console."""

import logging
import sys
from typing import Callable

_LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"

# Callback signature: (formatted_message: str) -> None
_gui_callback: Callable[[str], None] | None = None
_model_gui_callback: Callable[[str], None] | None = None
_console_handler: logging.StreamHandler | None = None
_formatter = logging.Formatter(_LOG_FORMAT)


class _GuiHandler(logging.Handler):
    """Logging handler that forwards formatted records to the GUI."""

    def emit(self, record: logging.LogRecord) -> None:
        if _gui_callback is not None:
            try:
                msg = self.format(record)
                _gui_callback(msg)
            except Exception:
                pass


class _ModelGuiHandler(logging.Handler):
    """Logging handler that forwards NeMo records to the Model Logs GUI."""

    def emit(self, record: logging.LogRecord) -> None:
        if _model_gui_callback is not None:
            try:
                msg = self.format(record)
                _model_gui_callback(msg)
            except Exception:
                pass


def setup(*, verbose: bool = False, console: bool = True) -> None:
    """Configure the root logger with our handlers.

    Call once at startup. The GUI callback can be attached later via
    ``set_gui_callback``.
    """
    global _console_handler

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    # Remove any pre-existing handlers
    root.handlers.clear()

    # Console handler (can be toggled on/off)
    _console_handler = logging.StreamHandler(sys.stderr)
    _console_handler.setFormatter(_formatter)
    if console:
        root.addHandler(_console_handler)

    # GUI handler (always active — silently no-ops until callback is set)
    gui_handler = _GuiHandler()
    gui_handler.setFormatter(_formatter)
    root.addHandler(gui_handler)


def capture_nemo_logs() -> None:
    """Intercept NeMo's own logger.

    Triggers NeMo logger initialization (by importing ``nemo.utils``),
    then removes its console stream handlers and adds our handler so
    records are routed to the Model Logs GUI tab instead.

    Must be called **before** any NeMo operation that produces log output
    (e.g. model loading).
    """
    # Importing nemo.utils triggers the singleton Logger which creates
    # the "nemo_logger" Python logger with its own stream handlers.
    import nemo.utils  # noqa: F401

    nemo_logger = logging.getLogger("nemo_logger")
    # Remove NeMo's stdout/stderr stream handlers
    for handler in list(nemo_logger.handlers):
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, (logging.FileHandler, logging.handlers.MemoryHandler)
        ):
            nemo_logger.removeHandler(handler)
    # Add our handler for the Model Logs tab
    model_handler = _ModelGuiHandler()
    model_handler.setFormatter(_formatter)
    nemo_logger.addHandler(model_handler)


def set_gui_callback(callback: Callable[[str], None]) -> None:
    """Register the function that receives formatted log lines for the GUI."""
    global _gui_callback
    _gui_callback = callback


def set_model_gui_callback(callback: Callable[[str], None]) -> None:
    """Register the function that receives NeMo/model log lines for the GUI."""
    global _model_gui_callback
    _model_gui_callback = callback


def set_console_enabled(enabled: bool) -> None:
    """Enable or disable the console output at runtime."""
    root = logging.getLogger()
    if enabled and _console_handler not in root.handlers:
        root.addHandler(_console_handler)
    elif not enabled and _console_handler in root.handlers:
        root.removeHandler(_console_handler)


def get(name: str) -> logging.Logger:
    """Return a named logger (convenience wrapper)."""
    return logging.getLogger(name)
