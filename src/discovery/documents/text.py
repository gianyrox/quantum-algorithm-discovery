from __future__ import annotations

import re

from discovery.documents.schema import ParsedDocument


def document_text(document: ParsedDocument) -> str:
    return "\n\n".join(section.text for section in document.sections if section.text.strip())


def token_set(text: str) -> set[str]:
    return {token.casefold() for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)}


def sentence_windows(text: str, *, size: int = 3) -> list[str]:
    sentences = [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+(?=[A-Z])", re.sub(r"\s+", " ", text))
        if item.strip()
    ]
    if size <= 1:
        return sentences
    return [" ".join(sentences[index : index + size]) for index in range(len(sentences))]
