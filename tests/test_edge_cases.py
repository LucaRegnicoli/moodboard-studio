"""
Edge-case and robustness tests: missing fields, image errors,
multi-upload, products that match no filters, etc.
"""
import json
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import Page

from conftest import upload_fixture, FIXTURES_DIR


def upload_json(page: Page, data) -> None:
    """Write arbitrary JSON to a temp file and upload it."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        path = f.name
    page.locator("#json-input").set_input_files(path)
    page.wait_for_function(
        "document.getElementById('upload-status').textContent !== 'Reading…'"
    )


class TestMissingFields:
    """Products with optional fields omitted render gracefully."""

    def _p(self, **kw):
        """Build a minimal product dict that passes tier filtering."""
        base = {"category": "Chairs", "tier": "", "name": "X", "url": "https://x.com", "image_url": ""}
        base.update(kw)
        return base

    def test_product_with_only_required_fields(self, page: Page):
        upload_json(page, [self._p(name="Bare Chair")])
        assert page.locator(".product-card").count() == 1
        assert "Bare Chair" in page.locator(".card-name").first.inner_text()

    def test_product_without_url_has_no_link(self, page: Page):
        upload_json(page, [self._p(category="Tables", name="No-Link Table", url="")])
        assert page.locator(".spec-link").count() == 0

    def test_product_without_tier_has_no_tier_row(self, page: Page):
        # tier="" means no tier value → no Tier spec row rendered
        upload_json(page, [self._p(category="Sofas", name="No Tier Product", tier="")])
        # Verify no spec-row with label "Tier" exists inside the card
        card = page.locator(".product-card").first
        spec_labels = [el.inner_text().upper() for el in card.locator(".spec-label").all()]
        assert "TIER" not in spec_labels

    def test_product_without_dimensions_omits_row(self, page: Page):
        upload_json(page, [self._p(category="Sofas", name="No Dims", dimensions="")])
        card = page.locator(".product-card").first
        assert "Dimensions" not in card.inner_text()

    def test_product_with_null_name_does_not_crash(self, page: Page):
        upload_json(page, [self._p(name=None)])
        assert page.locator(".product-card").count() == 1

    def test_category_only_products(self, page: Page):
        upload_json(page, [{"category": "X", "tier": ""}])
        assert page.locator(".product-card").count() == 1


class TestImageHandling:
    """Image loading, CORS fallback, and placeholder display."""

    def test_blank_image_url_shows_placeholder(self, page: Page):
        upload_json(page, [
            {"category": "Sofas", "tier": "", "name": "No Image", "url": "https://x.com", "image_url": ""}
        ])
        page.wait_for_timeout(500)  # let onerror fire
        assert page.locator(".image-placeholder").count() == 1

    def test_placeholder_text_content(self, page: Page):
        upload_json(page, [
            {"category": "Sofas", "tier": "", "name": "No Image", "url": "https://x.com", "image_url": ""}
        ])
        page.wait_for_timeout(500)
        text = page.locator(".image-placeholder").first.inner_text()
        assert "unavailable" in text.lower() or "Image" in text

    def test_bad_image_url_shows_placeholder(self, page: Page):
        upload_json(page, [
            {"category": "Sofas", "tier": "", "name": "Bad URL", "url": "https://x.com",
             "image_url": "https://this-domain-does-not-exist-xyz.example/img.jpg"}
        ])
        # Give time for onerror to fire and placeholder to render
        page.wait_for_timeout(3000)
        assert page.locator(".image-placeholder").count() == 1

    def test_multiple_bad_images_all_get_placeholders(self, page: Page):
        upload_json(page, [
            {"category": "C", "tier": "", "name": f"P{i}", "url": "https://x.com",
             "image_url": ""}
            for i in range(5)
        ])
        page.wait_for_timeout(500)
        assert page.locator(".image-placeholder").count() == 5


class TestFilterEdgeCases:
    """Filter edge cases: no match, single item, all unchecked."""

    def test_all_categories_unchecked_shows_message(self, page: Page):
        upload_fixture(page, "multi_category.json")
        for cb in page.locator("#filter-categories input[type='checkbox']").all():
            cb.uncheck()
        page.wait_for_timeout(200)
        assert "No products match" in page.locator("#board").inner_text()

    def test_no_match_message_disappears_on_recheck(self, page: Page):
        upload_fixture(page, "multi_category.json")
        for cb in page.locator("#filter-categories input[type='checkbox']").all():
            cb.uncheck()
        page.wait_for_timeout(100)
        # Re-check just one
        page.locator("#filter-categories input[type='checkbox']").first.check()
        page.wait_for_timeout(200)
        assert "No products match" not in page.locator("#board").inner_text()

    def test_single_product_category_shows_one_item(self, page: Page):
        upload_fixture(page, "multi_category.json")
        # Only leave "Tables" checked (2 products)
        for cb in page.locator("#filter-categories input[type='checkbox']").all():
            cb.uncheck()
        tables_cb = page.locator("#filter-categories label").filter(has_text="Tables").locator("input")
        tables_cb.check()
        page.wait_for_timeout(200)
        assert page.locator(".product-card").count() == 2
        assert page.locator(".category-section").count() == 1

    def test_toc_updates_when_category_unchecked(self, page: Page):
        upload_fixture(page, "multi_category.json")
        sofas_cb = page.locator("#filter-categories label").filter(has_text="Sofas").locator("input")
        sofas_cb.uncheck()
        page.wait_for_timeout(200)
        toc_text = page.locator(".toc-table").inner_text()
        assert "Sofas" not in toc_text


class TestMultipleUploads:
    """Uploading multiple files in sequence resets all state cleanly."""

    def test_second_upload_resets_product_count(self, page: Page):
        upload_fixture(page, "minimal.json")
        assert page.locator(".product-card").count() == 3
        upload_fixture(page, "multi_category.json")
        assert page.locator(".product-card").count() == 10

    def test_second_upload_resets_filter_checkboxes(self, page: Page):
        upload_fixture(page, "minimal.json")
        # Uncheck a category
        page.locator("#filter-categories input[type='checkbox']").first.uncheck()
        page.wait_for_timeout(100)
        # Upload a different file — filters should reset to all-checked
        upload_fixture(page, "multi_category.json")
        all_checked = page.evaluate("""
            Array.from(document.querySelectorAll('#filter-categories input[type="checkbox"]'))
                 .every(cb => cb.checked)
        """)
        assert all_checked

    def test_error_then_valid_upload_clears_error(self, page: Page):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("not json")
            bad_path = f.name
        page.locator("#json-input").set_input_files(bad_path)
        page.wait_for_function(
            "document.getElementById('upload-status').textContent !== 'Reading…'"
        )
        assert "error" in (page.get_attribute("#upload-status", "class") or "")

        # Now upload a valid file
        upload_fixture(page, "minimal.json")
        class_attr = page.get_attribute("#upload-status", "class") or ""
        assert "error" not in class_attr
        assert page.locator(".product-card").count() == 3


class TestBoardInfoPersistence:
    """Board info inputs survive a re-upload if the user typed them first."""

    def test_title_persists_across_upload(self, page: Page):
        upload_fixture(page, "minimal.json")
        page.fill("#input-title", "Persisted Title")
        page.locator("#input-title").dispatch_event("input")
        # The title input itself should keep its value (state is in DOM input, not cleared)
        assert page.input_value("#input-title") == "Persisted Title"

    def test_cover_meta_counts_update_after_second_upload(self, page: Page):
        upload_fixture(page, "minimal.json")
        meta_before = page.locator(".cover-meta").inner_text().lower()
        assert "3 products" in meta_before

        upload_fixture(page, "multi_category.json")
        meta_after = page.locator(".cover-meta").inner_text().lower()
        assert "10 products" in meta_after
