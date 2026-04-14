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

# -- UI texts ----------------------------------------------------------------

_TXT_WINDOW_TITLE = "Live Speech-to-Text"
_TXT_TAB_MAIN = "Main"
_TXT_TAB_POST_PROCESSING = "Post-processing"
_TXT_TAB_SETTINGS = "Settings"
_TXT_TAB_LOGS = "Logs"
_TXT_TAB_MODEL_LOGS = "Model Logs"
_TXT_STATUS_LOADING = "Loading model\u2026"


class LiveSTTWindow(Gtk.Window):
    def __init__(
        self,
        config: Config,
        registry: PostProcessorRegistry,
        *,
        on_settings_saved,
        on_start,
    ):
        super().__init__(title=_TXT_WINDOW_TITLE)
        self.set_default_size(520, 480)
        self.set_border_width(12)

        apply_css(self.get_screen())

        self.connect("delete-event", self._on_delete_event)

        notebook = Gtk.Notebook()
        self.add(notebook)

        self.main_tab = MainTab()
        self.main_tab.btn_start.connect("clicked", lambda _: on_start())
        notebook.append_page(self.main_tab, Gtk.Label(label=_TXT_TAB_MAIN))

        self.post_processing_tab = PostProcessingTab(registry, config)
        notebook.append_page(self.post_processing_tab, Gtk.Label(label=_TXT_TAB_POST_PROCESSING))

        self.settings_tab = SettingsTab(config, on_save=on_settings_saved)
        notebook.append_page(self.settings_tab, Gtk.Label(label=_TXT_TAB_SETTINGS))

        self.logs_tab = LogsTab()
        notebook.append_page(self.logs_tab, Gtk.Label(label=_TXT_TAB_LOGS))

        self.model_logs_tab = LogsTab()
        notebook.append_page(self.model_logs_tab, Gtk.Label(label=_TXT_TAB_MODEL_LOGS))

        self.main_tab.set_status(_TXT_STATUS_LOADING)
        self.main_tab.set_buttons_sensitive(False)

    def _on_delete_event(self, _widget, _event) -> bool:
        self.hide()
        return True
