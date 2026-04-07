"""
Tests for the CORS proxy / image preload feature.

Covers:
  - Sidebar proxy input present and empty by default
  - state.corsProxy updated on input
  - preloadImagesForExport builds the correct fetch URL when a proxy is set
  - preloadImagesForExport swaps img.src to a data URL on CORS success
  - preloadImagesForExport leaves img.src unchanged on CORS failure
  - restoreImagesAfterExport restores original src values
  - Overlay text cycles through "Preparing images…" → "Generating export…"
  - Clearing the proxy field reverts state to empty string
"""
import pytest
from playwright.sync_api import Page

from conftest import upload_fixture


@pytest.fixture(autouse=True)
def loaded(page):
    upload_fixture(page, "minimal.json")
    page.locator("#btn-sel-visible").click()
    page.wait_for_timeout(100)


# ============================================================
# Sidebar proxy input
# ============================================================
class TestProxySidebarInput:

    def test_proxy_input_present(self, page: Page):
        assert page.locator("#input-cors-proxy").count() == 1

    def test_proxy_input_empty_by_default(self, page: Page):
        assert page.input_value("#input-cors-proxy") == ""

    def test_state_cors_proxy_empty_by_default(self, page: Page):
        assert page.evaluate("state.corsProxy") == ""

    def test_typing_proxy_url_updates_state(self, page: Page):
        page.fill("#input-cors-proxy", "https://corsproxy.io/?")
        page.locator("#input-cors-proxy").dispatch_event("input")
        assert page.evaluate("state.corsProxy") == "https://corsproxy.io/?"

    def test_clearing_proxy_input_resets_state(self, page: Page):
        page.fill("#input-cors-proxy", "https://corsproxy.io/?")
        page.locator("#input-cors-proxy").dispatch_event("input")
        page.fill("#input-cors-proxy", "")
        page.locator("#input-cors-proxy").dispatch_event("input")
        assert page.evaluate("state.corsProxy") == ""

    def test_proxy_input_trims_whitespace(self, page: Page):
        page.fill("#input-cors-proxy", "  https://corsproxy.io/?  ")
        page.locator("#input-cors-proxy").dispatch_event("input")
        assert page.evaluate("state.corsProxy") == "https://corsproxy.io/?"


