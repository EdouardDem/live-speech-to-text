"""Centralised icon catalogue.

Maps short slugs to GTK symbolic icon names. Call :func:`get` with a slug
to retrieve the icon name to pass to ``Gtk.Image.new_from_icon_name`` or
similar APIs. Use :func:`list_slugs` to enumerate every available slug
(e.g. for UI pickers).
"""

_ICONS: dict[str, str] = {
    # Audio & voice
    "microphone": "audio-input-microphone-symbolic",
    "transcription": "audio-input-microphone-symbolic",
    "speaker": "audio-speakers-symbolic",
    "volume": "audio-volume-high-symbolic",
    "mute": "audio-volume-muted-symbolic",
    "headphones": "audio-headphones-symbolic",

    # Text & translation
    "text": "accessories-text-editor-symbolic",
    "translate": "preferences-desktop-locale-symbolic",
    "dictionary": "accessories-dictionary-symbolic",
    "spellcheck": "tools-check-spelling-symbolic",

    # Actions (edit)
    "edit": "document-edit-symbolic",
    "copy": "edit-copy-symbolic",
    "paste": "edit-paste-symbolic",
    "cut": "edit-cut-symbolic",
    "delete": "edit-delete-symbolic",
    "undo": "edit-undo-symbolic",
    "redo": "edit-redo-symbolic",
    "find": "edit-find-symbolic",
    "clear": "edit-clear-symbolic",
    "select-all": "edit-select-all-symbolic",

    # Actions (files & documents)
    "new": "document-new-symbolic",
    "open": "document-open-symbolic",
    "save": "document-save-symbolic",
    "file": "text-x-generic-symbolic",
    "folder": "folder-symbolic",
    "download": "document-save-symbolic",
    "send": "document-send-symbolic",

    # Actions (general)
    "add": "list-add-symbolic",
    "remove": "list-remove-symbolic",
    "run": "system-run-symbolic",
    "refresh": "view-refresh-symbolic",
    "settings": "preferences-system-symbolic",
    "search": "system-search-symbolic",
    "close": "window-close-symbolic",
    "menu": "open-menu-symbolic",

    # Media controls
    "play": "media-playback-start-symbolic",
    "pause": "media-playback-pause-symbolic",
    "stop": "media-playback-stop-symbolic",
    "record": "media-record-symbolic",

    # Status & feedback
    "info": "dialog-information-symbolic",
    "warning": "dialog-warning-symbolic",
    "error": "dialog-error-symbolic",
    "question": "dialog-question-symbolic",
    "check": "object-select-symbolic",

    # Navigation
    "back": "go-previous-symbolic",
    "forward": "go-next-symbolic",
    "up": "go-up-symbolic",
    "down": "go-down-symbolic",

    # Misc
    "lock": "changes-prevent-symbolic",
    "unlock": "changes-allow-symbolic",
    "star": "starred-symbolic",
    "user": "avatar-default-symbolic",
    "bot": "face-smile-symbolic",
    "cloud": "weather-overcast-symbolic",
}

_FALLBACK_ICON = "system-run-symbolic"


def get(slug: str) -> str:
    """Return the GTK icon name for *slug*, or a safe fallback."""
    return _ICONS.get(slug, _FALLBACK_ICON)


def list_slugs() -> list[str]:
    """Return every available slug, sorted alphabetically."""
    return sorted(_ICONS)


def has(slug: str) -> bool:
    """Return whether *slug* is a known icon."""
    return slug in _ICONS
