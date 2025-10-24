import re
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b")

def redact(text: str) -> str:
    text = EMAIL.sub("[REDACTED_EMAIL]", text or "")
    text = PHONE.sub("[REDACTED_PHONE]", text or "")
    return text

def maybe(enabled: bool, text: str) -> str:
    return redact(text) if enabled else text