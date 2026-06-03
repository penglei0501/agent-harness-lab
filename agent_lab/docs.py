"""Discover course documents used by the Web learning site."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .paths import DOCS_DIR


TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
VERSION_RE = re.compile(r"^(s\d+[a-c]?)-")


@dataclass(frozen=True)
class DocItem:
    locale: str
    version: str
    title: str
    path: Path


def _doc_sort_key(path: Path) -> tuple[str, int, str]:
    locale = path.parent.name
    match = VERSION_RE.match(path.name)
    if match:
        number = int(match.group(1)[1:])
    else:
        number = 10**9
    return (locale, number, path.name)


def load_docs(docs_dir: Path = DOCS_DIR) -> list[DocItem]:
    """Return docs grouped by locale and ordered by session number."""
    if not docs_dir.exists():
        return []

    docs: list[DocItem] = []
    for path in sorted(docs_dir.glob("*/*.md"), key=_doc_sort_key):
        locale = path.parent.name
        if locale not in {"en", "zh"}:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        title_match = TITLE_RE.search(text)
        version_match = VERSION_RE.match(path.name)
        title = title_match.group(1) if title_match else path.stem
        version = version_match.group(1) if version_match else path.stem
        docs.append(DocItem(locale=locale, version=version, title=title, path=path))

    return docs
