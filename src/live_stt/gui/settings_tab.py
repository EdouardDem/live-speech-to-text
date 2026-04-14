"""Settings tab — edit and persist configuration."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..services.config import Config
from ..services import logger

log = logger.get(__name__)

# -- UI texts ----------------------------------------------------------------

_TXT_SAVE_BTN = "Save settings"
_TXT_SAVE_MESSAGE = (
    "Settings saved. You may need to restart the application for all "
    "changes to take effect."
)
_TXT_SECTION_GENERAL = "General"
_TXT_SECTION_API_KEYS = "API Keys"

_TXT_LBL_HOTKEY = "Hotkey"
_TXT_LBL_MODEL = "Model"
_TXT_LBL_DEVICE = "Device"
_TXT_LBL_PASTE_METHOD = "Paste method"
_TXT_LBL_PASTE_SHORTCUT = "Paste shortcut"
_TXT_LBL_LOG_TO_CONSOLE = "Output logs to console"
_TXT_LBL_ANTHROPIC_KEY = "Anthropic API key"
_TXT_LBL_DEEPL_KEY = "DeepL API key"

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

_HOTKEY_FIELDS = {"hotkey"}


def _normalize_hotkey(value: str) -> str:
    """Ensure each part of a hotkey string has chevrons where needed.

    E.g. ``"ctrl+shift+z"`` becomes ``"<ctrl>+<shift>+z"``.
    Already-wrapped parts like ``"<ctrl>"`` are left untouched.
    """
    parts = [p.strip().lower() for p in value.split("+")]
    normalized = []
    for part in parts:
        bare = part.strip("<>").lower().strip()
        if bare in _PYNPUT_SPECIAL_KEYS and not (part.startswith("<") and part.endswith(">")):
            normalized.append(f"<{bare}>")
        else:
            normalized.append(part)
    return "+".join(normalized)

_GENERAL_SPEC = [
    ("hotkey", _TXT_LBL_HOTKEY, "entry"),
    ("model_name", _TXT_LBL_MODEL, "entry"),
    ("device", _TXT_LBL_DEVICE, "combo", ["auto", "cpu", "cuda"]),
    ("paste_method", _TXT_LBL_PASTE_METHOD, "combo", ["auto", "xclip", "xdotool", "wayland"]),
    ("paste_shortcut", _TXT_LBL_PASTE_SHORTCUT, "combo", ["ctrl+shift+v", "ctrl+v"]),
    ("log_to_console", _TXT_LBL_LOG_TO_CONSOLE, "toggle"),
]

_API_KEYS_SPEC = [
    ("anthropic_api_key", _TXT_LBL_ANTHROPIC_KEY, "password"),
    ("deepl_api_key", _TXT_LBL_DEEPL_KEY, "password"),
]


def _build_section(title: str, specs: list, config: Config, entries: dict) -> Gtk.Frame:
    frame = Gtk.Frame(label=title)
    frame.set_shadow_type(Gtk.ShadowType.NONE)
    frame.set_label_align(0.0, 0.5)

    grid = Gtk.Grid()
    grid.set_column_spacing(12)
    grid.set_row_spacing(8)
    grid.set_margin_top(8)
    grid.set_margin_bottom(8)
    grid.set_margin_start(12)
    grid.set_margin_end(12)

    for row, item in enumerate(specs):
        key, label_text, kind = item[0], item[1], item[2]
        label = Gtk.Label(label=label_text, xalign=0)
        grid.attach(label, 0, row, 1, 1)

        current_value = str(getattr(config, key))

        if kind == "combo":
            combo = Gtk.ComboBoxText()
            for opt in item[3]:
                combo.append_text(opt)
            combo.set_active(
                item[3].index(current_value) if current_value in item[3] else 0
            )
            combo.set_hexpand(True)
            grid.attach(combo, 1, row, 1, 1)
            entries[key] = combo
        elif kind == "password":
            entry = Gtk.Entry()
            entry.set_text(current_value)
            entry.set_visibility(False)
            entry.set_invisible_char('\u2022')
            entry.set_hexpand(True)
            grid.attach(entry, 1, row, 1, 1)
            entries[key] = entry
        elif kind == "toggle":
            switch = Gtk.Switch()
            switch.set_active(getattr(config, key) is True)
            switch.set_halign(Gtk.Align.START)
            grid.attach(switch, 1, row, 1, 1)
            entries[key] = switch
        else:
            entry = Gtk.Entry()
            entry.set_text(current_value)
            entry.set_hexpand(True)
            grid.attach(entry, 1, row, 1, 1)
            entries[key] = entry

    frame.add(grid)
    return frame

class SettingsTab(Gtk.ScrolledWindow):
    def __init__(self, config: Config, on_save):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._cfg = config
        self._on_save = on_save
        self._entries: dict[str, Gtk.Entry | Gtk.ComboBoxText] = {}

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        box.pack_start(
            _build_section(_TXT_SECTION_GENERAL, _GENERAL_SPEC, config, self._entries),
            False, False, 0,
        )
        box.pack_start(
            _build_section(_TXT_SECTION_API_KEYS, _API_KEYS_SPEC, config, self._entries),
            False, False, 0,
        )

        save_btn = Gtk.Button(label=_TXT_SAVE_BTN)
        save_btn.connect("clicked", self._on_save_clicked)
        box.pack_start(save_btn, False, False, 0)

        self._info_label = Gtk.Label()
        self._info_label.set_no_show_all(True)
        box.pack_start(self._info_label, False, False, 0)

        self.add(box)

    def _on_save_clicked(self, _btn: Gtk.Button) -> None:
        for key, widget in self._entries.items():
            if isinstance(widget, Gtk.Switch):
                setattr(self._cfg, key, widget.get_active())
                continue

            if isinstance(widget, Gtk.ComboBoxText):
                value = widget.get_active_text()
            else:
                value = widget.get_text()

            if key in _HOTKEY_FIELDS:
                value = _normalize_hotkey(value)
                widget.set_text(value)

            field_type = type(getattr(self._cfg, key))
            try:
                setattr(self._cfg, key, field_type(value))
            except (ValueError, TypeError):
                log.warning("Invalid value for %s: %s", key, value)

        self._cfg.save()
        self._on_save()
        self._info_label.set_text(_TXT_SAVE_MESSAGE)
        self._info_label.show()
