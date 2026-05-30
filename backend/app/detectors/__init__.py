"""Change detection engine modules"""

from .html_diff import html_changed
from .text_diff import text_changed
from .visual_diff import visual_diff

__all__ = ["html_changed", "text_changed", "visual_diff"]
