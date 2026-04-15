"""Registry — manages the ordered list of post-processors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from types import ModuleType

from pynput import keyboard

from .base import PostProcessor, PostProcessorConfig
from ..services import logger
from ..services.config import Config
from ..services.hotkey import start_hotkey_listener

log = logger.get(__name__)

# Fields present in PostProcessorConfig (used when deserialising from dicts).
_KNOWN_FIELDS = {f for f in PostProcessorConfig.__dataclass_fields__}

# ---------------------------------------------------------------------------
# Provider catalogue — each entry is the provider's config module.
# ---------------------------------------------------------------------------

_PROVIDER_IDS: list[str] = ["anthropic", "openai", "deepl"]


def _load_provider_config(provider: str) -> ModuleType:
    """Lazily import and return the config module for *provider*."""
    if provider == "anthropic":
        from .anthropic import config
        return config
    if provider == "openai":
        from .openai import config
        return config
    if provider == "deepl":
        from .deepl import config
        return config
    raise ValueError(f"Unknown post-processor provider: {provider!r}")


def get_provider_ids() -> list[str]:
    """Return the ordered list of available provider identifiers."""
    return list(_PROVIDER_IDS)


def get_provider_label(provider: str) -> str:
    """Human-readable label for *provider*."""
    return _load_provider_config(provider).LABEL


def get_provider_api_key_field(provider: str) -> str:
    """Config attribute name that holds the API key for *provider*."""
    return _load_provider_config(provider).API_KEY_FIELD


def create_provider_form(provider: str):
    """Return a new GTK form widget for *provider*."""
    return _load_provider_config(provider).create_form()


def make_config(provider: str, **overrides) -> PostProcessorConfig:
    """Create a PostProcessorConfig pre-filled with the provider's defaults."""
    defaults = _load_provider_config(provider).DEFAULTS
    return PostProcessorConfig(provider=provider, **{**defaults, **overrides})


def _make_processor(cfg: PostProcessorConfig, app_config: Config) -> PostProcessor:
    """Instantiate the right PostProcessor subclass for *cfg*."""
    if cfg.provider == "anthropic":
        from .anthropic.service import AnthropicProcessor
        return AnthropicProcessor(cfg, api_key=app_config.anthropic_api_key)
    if cfg.provider == "openai":
        from .openai.service import OpenAIProcessor
        return OpenAIProcessor(cfg, api_key=app_config.openai_api_key)
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

    The registry does not maintain its own change-notification system: every
    mutation persists through ``Config.save``, and interested parties simply
    subscribe to the ``post_processors`` key on the config.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._processors: list[PostProcessorConfig] = []
        self._hotkey_listeners: dict[str, keyboard.Listener] = {}
        self._saving = False

        config.subscribe({"post_processors"}, self._on_config_changed)
        self._reload()

    # -- Public query ---------------------------------------------------------

    def get_all(self) -> list[PostProcessorConfig]:
        """Return a snapshot of the current processor list."""
        return list(self._processors)

    # -- Public mutations -----------------------------------------------------

    def add(self, cfg: PostProcessorConfig) -> None:
        self._processors.append(cfg)
        self._setup_hotkey(cfg)
        self._save()

    def remove(self, proc_id: str) -> None:
        self._teardown_hotkey(proc_id)
        self._processors = [p for p in self._processors if p.id != proc_id]
        self._save()

    def update(self, cfg: PostProcessorConfig) -> None:
        idx = next(
            (i for i, p in enumerate(self._processors) if p.id == cfg.id), None
        )
        if idx is None:
            return
        self._teardown_hotkey(cfg.id)
        self._processors[idx] = cfg
        self._setup_hotkey(cfg)
        self._save()

    def move(self, proc_id: str, offset: int) -> None:
        """Shift *proc_id* by *offset* positions in the list (+1 = down)."""
        idx = next(
            (i for i, p in enumerate(self._processors) if p.id == proc_id), None
        )
        if idx is None:
            return
        new_idx = idx + offset
        if new_idx < 0 or new_idx >= len(self._processors):
            return
        proc = self._processors.pop(idx)
        self._processors.insert(new_idx, proc)
        log.info("Post-processor %s moved to position %d", proc.name, new_idx)
        self._save()

    def set_enabled(self, proc_id: str, enabled: bool) -> None:
        proc = next((p for p in self._processors if p.id == proc_id), None)
        if proc is None:
            return
        if proc.enabled == enabled:
            return
        proc.enabled = enabled
        log.info(
            "Post-processor %s: %s", proc.name, "enabled" if enabled else "disabled"
        )
        self._save()

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

    def _on_config_changed(self, _changed: set[str]) -> None:
        if self._saving:
            return
        self._reload()

    # -- Per-processor hotkeys ------------------------------------------------

    def _setup_hotkey(self, cfg: PostProcessorConfig) -> None:
        if not cfg.hotkey:
            return
        try:
            listener = start_hotkey_listener(
                cfg.hotkey, lambda pid=cfg.id: self._on_hotkey_fired(pid)
            )
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
        self.set_enabled(proc_id, not proc.enabled)
