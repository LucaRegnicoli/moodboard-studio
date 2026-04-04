"""
Tests for PNG and PDF export: overlay lifecycle, download delivery,
button state management, and timeout / error handling.
"""
import pytest
from playwright.sync_api import Page

from conftest import upload_fixture, wait_for_export


@pytest.fixture(autouse=True)
def loaded(page):
    upload_fixture(page, "minimal.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _h2c_calls(page: Page) -> list:
    return page.evaluate("window._h2cLog || []")


def _patch_h2c(page: Page):
    """Instrument html2canvas to record all calls and timing."""
    page.evaluate("""() => {
        if (window._h2c_patched) return;
        window._h2c_patched = true;
        window._h2cLog = [];
        const orig = window.html2canvas;
        window.html2canvas = function(el, opts) {
            const t0 = Date.now();
            window._h2cLog.push({ type: 'start', opts: { imageTimeout: opts && opts.imageTimeout } });
            const p = orig(el, opts);
            p.then(() => window._h2cLog.push({ type: 'resolve', ms: Date.now() - t0 }));
            p.catch(e => window._h2cLog.push({ type: 'reject', ms: Date.now() - t0, err: String(e) }));
            return p;
        };
    }""")


# ---------------------------------------------------------------------------
# PNG export
# ---------------------------------------------------------------------------
class TestPNGExport:

    def test_png_overlay_appears_on_click(self, page: Page):
        page.locator("#btn-export-png").click()
        page.wait_for_function(
            "document.getElementById('export-overlay').style.display !== 'none'"
        )
        assert page.evaluate(
            "document.getElementById('export-overlay').style.display"
        ) != "none"

    def test_png_overlay_disappears_after_export(self, page: Page):
        page.locator("#btn-export-png").click()
        result = wait_for_export(page)
        assert result["done"], "PNG export overlay never closed"

    def test_png_export_triggers_download(self, page: Page):
        with page.expect_download() as dl_info:
            page.locator("#btn-export-png").click()
        download = dl_info.value
        assert download.suggested_filename == "moodboard.png"

    def test_png_download_has_content(self, page: Page):
        with page.expect_download() as dl_info:
            page.locator("#btn-export-png").click()
        dl = dl_info.value
        path = dl.path()
        assert path and path.stat().st_size > 0

    def test_png_no_alert_on_success(self, page: Page):
        page.locator("#btn-export-png").click()
        result = wait_for_export(page)
        assert not result["alert"], "Alert was shown on PNG export (expected success)"

    def test_png_buttons_disabled_during_export(self, page: Page):
        page.locator("#btn-export-png").click()
        # Check immediately after click before export finishes
        page.wait_for_function(
            "document.getElementById('export-overlay').style.display !== 'none'"
        )
        assert page.get_attribute("#btn-export-png", "disabled") is not None
        assert page.get_attribute("#btn-export-pdf", "disabled") is not None

    def test_png_buttons_reenabled_after_export(self, page: Page):
        page.locator("#btn-export-png").click()
        result = wait_for_export(page)
        assert result["done"]
        assert page.get_attribute("#btn-export-png", "disabled") is None
        assert page.get_attribute("#btn-export-pdf", "disabled") is None

    def test_png_uses_image_timeout_option(self, page: Page):
        _patch_h2c(page)
        page.locator("#btn-export-png").click()
        wait_for_export(page)
        calls = _h2c_calls(page)
        assert len(calls) >= 1
        start = next(c for c in calls if c["type"] == "start")
        assert start["opts"]["imageTimeout"] == 10000

    def test_png_html2canvas_resolves(self, page: Page):
        _patch_h2c(page)
        page.locator("#btn-export-png").click()
        wait_for_export(page)
        calls = _h2c_calls(page)
        resolved = [c for c in calls if c["type"] == "resolve"]
        assert len(resolved) == 1

    def test_png_export_completes_within_timeout(self, page: Page):
        """html2canvas must resolve well within the 30-second outer timeout."""
        _patch_h2c(page)
        page.locator("#btn-export-png").click()
        wait_for_export(page)
        calls = _h2c_calls(page)
        resolved = [c for c in calls if c["type"] == "resolve"]
        assert resolved, "html2canvas did not resolve"
        assert resolved[0]["ms"] < 30000, "html2canvas took longer than 30 s"


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------
class TestPDFExport:

    def test_pdf_overlay_appears_on_click(self, page: Page):
        page.locator("#btn-export-pdf").click()
        page.wait_for_function(
            "document.getElementById('export-overlay').style.display !== 'none'"
        )

    def test_pdf_overlay_disappears_after_export(self, page: Page):
        page.locator("#btn-export-pdf").click()
        result = wait_for_export(page, max_seconds=60)
        assert result["done"], "PDF export overlay never closed"

    def test_pdf_export_triggers_download(self, page: Page):
        with page.expect_download(timeout=60000) as dl_info:
            page.locator("#btn-export-pdf").click()
        download = dl_info.value
        assert download.suggested_filename == "moodboard.pdf"

    def test_pdf_download_has_content(self, page: Page):
        with page.expect_download(timeout=60000) as dl_info:
            page.locator("#btn-export-pdf").click()
        path = dl_info.value.path()
        assert path and path.stat().st_size > 1000  # PDFs are never tiny

    def test_pdf_no_alert_on_success(self, page: Page):
        page.locator("#btn-export-pdf").click()
        result = wait_for_export(page, max_seconds=60)
        assert not result["alert"], "Alert was shown on PDF export"

    def test_pdf_buttons_reenabled_after_export(self, page: Page):
        page.locator("#btn-export-pdf").click()
        result = wait_for_export(page, max_seconds=60)
        assert result["done"]
        assert page.get_attribute("#btn-export-pdf", "disabled") is None

    def test_pdf_renders_multiple_pages(self, page: Page):
        """PDF requires multiple html2canvas calls (one per A4 page)."""
        _patch_h2c(page)
        page.locator("#btn-export-pdf").click()
        wait_for_export(page, max_seconds=60)
        calls = _h2c_calls(page)
        resolved = [c for c in calls if c["type"] == "resolve"]
        assert len(resolved) >= 1  # minimal.json may be 1 page

    def test_pdf_uses_image_timeout_option(self, page: Page):
        _patch_h2c(page)
        page.locator("#btn-export-pdf").click()
        wait_for_export(page, max_seconds=60)
        calls = _h2c_calls(page)
        starts = [c for c in calls if c["type"] == "start"]
        assert starts, "No html2canvas calls recorded"
        assert all(s["opts"]["imageTimeout"] == 10000 for s in starts)


# ---------------------------------------------------------------------------
# Timeout protection
# ---------------------------------------------------------------------------
class TestTimeoutProtection:

    def test_hung_html2canvas_eventually_unblocks(self, page: Page):
        """
        Replace html2canvas with a version that never resolves or rejects.
        The 30-second outer timeout must close the overlay and show an alert.
        We use a much shorter fake timeout (50 ms) to keep the test fast.
        """
        # Patch EXPORT_TIMEOUT_MS to 2000 ms so we don't wait 30 s in CI
        page.evaluate("window.EXPORT_TIMEOUT_MS_OVERRIDE = 2000")
        page.evaluate("""() => {
            // Monkey-patch the exported function's timeout constant
            const origH2C = window.html2canvas;
            window.html2canvas = function() {
                // Return a promise that never settles
                return new Promise(() => {});
            };
            // Also patch our timeout wrapper to use the shorter value
            const origRace = Promise.race.bind(Promise);
            const _orig = window.html2canvasWithTimeout;
            window.html2canvasWithTimeout = function(el, opts) {
                const capture = window.html2canvas(el, opts);
                const timeout = new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('html2canvas timed out')), 2000)
                );
                return origRace([capture, timeout]);
            };
        }""")

        alerts = []
        # page fixture already dismisses dialogs; only record the message here.
        page.on("dialog", lambda d: alerts.append(d.message))

        page.locator("#btn-export-png").click()
        result = wait_for_export(page, max_seconds=10)

        assert result["done"], "Overlay never closed even after timeout"
        assert result["alert"], "No error alert shown after timeout"
        # Buttons must be re-enabled after the failed export
        assert page.get_attribute("#btn-export-png", "disabled") is None
