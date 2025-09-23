from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import re


TITLE_SANITIZE_PATTERN = re.compile(r"[\\/:*?\"<>|]")


def title_to_filename(title: str) -> str:
    sanitized = TITLE_SANITIZE_PATTERN.sub("_", title.strip())
    if not sanitized:
        sanitized = "untitled"
    return f"{sanitized}.md"


def note_path_for_title(vault_path: Path, title: str, folder: Optional[str] = None) -> Path:
    base = vault_path
    if folder:
        base = base / folder
    return base / title_to_filename(title)


def list_note_paths(vault_path: Path, folder: Optional[str] = None) -> List[Path]:
    base = vault_path / folder if folder else vault_path
    if not base.exists():
        return []
    return [p for p in base.rglob("*.md") if p.is_file()]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


