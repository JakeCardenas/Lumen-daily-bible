"""Filesystem locations used by the data build."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tool"
CACHE = TOOL / "cache"
DATA = TOOL / "data"
ASSETS = ROOT / "assets"
