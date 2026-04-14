"""Provider metadata and default configuration for the DeepL post-processor."""

LABEL = "DeepL"
API_KEY_FIELD = "deepl_api_key"

DEFAULTS: dict[str, object] = {
    "icon": "preferences-desktop-locale-symbolic",
    "target_language": "English",
}


def create_form():
    """Return a new GTK form widget for this provider."""
    from .gui import DeepLForm
    return DeepLForm()
