import re


def normalize_text(s: str) -> str:
    # remove timestamps (simple heuristic), collapse whitespace
    s = re.sub(r"\d{1,2}:\d{2}(:\d{2})?", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def text_changed(previous_text: str | None, current_text: str, threshold: float = 0.01) -> dict:
    """Compare normalized text and return whether meaningful change occurred.

    threshold: fraction of change to consider significant (simple heuristic)
    """
    curr = normalize_text(current_text)
    prev = normalize_text(previous_text) if previous_text else ""
    if prev == curr:
        return {"changed": False, "ratio": 0.0}
    # simple diff ratio based on length and common prefix
    import difflib

    seq = difflib.SequenceMatcher(None, prev, curr)
    ratio = 1.0 - seq.ratio()
    changed = ratio >= threshold
    return {"changed": changed, "ratio": ratio}
