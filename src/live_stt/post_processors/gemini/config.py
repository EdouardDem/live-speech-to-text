"""Provider metadata and default configuration for the Gemini post-processor."""

from ...services import icons


LABEL = "Gemini"
API_KEY_FIELD = "gemini_api_key"

DEFAULTS: dict[str, object] = {
    "icon": icons.get("text"),
    "prompt": (
        "Translate the following text to English. "
        "Return only the translation:\n\n{INPUT}"
    ),
    "model": "gemini-2.5-flash",
    "max_tokens": 1024,
}


def create_form():
    """Return a new GTK form widget for this provider."""
    from .gui import GeminiForm
    return GeminiForm()
