import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PostProcessorConfig:
    """Serialisable configuration for a single post-processor step."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Processor"
    icon: str = "system-run-symbolic"
    provider: str = "anthropic"  # "anthropic" | "deepl"
    enabled: bool = True
    hotkey: str = ""  # empty = no hotkey

    # Anthropic-specific
    prompt: str = ""
    model: str = ""
    max_tokens: int = 1024

    # DeepL-specific
    target_language: str = ""


def _provider_defaults(provider: str) -> dict[str, object]:
    """Return default field values for *provider*."""
    if provider == "anthropic":
        from .anthropic.config import DEFAULTS
        return DEFAULTS
    if provider == "deepl":
        from .deepl.config import DEFAULTS
        return DEFAULTS
    return {}


def make_config(provider: str, **overrides) -> PostProcessorConfig:
    """Create a PostProcessorConfig pre-filled with the provider's defaults."""
    defaults = _provider_defaults(provider)
    return PostProcessorConfig(provider=provider, **{**defaults, **overrides})


class PostProcessor(ABC):
    """Abstract base for a post-processing step."""

    def __init__(self, cfg: PostProcessorConfig) -> None:
        self.cfg = cfg

    @abstractmethod
    def run(self, text: str) -> str:
        """Transform *text* and return the result."""
