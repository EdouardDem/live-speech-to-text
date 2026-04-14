from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

from . import keystore

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "live-stt" / "config.yaml"

# Fields whose values are stored encrypted in the YAML file.
_ENCRYPTED_FIELDS = {"anthropic_api_key", "deepl_api_key"}


@dataclass
class Config:
    hotkey: str = "<ctrl>+<shift>+z"
    model_name: str = "nvidia/parakeet-tdt-0.6b-v3"
    sample_rate: int = 16000
    device: str = "auto"  # auto | cpu | cuda
    paste_method: str = "auto"  # auto | xclip | xdotool | wayland
    paste_shortcut: str = "ctrl+shift+v"
    log_to_console: bool = False
    anthropic_api_key: str = ""
    deepl_api_key: str = ""
    post_processors: list = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_listeners", [])
        object.__setattr__(self, "_last_saved", asdict(self))

    def subscribe(
        self,
        keys: Iterable[str],
        callback: Callable[[set[str]], None],
    ) -> None:
        """Register a callback invoked when any of *keys* changes on save.

        The callback receives the subset of *keys* whose values changed since
        the previous save. Listeners are skipped entirely when none of the
        keys they care about were modified.
        """
        self._listeners.append((frozenset(keys), callback))

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        p = Path(path) if path else DEFAULT_CONFIG_PATH
        if p.exists():
            data = yaml.safe_load(p.read_text()) or {}
            valid_keys = {f.name for f in fields(cls)}
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            # Decrypt encrypted fields
            for key in _ENCRYPTED_FIELDS:
                if key in filtered and filtered[key]:
                    filtered[key] = keystore.decrypt(filtered[key])
            return cls(**filtered)
        return cls()

    def save(self, path: str | Path | None = None) -> None:
        p = Path(path) if path else DEFAULT_CONFIG_PATH
        p.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)
        changes = self._extract_changes_and_update_last_saved(data)
        enc = self._encrypt_fields(data)
        
        p.write_text(yaml.dump(enc, default_flow_style=False, sort_keys=False))
        
        self._fire_callbacks(changes)

    def _encrypt_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        output = dict(data)
        for key in _ENCRYPTED_FIELDS:
            if output.get(key):
                output[key] = keystore.encrypt(output[key])
        return output

    def _extract_changes_and_update_last_saved(self, data: dict[str, Any]) -> set[str]:
        changes = {k for k, v in data.items() if self._last_saved.get(k) != v}
        self._last_saved = data
        return changes

    def _fire_callbacks(self, changes: set[str]) -> bool:
        for keys, callback in self._listeners:
            relevant = changes & keys
            if relevant:
                callback(relevant)
