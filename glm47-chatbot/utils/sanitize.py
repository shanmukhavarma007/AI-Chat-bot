import html
import re


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return text.strip()


def sanitize_message(text: str, max_length: int = 4000) -> str:
    text = strip_html(text)
    if len(text) > max_length:
        text = text[:max_length]
    if not text:
        raise ValueError("Message cannot be empty")
    return text


def sanitize_system_prompt(text: str, max_length: int = 500) -> str:
    return sanitize_message(text, max_length)