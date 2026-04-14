"""Main GTK window — notebook with Main, Post-processing, Settings, and Log tabs."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..post_processors.registry import PostProcessorRegistry
from ..services.config import Config
from .logs_tab import LogsTab
from .main_tab import MainTab
from .post_processing_tab import PostProcessingTab
from .settings_tab import SettingsTab
from .style import apply_css


class LiveSTTWindow(Gtk.Window):
    def __init__(
        self,
        config: Config,
        registry: PostProcessorRegistry,
        *,
        on_settings_saved,
        on_start,
    ):
        super().__init__(title="Live Speech-to-Text")
        self.set_default_size(520, 480)
        self.set_border_width(12)

        apply_css(self.get_screen())

        self.connect("delete-event", self._on_delete_event)

        notebook = Gtk.Notebook()
        self.add(notebook)

        self.main_tab = MainTab()
        self.main_tab.btn_start.connect("clicked", lambda _: on_start())
        notebook.append_page(self.main_tab, Gtk.Label(label="Main"))

        self.post_processing_tab = PostProcessingTab(registry, config)
        notebook.append_page(self.post_processing_tab, Gtk.Label(label="Post-processing"))

        self.settings_tab = SettingsTab(config, on_save=on_settings_saved)
        notebook.append_page(self.settings_tab, Gtk.Label(label="Settings"))

        self.logs_tab = LogsTab()
        notebook.append_page(self.logs_tab, Gtk.Label(label="Logs"))

        self.model_logs_tab = LogsTab()
        notebook.append_page(self.model_logs_tab, Gtk.Label(label="Model Logs"))

        self.main_tab.set_status("Loading model…")
        self.main_tab.set_buttons_sensitive(False)

    def _on_delete_event(self, _widget, _event) -> bool:
        self.hide()
        return True
