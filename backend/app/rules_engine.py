import re
from typing import List, Tuple
from .models import AIRule

PRICE_KEYWORDS = ["price", "pricing", "cost", "sale", "discount", "$", "€", "£", "usd", "eur", "£"]
SECURITY_KEYWORDS = ["security", "vulnerability", "breach", "exploit", "attack", "leak", "malware", "ransomware"]
FOOTER_PATTERNS = [r"<footer", r"class=[\"'][^\"']*footer", r"id=[\"'][^\"']*footer"]
COOKIE_PATTERNS = [r"cookie", r"cookie banner", r"cookie-consent", r"gdpr", r"consent"]


def _contains_any(text: str, keywords: List[str]) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(keyword in lower for keyword in keywords)


def _matches_regex(text: str, patterns: List[str]) -> bool:
    if not text:
        return False
    for pattern in patterns:
        if re.search(pattern, text, re.I):
            return True
    return False


def _parse_importance_threshold(rule_text: str) -> float | None:
    m = re.search(r"importance\s*>\s*(\d+)%?", rule_text)
    if m:
        val = int(m.group(1))
        if val > 1:
            return min(1.0, val / 100.0)
        return float(val)
    return None


def _parse_selector_value(rule_text: str) -> str | None:
    m = re.search(r"selector\s*[:=]\s*([\S]+)", rule_text)
    return m.group(1).strip() if m else None


def _matches_rule(rule_text: str, monitor_selector: str | None, raw_html: str, cleaned_html: str, text: str, ai_score: float, diff_summary: dict) -> bool:
    lower = rule_text.lower()
    if "price" in lower or "pricing" in lower:
        return _contains_any(raw_html + cleaned_html + text, PRICE_KEYWORDS)
    if "security" in lower:
        return _contains_any(raw_html + cleaned_html + text, SECURITY_KEYWORDS)
    if "footer" in lower:
        return _matches_regex(raw_html, FOOTER_PATTERNS)
    if "cookie" in lower:
        return _matches_regex(raw_html, COOKIE_PATTERNS)
    threshold = _parse_importance_threshold(lower)
    if threshold is not None:
        return ai_score >= threshold
    selector_value = _parse_selector_value(lower)
    if selector_value and monitor_selector:
        return selector_value in monitor_selector
    return any(keyword in lower for keyword in ["price", "security", "footer", "cookie", "importance", "selector"])


def evaluate_rules(rules: List[AIRule], monitor_selector: str | None, raw_html: str, cleaned_html: str, text: str, ai_score: float, diff_summary: dict) -> Tuple[bool, str]:
    if not rules:
        return True, "No active rules"

    skip_reasons = []
    allow_reasons = []
    positive_rule_found = False

    for rule in rules:
        rule_text = rule.rule_text or ""
        matches = _matches_rule(rule_text, monitor_selector, raw_html, cleaned_html, text, ai_score, diff_summary)
        if "ignore" in rule_text.lower():
            if matches:
                skip_reasons.append(f"Ignored by rule '{rule.name}'")
        else:
            if any(tag in rule_text.lower() for tag in ["alert only", "notify only", "alert on", "only if"]):
                positive_rule_found = True
                if matches:
                    allow_reasons.append(f"Allowed by rule '{rule.name}'")
            else:
                positive_rule_found = True
                if matches:
                    allow_reasons.append(f"Matched rule '{rule.name}'")

    if skip_reasons:
        return False, "; ".join(skip_reasons)
    if positive_rule_found and not allow_reasons:
        return False, "No rule conditions matched"
    return True, "; ".join(allow_reasons) if allow_reasons else "Allowed"
