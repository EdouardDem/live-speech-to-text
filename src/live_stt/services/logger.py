"""Centralized logger — routes log records to the GUI and optionally to the console."""

import logging
import sys
from typing import Callable

_LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"

# Callback signature: (formatted_message: str) -> None
_gui_callback: Callable[[str], None] | None = None
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


def set_gui_callback(callback: Callable[[str], None]) -> None:
    """Register the function that receives formatted log lines for the GUI."""
    global _gui_callback
    _gui_callback = callback


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
