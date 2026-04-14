from collections.abc import Callable
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

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

    def subscribe(self, callback: Callable[[], None]) -> None:
        """Register a callback to be invoked whenever the config is saved."""
        self._listeners.append(callback)

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
        # Encrypt sensitive fields before writing
        for key in _ENCRYPTED_FIELDS:
            if data.get(key):
                data[key] = keystore.encrypt(data[key])
        p.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
        for listener in self._listeners:
            listener()
