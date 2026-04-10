"""Encrypted key storage using Fernet symmetric encryption.

The encryption key is stored in a separate file from the config,
so reading config.yaml alone does not expose API keys.
"""

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from . import logger

log = logger.get(__name__)

_KEY_FILE = Path.home() / ".config" / "live-stt" / ".keyfile"


def _get_fernet() -> Fernet:
    """Return a Fernet instance, generating the key file if needed."""
    if not _KEY_FILE.exists():
        _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _KEY_FILE.write_bytes(Fernet.generate_key())
        _KEY_FILE.chmod(0o600)
    return Fernet(_KEY_FILE.read_bytes().strip())


def encrypt(value: str) -> str:
    """Encrypt a plaintext string and return a base64-encoded token."""
    if not value:
        return ""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a Fernet token back to plaintext. Returns empty string on failure."""
    if not token:
        return ""
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except (InvalidToken, Exception):
        log.warning("Failed to decrypt stored key — it may have been corrupted")
        return ""
