"""
Shared fixtures for Moodboard Studio end-to-end tests.

Architecture
------------
- A single ThreadingHTTPServer serves the project root for the entire session,
  eliminating per-test startup cost.
- The Playwright browser is also session-scoped; only the page is
  function-scoped so every test starts from a clean state.
- All fixtures are synchronous (Playwright sync API) to keep tests simple
  and avoid asyncio mode configuration headaches.
"""
import os
import socket
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, Page

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------
def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _QuietHandler(SimpleHTTPRequestHandler):
    """Serve the project root, suppress access logs."""
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def app_url() -> str:
    """Start a local HTTP server serving the project root and return its base URL."""
    port = _find_free_port()
    handler = lambda *a, **kw: _QuietHandler(*a, directory=str(PROJECT_ROOT), **kw)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


# ---------------------------------------------------------------------------
# Playwright browser (session-scoped — one browser process for all tests)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        yield browser
        browser.close()


# ---------------------------------------------------------------------------
# Page (function-scoped — clean state per test)
# ---------------------------------------------------------------------------
@pytest.fixture
def page(browser_instance, app_url) -> Page:
    """Fresh page navigated to the app, ready for interaction."""
    ctx = browser_instance.new_context(accept_downloads=True)
    pg = ctx.new_page()

    # Dismiss any unexpected alerts automatically
    pg.on("dialog", lambda d: d.dismiss())

    pg.goto(f"{app_url}/index.html")
    pg.wait_for_load_state("domcontentloaded")

    yield pg

    ctx.close()


# ---------------------------------------------------------------------------
# Convenience helpers available to all tests
# ---------------------------------------------------------------------------
def upload_fixture(page: Page, name: str) -> None:
    """Upload a fixture JSON file and wait for the board to populate.

    Uses a two-phase wait to avoid the race where the previous upload's
    terminal status (e.g. '3 products loaded') is already present when the
    new FileReader starts, causing a single-condition wait to exit early.
    """
    import json as _json

    path = str(FIXTURES_DIR / name)
    old_status = page.evaluate("document.getElementById('upload-status').textContent")

    page.locator("#json-input").set_input_files(path)

    # Phase 1 – wait for status to leave the previous value (upload started)
    page.wait_for_function(
        f"document.getElementById('upload-status').textContent !== {_json.dumps(old_status)}"
    )
    # Phase 2 – wait for a terminal state (not "Reading…")
    page.wait_for_function(
        "document.getElementById('upload-status').textContent !== 'Reading\u2026'"
    )


def wait_for_export(page: Page, max_seconds: int = 45) -> dict:
    """
    Click has already happened. Wait for the export overlay to appear then
    disappear.  Returns ``{'done': bool, 'elapsed_s': float, 'alert': bool}``.

    Note: the page fixture already registers a dismiss handler for all dialogs,
    so we only record the message here without calling dismiss() again.
    """
    import time as _time

    alert_seen = []
    # Only record the message; the page fixture's on("dialog") handler dismisses.
    page.once("dialog", lambda d: alert_seen.append(d.message))

    try:
        # Wait for overlay to appear (display flips from 'none' to '')
        page.wait_for_function(
            "document.getElementById('export-overlay').style.display !== 'none'",
            timeout=5000,
        )
    except Exception:
        return {"done": False, "elapsed_s": 0, "alert": bool(alert_seen)}

    t0 = _time.time()
    try:
        # Wait for overlay to disappear again
        page.wait_for_function(
            "document.getElementById('export-overlay').style.display === 'none'",
            timeout=max_seconds * 1000,
        )
        return {"done": True, "elapsed_s": _time.time() - t0, "alert": bool(alert_seen)}
    except Exception:
        return {"done": False, "elapsed_s": max_seconds, "alert": bool(alert_seen)}
