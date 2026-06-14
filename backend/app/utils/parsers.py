"""File and URL parsing utilities."""

import re
import io
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader
import httpx
from bs4 import BeautifulSoup


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text_parts = []
    reader = PdfReader(file_path)
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n\n".join(text_parts)


def parse_txt(file_path: str) -> str:
    """Extract text from a plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_uploaded_file(file_path: str) -> str:
    """Parse an uploaded file based on its extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".txt":
        return parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


async def fetch_and_parse_url(url: str) -> dict:
    """Fetch a URL and extract its main content (async version)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else url
    # Get main content
    text = soup.get_text(separator="\n", strip=True)
    # Clean up whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    content = "\n".join(lines)

    # Truncate to reasonable size
    if len(content) > 50000:
        content = content[:50000] + "\n\n[Content truncated...]"

    return {
        "title": title[:500],
        "content": content,
        "url": url,
    }


def fetch_and_parse_url_sync(url: str) -> dict:
    """Fetch a URL and extract its main content (synchronous version)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = httpx.get(url, headers=headers, timeout=30.0, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else url
    # Get main content
    text = soup.get_text(separator="\n", strip=True)
    # Clean up whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    content = "\n".join(lines)

    # Truncate to reasonable size
    if len(content) > 50000:
        content = content[:50000] + "\n\n[Content truncated...]"

    return {
        "title": title[:500],
        "content": content,
        "url": url,
    }
