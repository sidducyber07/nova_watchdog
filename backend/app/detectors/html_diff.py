import hashlib


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def html_changed(previous_html: str | None, current_html: str) -> dict:
    """Return a dict describing whether HTML changed and hashes."""
    current_hash = compute_hash(current_html)
    previous_hash = compute_hash(previous_html) if previous_html else None
    changed = previous_hash != current_hash
    return {"changed": changed, "previous_hash": previous_hash, "current_hash": current_hash}
