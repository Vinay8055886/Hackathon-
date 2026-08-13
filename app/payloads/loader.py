"""Payload pack loader.

Packs are versioned YAML files. Bundled packs live in app/payloads/packs;
operators may drop additional packs into the repository-root payload_packs/
directory (loaded at runtime).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.core.config import PROJECT_ROOT
from app.payloads.schema import PayloadPackDef

BUNDLED_DIR = Path(__file__).resolve().parent / "packs"
RUNTIME_DIR = PROJECT_ROOT / "payload_packs"


class PayloadLoadError(Exception):
    pass


def _load_pack_file(path: Path) -> PayloadPackDef:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PayloadLoadError(f"Invalid YAML in {path}: {exc}") from exc
    try:
        return PayloadPackDef.model_validate(raw)
    except ValidationError as exc:
        raise PayloadLoadError(f"Invalid pack schema in {path}: {exc}") from exc


def load_pack(name: str, dirs: list[Path] | None = None) -> PayloadPackDef:
    search_dirs = dirs or [BUNDLED_DIR, RUNTIME_DIR]
    for directory in search_dirs:
        candidates = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))
        for path in candidates:
            if path.stem == name:
                return _load_pack_file(path)
    raise PayloadLoadError(f"Payload pack {name!r} not found in {[str(d) for d in search_dirs]}")


def load_all_packs(dirs: list[Path] | None = None) -> list[PayloadPackDef]:
    search_dirs = dirs or [BUNDLED_DIR, RUNTIME_DIR]
    packs: list[PayloadPackDef] = []
    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml")):
            packs.append(_load_pack_file(path))
    return packs
