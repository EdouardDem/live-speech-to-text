"""Registry — manages the ordered list of post-processors."""

from collections.abc import Callable
from dataclasses import asdict

from pynput import keyboard

from .base import PostProcessor, PostProcessorConfig
from ..services import logger
from ..services.config import Config

log = logger.get(__name__)

# Fields present in PostProcessorConfig (used when deserialising from dicts).
_KNOWN_FIELDS = {f for f in PostProcessorConfig.__dataclass_fields__}


def _make_processor(cfg: PostProcessorConfig, app_config: Config) -> PostProcessor:
    """Instantiate the right PostProcessor subclass for *cfg*."""
    if cfg.provider == "anthropic":
        from .anthropic.service import AnthropicProcessor
        return AnthropicProcessor(cfg, api_key=app_config.anthropic_api_key)
    if cfg.provider == "deepl":
        from .deepl.service import DeepLProcessor
        return DeepLProcessor(cfg, api_key=app_config.deepl_api_key)
    raise ValueError(f"Unknown post-processor provider: {cfg.provider!r}")


class PostProcessorRegistry:
    """Owns the ordered list of PostProcessorConfig objects.

    Responsibilities
    ----------------
    - Deserialise configs from ``Config.post_processors`` on startup and on
      external config saves (e.g. API key change).
    - Provide add / remove / update / set_enabled mutations that persist to
      ``Config`` immediately.
    - Run the processing pipeline.
    - Manage per-processor pynput hotkey listeners that toggle enabled state.
    - Notify registered change callbacks (via ``GLib.idle_add``) whenever the
      processor list changes, so the GUI can rebuild itself.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._processors: list[PostProcessorConfig] = []
        self._hotkey_listeners: dict[str, keyboard.Listener] = {}
        self._change_callbacks: list[Callable[[list[PostProcessorConfig]], None]] = []
        self._saving = False

        config.subscribe(self._on_config_changed)
        self._reload()

    # -- Public query ---------------------------------------------------------

    def get_all(self) -> list[PostProcessorConfig]:
        """Return a snapshot of the current processor list."""
        return list(self._processors)

    # -- Public mutations -----------------------------------------------------

    def add(self, cfg: PostProcessorConfig) -> None:
        self._processors.append(cfg)
        self._setup_hotkey(cfg)
        self._save_and_notify()

    def remove(self, proc_id: str) -> None:
        self._teardown_hotkey(proc_id)
        self._processors = [p for p in self._processors if p.id != proc_id]
        self._save_and_notify()

    def update(self, cfg: PostProcessorConfig) -> None:
        idx = next(
            (i for i, p in enumerate(self._processors) if p.id == cfg.id), None
        )
        if idx is None:
            return
        self._teardown_hotkey(cfg.id)
        self._processors[idx] = cfg
        self._setup_hotkey(cfg)
        self._save_and_notify()

    def set_enabled(self, proc_id: str, enabled: bool) -> None:
        proc = next((p for p in self._processors if p.id == proc_id), None)
        if proc is None:
            return
        proc.enabled = enabled
        self._save()

    # -- Change callbacks -----------------------------------------------------

    def on_change(self, callback: Callable[[list[PostProcessorConfig]], None]) -> None:
        """Register a callback invoked (on the GTK thread) on any list change."""
        self._change_callbacks.append(callback)

    # -- Pipeline -------------------------------------------------------------

    def run_pipeline(
        self,
        text: str,
        on_step: Callable[[str, str, str], None],
    ) -> str:
        """Run all enabled processors in sequence.

        *on_step(result, name, icon)* is called after each successful step.
        Returns the final text (unchanged if no processors are enabled).
        """
        result = text
        for cfg in self._processors:
            if not cfg.enabled:
                continue
            processor = _make_processor(cfg, self._config)
            result = processor.run(result)
            on_step(result, cfg.name, cfg.icon)
        return result

    # -- Persistence ----------------------------------------------------------

    def _save(self) -> None:
        self._config.post_processors = [asdict(p) for p in self._processors]
        self._saving = True
        try:
            self._config.save()
        finally:
            self._saving = False

    def _save_and_notify(self) -> None:
        self._save()
        self._notify_change()

    # -- Internal state management --------------------------------------------

    def _reload(self) -> None:
        """Rebuild the processor list from the raw dicts in Config."""
        self._teardown_all_hotkeys()
        self._processors = []
        for d in self._config.post_processors:
            filtered = {k: v for k, v in d.items() if k in _KNOWN_FIELDS}
            cfg = PostProcessorConfig(**filtered)
            self._processors.append(cfg)
            self._setup_hotkey(cfg)

    def _on_config_changed(self) -> None:
        if self._saving:
            return
        # External save (e.g. API key change in Settings) — rebuild so
        # processors pick up the new key on next run.
        self._reload()
        self._notify_change()

    def _notify_change(self) -> None:
        from gi.repository import GLib

        snapshot = list(self._processors)
        GLib.idle_add(self._fire_callbacks, snapshot)

    def _fire_callbacks(self, snapshot: list[PostProcessorConfig]) -> bool:
        for cb in self._change_callbacks:
            cb(snapshot)
        return False  # GLib.SOURCE_REMOVE

    # -- Per-processor hotkeys ------------------------------------------------

    def _setup_hotkey(self, cfg: PostProcessorConfig) -> None:
        if not cfg.hotkey:
            return
        try:
            listener_cell: list[keyboard.Listener] = []
            hk = keyboard.HotKey(
                keyboard.HotKey.parse(cfg.hotkey),
                lambda pid=cfg.id: self._on_hotkey_fired(pid),
            )

            def for_canonical(func):
                return lambda key: func(listener_cell[0].canonical(key))

            listener = keyboard.Listener(
                on_press=for_canonical(hk.press),
                on_release=for_canonical(hk.release),
            )
            listener_cell.append(listener)
            listener.start()
            self._hotkey_listeners[cfg.id] = listener
            log.info("Post-processor hotkey registered: %s → %s", cfg.hotkey, cfg.name)
        except Exception:
            log.exception("Failed to register hotkey for processor %s", cfg.name)

    def _teardown_hotkey(self, proc_id: str) -> None:
        listener = self._hotkey_listeners.pop(proc_id, None)
        if listener is not None:
            listener.stop()

    def _teardown_all_hotkeys(self) -> None:
        for listener in self._hotkey_listeners.values():
            listener.stop()
        self._hotkey_listeners.clear()

    def _on_hotkey_fired(self, proc_id: str) -> None:
        """Toggle enabled state for *proc_id* (called from pynput thread via idle_add)."""
        proc = next((p for p in self._processors if p.id == proc_id), None)
        if proc is None:
            return
        proc.enabled = not proc.enabled
        self._save()
        self._notify_change()
