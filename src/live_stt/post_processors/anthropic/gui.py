"""GTK form widget for Anthropic post-processor configuration."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..base import PostProcessorConfig

# -- UI texts ----------------------------------------------------------------

_TXT_LBL_PROMPT = "Prompt"
_TXT_LBL_MODEL = "Model"
_TXT_LBL_MAX_TOKENS = "Max tokens"
_TXT_HINT_PROMPT = "Use {INPUT} where the transcribed text should be inserted."

_DEFAULT_MAX_TOKENS = 1024


class AnthropicForm(Gtk.Grid):
    """Provider-specific configuration fields for an Anthropic processor."""

    def __init__(self) -> None:
        super().__init__()
        self.set_column_spacing(12)
        self.set_row_spacing(8)

        # Prompt
        self.attach(Gtk.Label(label=_TXT_LBL_PROMPT, xalign=0), 0, 0, 1, 1)
        prompt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self._prompt = Gtk.TextView()
        self._prompt.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._prompt.set_hexpand(True)
        self._prompt.set_size_request(-1, 100)
        prompt_scroll = Gtk.ScrolledWindow()
        prompt_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        prompt_scroll.add(self._prompt)
        prompt_scroll.set_size_request(-1, 110)
        hint = Gtk.Label(label=_TXT_HINT_PROMPT)
        hint.set_xalign(0)
        hint.get_style_context().add_class("dim-label")
        prompt_box.pack_start(prompt_scroll, True, True, 0)
        prompt_box.pack_start(hint, False, False, 0)
        self.attach(prompt_box, 1, 0, 1, 1)

        # Model
        self.attach(Gtk.Label(label=_TXT_LBL_MODEL, xalign=0), 0, 1, 1, 1)
        self._model = Gtk.Entry()
        self._model.set_hexpand(True)
        self.attach(self._model, 1, 1, 1, 1)

        # Max tokens
        self.attach(Gtk.Label(label=_TXT_LBL_MAX_TOKENS, xalign=0), 0, 2, 1, 1)
        self._max_tokens = Gtk.Entry()
        self._max_tokens.set_hexpand(True)
        self.attach(self._max_tokens, 1, 2, 1, 1)

    def populate(self, cfg: PostProcessorConfig) -> None:
        self._prompt.get_buffer().set_text(cfg.prompt)
        self._model.set_text(cfg.model)
        self._max_tokens.set_text(str(cfg.max_tokens))

    def collect(self) -> dict:
        buf = self._prompt.get_buffer()
        prompt = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        try:
            max_tokens = int(self._max_tokens.get_text())
        except ValueError:
            max_tokens = _DEFAULT_MAX_TOKENS
        return {
            "prompt": prompt,
            "model": self._model.get_text().strip(),
            "max_tokens": max_tokens,
        }
