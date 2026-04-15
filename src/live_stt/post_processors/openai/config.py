"""Provider metadata and default configuration for the OpenAI post-processor."""

from ...services import icons


LABEL = "OpenAI"
API_KEY_FIELD = "openai_api_key"

DEFAULTS: dict[str, object] = {
    "icon": icons.get("text"),
    "prompt": (
        "Translate the following text to English. "
        "Return only the translation:\n\n{INPUT}"
    ),
    "model": "gpt-4o-mini",
    "max_tokens": 1024,
}


def create_form():
    """Return a new GTK form widget for this provider."""
    from .gui import OpenAIForm
    return OpenAIForm()
