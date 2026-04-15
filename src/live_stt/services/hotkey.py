from collections.abc import Callable

from pynput import keyboard

from .config import Config
from . import logger

log = logger.get(__name__)


# Keys that must be wrapped in <chevrons> for pynput hotkey format.
_PYNPUT_SPECIAL_KEYS = {
    "alt", "alt_l", "alt_r", "alt_gr",
    "ctrl", "ctrl_l", "ctrl_r",
    "shift", "shift_l", "shift_r",
    "cmd", "cmd_l", "cmd_r",
    "super", "super_l", "super_r",
    "tab", "enter", "space", "backspace", "delete",
    "esc", "escape",
    "up", "down", "left", "right",
    "home", "end", "page_up", "page_down",
    "insert", "print_screen", "scroll_lock", "pause",
    "caps_lock", "num_lock",
    "f1", "f2", "f3", "f4", "f5", "f6",
    "f7", "f8", "f9", "f10", "f11", "f12",
}


def normalize_hotkey(value: str) -> str:
    """Return *value* normalised to pynput's hotkey syntax.

    Strips whitespace, lowercases each part, and wraps recognised modifier /
    named keys in ``<chevrons>``.  E.g. ``"Ctrl + shift+z"`` becomes
    ``"<ctrl>+<shift>+z"``.  Already-wrapped parts are left untouched.
    """
    if not value:
        return value
    normalized = []
    for part in value.split("+"):
        part = part.strip().lower()
        bare = part.strip("<>").strip()
        if bare in _PYNPUT_SPECIAL_KEYS and not (
            part.startswith("<") and part.endswith(">")
        ):
            normalized.append(f"<{bare}>")
        else:
            normalized.append(part)
    return "+".join(normalized)


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
