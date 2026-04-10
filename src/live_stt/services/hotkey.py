from pynput import keyboard

from . import logger

log = logger.get(__name__)


class HotkeyListener:
    """Listens for a global hotkey combination and fires a callback."""

    def __init__(self, hotkey_str: str, on_activate):
        self._hotkey_str = hotkey_str
        self._on_activate = on_activate
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(self._hotkey_str),
            self._on_activate,
        )
        self._listener = keyboard.Listener(
            on_press=self._for_canonical(hotkey.press),
            on_release=self._for_canonical(hotkey.release),
        )
        self._listener.start()
        log.info("Hotkey listener active: %s", self._hotkey_str)

    def _for_canonical(self, func):
        """Wrap key events through the listener's canonical mapping."""
        return lambda key: func(self._listener.canonical(key))

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
