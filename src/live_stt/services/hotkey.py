from collections.abc import Callable

from pynput import keyboard

from .config import Config
from . import logger

log = logger.get(__name__)


def start_hotkey_listener(
    hotkey_str: str, on_activate: Callable[[], None]
) -> keyboard.Listener:
    """Parse *hotkey_str* and start a pynput listener that fires *on_activate*.

    Centralises the canonical-key wrapping required by ``pynput.keyboard.HotKey``.
    Raises whatever ``keyboard.HotKey.parse`` raises on malformed input.
    """
    listener_cell: list[keyboard.Listener] = []
    hk = keyboard.HotKey(keyboard.HotKey.parse(hotkey_str), on_activate)

    def for_canonical(func):
        return lambda key: func(listener_cell[0].canonical(key))

    listener = keyboard.Listener(
        on_press=for_canonical(hk.press),
        on_release=for_canonical(hk.release),
    )
    listener_cell.append(listener)
    listener.start()
    return listener


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
        self._listener = start_hotkey_listener(self._hotkey_str, self._on_activate)
        log.info("Hotkey listener active: %s", self._hotkey_str)

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_config_changed(self, _changed: set[str]) -> None:
        self.stop()
        self.start()
