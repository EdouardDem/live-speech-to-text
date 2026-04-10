"""Main GTK window — notebook with Main, Settings, and Log tabs."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..services.config import Config
from .log_tab import LogTab
from .main_tab import MainTab
from .settings_tab import SettingsTab
from .style import apply_css


class LiveSTTWindow(Gtk.Window):
    def __init__(self, config: Config, *, on_settings_saved, on_start, on_translate):
        super().__init__(title="Live Speech-to-Text")
        self.set_default_size(480, 420)
        self.set_border_width(12)

        apply_css(self.get_screen())

        # Hide instead of destroy on window close
        self.connect("delete-event", self._on_delete_event)

        notebook = Gtk.Notebook()
        self.add(notebook)

        self.main_tab = MainTab()
        self.main_tab.btn_start.connect("clicked", lambda _: on_start())
        self.main_tab.btn_translate.connect("clicked", lambda _: on_translate())
        notebook.append_page(self.main_tab, Gtk.Label(label="Main"))

        self.settings_tab = SettingsTab(config, on_save=on_settings_saved)
        notebook.append_page(self.settings_tab, Gtk.Label(label="Settings"))

        self.log_tab = LogTab()
        notebook.append_page(self.log_tab, Gtk.Label(label="Log"))

        # Initial state
        self.main_tab.set_status("Loading model…")
        self.main_tab.set_buttons_sensitive(False)

    def _on_delete_event(self, _widget, _event) -> bool:
        """Hide the window instead of destroying it."""
        self.hide()
        return True
