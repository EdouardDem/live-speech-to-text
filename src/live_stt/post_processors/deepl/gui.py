"""GTK form widget for DeepL post-processor configuration."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..base import PostProcessorConfig
from .service import LANGUAGE_NAMES

# -- UI texts ----------------------------------------------------------------

_TXT_LBL_TARGET_LANGUAGE = "Target language"
_DEFAULT_LANGUAGE = "English"


class DeepLForm(Gtk.Grid):
    """Provider-specific configuration fields for a DeepL processor."""

    def __init__(self) -> None:
        super().__init__()
        self.set_column_spacing(12)
        self.set_row_spacing(8)

        self.attach(Gtk.Label(label=_TXT_LBL_TARGET_LANGUAGE, xalign=0), 0, 0, 1, 1)
        self._lang_combo = Gtk.ComboBoxText()
        self._lang_combo.set_hexpand(True)
        for name in LANGUAGE_NAMES:
            self._lang_combo.append_text(name)
        self.attach(self._lang_combo, 1, 0, 1, 1)

    def populate(self, cfg: PostProcessorConfig) -> None:
        lang = cfg.target_language.title()
        model = self._lang_combo.get_model()
        for i, row in enumerate(model):
            if row[0] == lang:
                self._lang_combo.set_active(i)
                return
        # Fallback: first entry
        self._lang_combo.set_active(0)

    def collect(self) -> dict:
        return {"target_language": self._lang_combo.get_active_text() or _DEFAULT_LANGUAGE}
