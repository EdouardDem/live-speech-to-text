from pynput import keyboard

from .config import Config
from . import logger

log = logger.get(__name__)


class HotkeyListener:
    """Listens for a global hotkey combination and fires a callback.

    ``hotkey_key`` is the attribute name on *config* that holds the hotkey
    string (e.g. ``"hotkey"`` or ``"translate_hotkey"``).  When the config is
    saved the listener automatically restarts with the new binding.
    """

    def __init__(self, config: Config, hotkey_key: str, on_activate):
        self._config = config
        self._hotkey_key = hotkey_key
        self._on_activate = on_activate
        self._listener: keyboard.Listener | None = None
        config.subscribe({hotkey_key}, self._on_config_changed)

    @property
    def _hotkey_str(self) -> str:
        return getattr(self._config, self._hotkey_key)

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

    def _on_config_changed(self, _changed: set[str]) -> None:
        self.stop()
        self.start()
