from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import frontmatter
import re


LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def read_note_frontmatter(path: Path) -> Tuple[str, Dict[str, Any]]:
    post = frontmatter.load(path)
    content = post.content or ""
    metadata: Dict[str, Any] = dict(post.metadata or {})
    return content, metadata


def write_note_frontmatter(path: Path, content: str, metadata: Dict[str, Any]) -> None:
    post = frontmatter.Post(content, **metadata)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Handle frontmatter serialization more carefully
    try:
        output = frontmatter.dumps(post)
        # Ensure output is string, not bytes
        if isinstance(output, bytes):
            output = output.decode("utf-8")
        path.write_text(output, encoding="utf-8")
    except Exception as e:
        # Fallback: manually create frontmatter
        yaml_header = ""
        if metadata:
            import yaml
            yaml_header = "---\n" + yaml.dump(metadata, default_flow_style=False) + "---\n"
        final_content = yaml_header + content
        path.write_text(final_content, encoding="utf-8")


def extract_outlinks(markdown_text: str) -> List[str]:
    return [m.group(1).strip() for m in LINK_PATTERN.finditer(markdown_text)]


def replace_section(markdown_text: str, section: str, new_body: str) -> str:
    """
    Replace the body of a markdown section (by its heading text) with new_body.
    If the section doesn't exist, append it at the end.
    """
    lines = markdown_text.splitlines()
    header_regex = re.compile(rf"^\s*#+\s+{re.escape(section)}\s*$", re.IGNORECASE)

    start_idx = None
    for i, line in enumerate(lines):
        if header_regex.match(line):
            start_idx = i
            break

    if start_idx is None:
        # Append new section
        out = markdown_text.rstrip() + "\n\n" + f"## {section}\n" + new_body.rstrip() + "\n"
        return out

    # Find end of section (next header or end of file)
    end_idx = len(lines)
    header_start = re.compile(r"^\s*#+\s+.+$")
    for j in range(start_idx + 1, len(lines)):
        if header_start.match(lines[j]):
            end_idx = j
            break

    # Build new content
    new_lines = []
    new_lines.extend(lines[: start_idx + 1])
    new_body_lines = new_body.splitlines()
    new_lines.extend(new_body_lines)
    if end_idx < len(lines):
        new_lines.extend(lines[end_idx:])
    else:
        new_lines.append("")
    return "\n".join(new_lines)


