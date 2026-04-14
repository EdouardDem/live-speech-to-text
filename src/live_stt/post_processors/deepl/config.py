"""Provider metadata and default configuration for the DeepL post-processor."""

from ...services import icons

LABEL = "DeepL"
API_KEY_FIELD = "deepl_api_key"

DEFAULTS: dict[str, object] = {
    "icon": icons.get("translate"),
    "target_language": "English",
}


def create_form():
    """Return a new GTK form widget for this provider."""
    from .gui import DeepLForm
    return DeepLForm()
