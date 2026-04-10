"""Settings tab — edit and persist configuration."""

import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..services.config import Config

log = logging.getLogger(__name__)

_SETTINGS_SPEC = [
    ("hotkey", "Hotkey", "entry"),
    ("model_name", "Model", "entry"),
    ("device", "Device", "combo", ["auto", "cpu", "cuda"]),
    ("paste_method", "Paste method", "combo", ["auto", "xclip", "xdotool", "wayland"]),
    ("paste_shortcut", "Paste shortcut", "entry"),
    ("translate_hotkey", "Translate hotkey", "entry"),
    ("translate_language", "Translate language", "entry"),
    ("translate_provider", "Translate provider", "combo", ["anthropic", "deepl"]),
    ("translate_model", "Translate model", "entry"),
    ("translate_max_tokens", "Max tokens", "entry"),
]


class SettingsTab(Gtk.ScrolledWindow):
    def __init__(self, config: Config, on_save):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._cfg = config
        self._on_save = on_save
        self._entries: dict[str, Gtk.Entry | Gtk.ComboBoxText] = {}

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(8)
        grid.set_margin_top(16)
        grid.set_margin_bottom(16)
        grid.set_margin_start(16)
        grid.set_margin_end(16)

        for row, item in enumerate(_SETTINGS_SPEC):
            key, label_text, kind = item[0], item[1], item[2]
            label = Gtk.Label(label=label_text, xalign=0)
            grid.attach(label, 0, row, 1, 1)

            current_value = str(getattr(self._cfg, key))

            if kind == "combo":
                combo = Gtk.ComboBoxText()
                for opt in item[3]:
                    combo.append_text(opt)
                combo.set_active(
                    item[3].index(current_value) if current_value in item[3] else 0
                )
                combo.set_hexpand(True)
                grid.attach(combo, 1, row, 1, 1)
                self._entries[key] = combo
            else:
                entry = Gtk.Entry()
                entry.set_text(current_value)
                entry.set_hexpand(True)
                grid.attach(entry, 1, row, 1, 1)
                self._entries[key] = entry

        save_btn = Gtk.Button(label="Save settings")
        save_btn.connect("clicked", self._on_save_clicked)
        grid.attach(save_btn, 0, len(_SETTINGS_SPEC), 2, 1)

        self.add(grid)

    def _on_save_clicked(self, _btn: Gtk.Button) -> None:
        for key, widget in self._entries.items():
            if isinstance(widget, Gtk.ComboBoxText):
                value = widget.get_active_text()
            else:
                value = widget.get_text()

            field_type = type(getattr(self._cfg, key))
            try:
                setattr(self._cfg, key, field_type(value))
            except (ValueError, TypeError):
                log.warning("Invalid value for %s: %s", key, value)

        self._cfg.save()
        self._on_save()
