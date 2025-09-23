from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import os
import yaml


DEFAULT_CONFIG_FILENAME_CANDIDATES = (
    "obsidian_mcp_config.yaml",
    "config.yaml",
)


@dataclass
class VaultConfig:
    path: str
    templates_folder: Optional[str] = None
    daily_notes_folder: Optional[str] = None
    attachments_folder: Optional[str] = None


@dataclass
class AppConfig:
    vault: VaultConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML structure in {path}")
    return data


def _dict_get(d: dict[str, Any], key: str, default: Any = None) -> Any:
    value = d.get(key, default)
    return value


def find_default_config(start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Locate a default configuration file by checking common filenames
    in the provided directory (or current working directory).
    """
    base = start_dir or Path.cwd()
    for name in DEFAULT_CONFIG_FILENAME_CANDIDATES:
        candidate = base / name
        if candidate.exists():
            return candidate
    return None


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from YAML. If config_path is None, try environment
    variable OBSIDIAN_MCP_CONFIG, then common filenames in the CWD.
    """
    env_cfg = os.getenv("OBSIDIAN_MCP_CONFIG")
    if config_path is None and env_cfg:
        config_path = Path(env_cfg)

    if config_path is None:
        config_path = find_default_config()

    if config_path is None:
        # Minimal fallback configuration; vault path will be resolved later
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", str((Path.cwd() / "vault").resolve()))
        return AppConfig(vault=VaultConfig(path=vault_path))

    data = _read_yaml(config_path)
    vault_data = _dict_get(data, "vault", {})
    vault_path = str(_dict_get(vault_data, "path", os.getenv("OBSIDIAN_VAULT_PATH", str((Path.cwd() / "vault").resolve()))))
    templates_folder = _dict_get(vault_data, "templates_folder", None)
    daily_notes_folder = _dict_get(vault_data, "daily_notes_folder", None)
    attachments_folder = _dict_get(vault_data, "attachments_folder", None)

    return AppConfig(
        vault=VaultConfig(
            path=vault_path,
            templates_folder=templates_folder,
            daily_notes_folder=daily_notes_folder,
            attachments_folder=attachments_folder,
        )
    )


def ensure_vault_path(config: AppConfig) -> Path:
    """
    Resolve and ensure the vault directory exists. Returns the absolute Path.
    """
    vault_path = Path(config.vault.path).expanduser()
    if not vault_path.is_absolute():
        vault_path = (Path.cwd() / vault_path).resolve()
    vault_path.mkdir(parents=True, exist_ok=True)
    return vault_path


