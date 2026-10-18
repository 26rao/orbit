"""HTML text extraction, cleaning, and content hashing."""

import hashlib
import re
from typing import Tuple
from bs4 import BeautifulSoup


def clean_html(html_content: str) -> Tuple[str, str]:
    """
    Extract readable text and title from HTML content.
    Removes boilerplate (scripts, styles, nav, footer, header, ads).
    Returns (title, cleaned_text).
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Remove non-content tags
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "svg"]):
        element.extract()

    # Extract paragraphs and headings
    text_blocks = []
    for tag in soup.find_all(["h1", "h2", "h3", "p"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 20:  # Skip tiny fragments / buttons
            text_blocks.append(text)

    cleaned_text = "\n\n".join(text_blocks)
    if not cleaned_text:
        # Fallback to entire stripped text
        cleaned_text = soup.get_text(separator=" ", strip=True)

    # Collapse excessive whitespace
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return title, cleaned_text


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash of normalized text for deduplication."""
    normalized = re.sub(r"\W+", "", text.lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