# ============================================================
# Fetch URL construction
# ============================================================
class TestFetchURLConstruction:
    """
    Verifies that preloadImagesForExport builds the correct URL to fetch.
    We intercept window.fetch to record what URL it was called with.
    """

    def _patch_fetch(self, page: Page, mode: str = "fail") -> None:
        """
        Replace window.fetch with a spy that records called URLs.
        mode='fail'    → always rejects (simulates CORS failure)
        mode='succeed' → resolves with a tiny 1×1 transparent PNG data URL
        """
        if mode == "succeed":
            page.evaluate("""() => {
                window._fetchLog = [];
                window.fetch = async (url, opts) => {
                    window._fetchLog.push(url);
                    // Return a minimal valid image blob
                    const b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
                    const bytes = atob(b64);
                    const arr = new Uint8Array(bytes.length);
                    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
                    const blob = new Blob([arr], {type: 'image/png'});
                    return { ok: true, blob: () => Promise.resolve(blob) };
                };
            }""")
        else:
            page.evaluate("""() => {
                window._fetchLog = [];
                window.fetch = async (url, opts) => {
                    window._fetchLog.push(url);
                    throw new Error('CORS blocked');
                };
            }""")

    def _inject_img_src(self, page: Page, url: str = "https://example.com/image.jpg") -> None:
        """Ensure every selected card has an <img> with the given src."""
        page.evaluate(f"""() => {{
            document.querySelectorAll('#board .product-card.export-selected').forEach(card => {{
                const wrap = card.querySelector('.card-image-wrap');
                let img = wrap.querySelector('img');
                if (!img) {{ img = document.createElement('img'); wrap.appendChild(img); }}
                img.src = {repr(url)};
            }});
        }}""")

    def test_no_proxy_fetch_uses_raw_image_url(self, page: Page):
        test_url = "https://example.com/image.jpg"
        self._inject_img_src(page, test_url)
        self._patch_fetch(page)
        page.evaluate("""
            preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        page.wait_for_timeout(300)
        log = page.evaluate("window._fetchLog")
        assert test_url in log

    def test_proxy_prepended_to_image_url(self, page: Page):
        """When corsProxy is set, each fetch URL must start with the proxy prefix."""
        proxy = "https://myproxy.example.com/?"
        page.evaluate(f"state.corsProxy = {repr(proxy)}")
        self._patch_fetch(page)
        page.evaluate("""
            preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        page.wait_for_timeout(300)
        log = page.evaluate("window._fetchLog")
        # Every URL that was fetched must start with the proxy prefix
        # (some cards may have no img src and are skipped)
        fetched = [u for u in log if u]
        assert all(u.startswith(proxy) for u in fetched), \
            f"Expected all URLs to start with proxy. Got: {fetched}"

    def test_no_proxy_fetch_does_not_prepend_anything(self, page: Page):
        page.evaluate("state.corsProxy = ''")
        self._patch_fetch(page)
        page.evaluate("""
            preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        page.wait_for_timeout(300)
        log = page.evaluate("window._fetchLog")
        fetched = [u for u in log if u]
        assert not any(u.startswith("https://myproxy") for u in fetched)


# ============================================================
# Image src swapping on success / failure
# ============================================================
class TestImageSrcSwapping:

    def _patch_fetch_succeed(self, page: Page) -> None:
        page.evaluate("""() => {
            window.fetch = async (url) => {
                const b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
                const bytes = atob(b64);
                const arr = new Uint8Array(bytes.length);
                for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
                const blob = new Blob([arr], {type: 'image/png'});
                return { ok: true, blob: () => Promise.resolve(blob) };
            };
        }""")

    def _patch_fetch_fail(self, page: Page) -> None:
        page.evaluate("""() => {
            window.fetch = async () => { throw new Error('CORS blocked'); };
        }""")

    def test_successful_fetch_changes_img_src_to_data_url(self, page: Page):
        # Give cards a non-data src so the preloader has something to fetch
        page.evaluate("""() => {
            document.querySelectorAll('#board .product-card.export-selected img')
                .forEach(img => { img.src = 'https://example.com/image.jpg'; });
        }""")
        self._patch_fetch_succeed(page)
        page.evaluate("""
            preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        page.wait_for_timeout(500)
        srcs = page.evaluate("""() =>
            Array.from(document.querySelectorAll('#board .product-card.export-selected img'))
                 .map(img => img.src)
        """)
        assert all(s.startswith("data:") for s in srcs if s), \
            f"Expected data URLs after successful fetch, got: {srcs}"

    def test_successful_fetch_saves_original_src_in_dataset(self, page: Page):
        page.evaluate("""() => {
            document.querySelectorAll('#board .product-card.export-selected img')
                .forEach(img => { img.src = 'https://example.com/image.jpg'; });
        }""")
        self._patch_fetch_succeed(page)
        page.evaluate("""
            preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        page.wait_for_timeout(500)
        export_srcs = page.evaluate("""() =>
            Array.from(document.querySelectorAll('#board .product-card.export-selected img'))
                 .map(img => img.dataset.exportSrc || '')
        """)
        assert all(s == "https://example.com/image.jpg" for s in export_srcs if s)

    def test_failed_fetch_leaves_img_src_unchanged(self, page: Page):
        original = "https://example.com/no-cors-image.jpg"
        page.evaluate(f"""() => {{
            document.querySelectorAll('#board .product-card.export-selected img')
                .forEach(img => {{ img.src = {repr(original)}; }});
        }}""")
        self._patch_fetch_fail(page)
        page.evaluate("""
            preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        page.wait_for_timeout(300)
        srcs = page.evaluate("""() =>
            Array.from(document.querySelectorAll('#board .product-card.export-selected img'))
                 .map(img => img.src)
        """)
        assert all(s == original for s in srcs if s)

    def test_failed_fetch_does_not_set_export_src_dataset(self, page: Page):
        page.evaluate("""() => {
            document.querySelectorAll('#board .product-card.export-selected img')
                .forEach(img => { img.src = 'https://example.com/image.jpg'; });
        }""")
        self._patch_fetch_fail(page)
        page.evaluate("""
            preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        page.wait_for_timeout(300)
        export_srcs = page.evaluate("""() =>
            Array.from(document.querySelectorAll('#board .product-card.export-selected img'))
                 .map(img => img.dataset.exportSrc || '')
        """)
        assert all(s == "" for s in export_srcs)


# ============================================================
# restoreImagesAfterExport
# ============================================================
class TestRestoreImages:

    def test_restore_puts_original_src_back(self, page: Page):
        original = "https://example.com/original.jpg"
        page.evaluate(f"""() => {{
            document.querySelectorAll('#board .product-card.export-selected img')
                .forEach(img => {{
                    img.dataset.exportSrc = {repr(original)};
                    img.src = 'data:image/png;base64,abc';
                }});
        }}""")
        page.evaluate("""
            restoreImagesAfterExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        page.wait_for_timeout(100)
        srcs = page.evaluate("""() =>
            Array.from(document.querySelectorAll('#board .product-card.export-selected img'))
                 .map(img => img.src)
        """)
        assert all(s == original for s in srcs if s)

    def test_restore_removes_export_src_from_dataset(self, page: Page):
        page.evaluate("""() => {
            document.querySelectorAll('#board .product-card.export-selected img')
                .forEach(img => {
                    img.dataset.exportSrc = 'https://example.com/original.jpg';
                    img.src = 'data:image/png;base64,abc';
                });
        }""")
        page.evaluate("""
            restoreImagesAfterExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        export_srcs = page.evaluate("""() =>
            Array.from(document.querySelectorAll('#board .product-card.export-selected img'))
                 .map(img => img.dataset.exportSrc || '')
        """)
        assert all(s == "" for s in export_srcs)

    def test_restore_is_safe_when_no_export_src_set(self, page: Page):
        """Calling restore on cards that were never preloaded must not throw."""
        page.evaluate("""
            restoreImagesAfterExport(
                document.querySelectorAll('#board .product-card.export-selected')
            )
        """)
        # No exception = pass


# ============================================================
# Overlay text during preload
# ============================================================
class TestOverlayText:

    def _inject_img_src(self, page: Page, url: str = "https://example.com/image.jpg") -> None:
        page.evaluate(f"""() => {{
            document.querySelectorAll('#board .product-card.export-selected').forEach(card => {{
                const wrap = card.querySelector('.card-image-wrap');
                let img = wrap.querySelector('img');
                if (!img) {{ img = document.createElement('img'); wrap.appendChild(img); }}
                img.src = {repr(url)};
            }});
        }}""")

    def test_overlay_text_changes_to_preparing_during_preload(self, page: Page):
        """
        Inject a slow fetch so we can catch the overlay text mid-preload.
        Cards need a real img src — minimal.json has empty image_urls so
        preload would skip them and complete instantly without the injection.
        """
        self._inject_img_src(page)
        page.evaluate("""() => {
            window.fetch = () => new Promise(resolve =>
                setTimeout(() => resolve({ ok: false }), 2000)
            );
        }""")
        page.evaluate("""() => {
            document.getElementById('export-overlay').style.display = '';
            preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            );
        }""")
        page.wait_for_timeout(150)
        text = page.locator("#export-spinner-text").inner_text()
        assert "Preparing" in text

    def test_overlay_text_resets_to_generating_after_preload(self, page: Page):
        page.evaluate("""() => {
            window.fetch = async () => ({ ok: false });
        }""")
        page.evaluate("""async () => {
            await preloadImagesForExport(
                document.querySelectorAll('#board .product-card.export-selected')
            );
        }""")
        page.wait_for_timeout(300)
        text = page.locator("#export-spinner-text").inner_text()
        assert "Generating" in text
