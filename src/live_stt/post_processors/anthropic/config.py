"""Provider metadata and default configuration for the Anthropic post-processor."""

from ...services import icons


LABEL = "Anthropic"
API_KEY_FIELD = "anthropic_api_key"

DEFAULTS: dict[str, object] = {
    "icon": icons.get("text"),
    "prompt": (
        "Translate the following text to English. "
        "Return only the translation:\n\n{INPUT}"
    ),
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 1024,
}


def create_form():
    """Return a new GTK form widget for this provider."""
    from .gui import AnthropicForm
    return AnthropicForm()
