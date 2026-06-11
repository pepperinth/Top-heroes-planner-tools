"""
persistence.py — Cookie-based browser persistence for Top Heroes Tools.

Each page creates its own manager via new_manager(page_key), then passes it to
save() / load(). Data never leaves the user's browser.
"""
from __future__ import annotations
import json
from datetime import datetime
import streamlit as st

try:
    import extra_streamlit_components as stx
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

_EXPIRY = datetime(2030, 1, 1)


def available() -> bool:
    return _AVAILABLE


def new_manager(page_key: str):
    """
    Instantiate a CookieManager for one page. Call once, at the very top of the
    page script (before any other widget), using a unique page_key per page.
    Returns None when extra-streamlit-components is not installed.
    """
    if not _AVAILABLE:
        return None
    return stx.CookieManager(key=f"th_{page_key}_mgr")


def save(mgr, cookie_key: str, data: dict) -> None:
    """Serialize data to JSON and write to a browser cookie."""
    if mgr is None:
        return
    try:
        mgr.set(cookie_key, json.dumps(data, ensure_ascii=False), expires_at=_EXPIRY)
    except Exception:
        pass


def load(mgr, cookie_key: str) -> dict | None:
    """Read and parse a JSON cookie. Returns None if missing, empty, or invalid."""
    if mgr is None:
        return None
    try:
        raw = mgr.get(cookie_key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None
