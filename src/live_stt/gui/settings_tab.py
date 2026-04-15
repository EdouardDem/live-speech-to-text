"""Settings tab — edit and persist configuration."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..services.config import Config
from ..services import logger
from ..services.hotkey import normalize_hotkey

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
_TXT_LBL_MAX_RECORDING = "Max recording duration (seconds)"
_TXT_LBL_ANTHROPIC_KEY = "Anthropic API key"
_TXT_LBL_OPENAI_KEY = "OpenAI API key"
_TXT_LBL_DEEPL_KEY = "DeepL API key"

_HOTKEY_FIELDS = {"hotkey"}

_HELP_TEXTS: dict[str, str] = {
    "max_recording_seconds": (
        "Adjust this based on your available RAM — longer recordings "
        "consume more memory during transcription."
    ),
}

_GENERAL_SPEC = [
    ("hotkey", _TXT_LBL_HOTKEY, "entry"),
    ("model_name", _TXT_LBL_MODEL, "entry"),
    ("device", _TXT_LBL_DEVICE, "combo", ["auto", "cpu", "cuda"]),
    ("paste_method", _TXT_LBL_PASTE_METHOD, "combo", ["auto", "xclip", "xdotool", "wayland"]),
    ("paste_shortcut", _TXT_LBL_PASTE_SHORTCUT, "combo", ["ctrl+shift+v", "ctrl+v"]),
    ("max_recording_seconds", _TXT_LBL_MAX_RECORDING, "entry"),
    ("log_to_console", _TXT_LBL_LOG_TO_CONSOLE, "toggle"),
]

_API_KEYS_SPEC = [
    ("anthropic_api_key", _TXT_LBL_ANTHROPIC_KEY, "password"),
    ("openai_api_key", _TXT_LBL_OPENAI_KEY, "password"),
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

    row = 0
    for item in specs:
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
        row += 1

        help_text = _HELP_TEXTS.get(key)
        if help_text:
            help_label = Gtk.Label(label=help_text, xalign=0)
            help_label.set_line_wrap(True)
            help_label.get_style_context().add_class("dim-label")
            grid.attach(help_label, 1, row, 1, 1)
            row += 1

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
                value = normalize_hotkey(value)
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
