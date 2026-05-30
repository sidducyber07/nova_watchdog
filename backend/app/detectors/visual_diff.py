from PIL import Image, ImageChops
import numpy as np


def visual_diff(path_a: str, path_b: str, threshold: float = 0.02) -> dict:
    """Compute a simple visual diff between two images.

    Returns changed boolean and percent differing pixels.
    """
    a = Image.open(path_a).convert("RGB")
    b = Image.open(path_b).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    arr = np.asarray(diff)
    # consider pixel different if any channel > 0
    diff_pixels = np.count_nonzero(arr)
    total = arr.size
    ratio = diff_pixels / total
    changed = ratio >= threshold
    return {"changed": changed, "diff_ratio": float(ratio)}
