"""
Tests for JSON upload, parsing, and status feedback.
"""
import json
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import Page

from conftest import upload_fixture, FIXTURES_DIR


class TestInitialState:
    """App loads with a clean slate before any file is uploaded."""

    def test_empty_state_heading_visible(self, page: Page):
        heading = page.locator("#empty-state .empty-heading")
        assert heading.is_visible()
        assert "moodboard begins" in heading.inner_text().lower()

    def test_empty_state_body_visible(self, page: Page):
        body = page.locator("#empty-state .empty-body")
        assert body.is_visible()
        assert "upload" in body.inner_text().lower()

    def test_export_buttons_disabled_before_upload(self, page: Page):
        assert page.get_attribute("#btn-export-png", "disabled") is not None
        assert page.get_attribute("#btn-export-pdf", "disabled") is not None

    def test_upload_status_empty_before_upload(self, page: Page):
        assert page.locator("#upload-status").inner_text().strip() == ""

    def test_filter_section_hidden_before_upload(self, page: Page):
        assert page.evaluate(
            "document.getElementById('section-filters').style.display"
        ) == "none"

    def test_drop_zone_visible(self, page: Page):
        assert page.locator("#drop-zone").is_visible()

    def test_board_has_no_product_cards_initially(self, page: Page):
        assert page.locator(".product-card").count() == 0


class TestSuccessfulUpload:
    """Uploading a valid JSON file populates the board."""

    def test_status_shows_product_count(self, page: Page):
        upload_fixture(page, "minimal.json")
        status = page.locator("#upload-status").inner_text()
        assert "3 products loaded" in status

    def test_status_has_no_error_class(self, page: Page):
        upload_fixture(page, "minimal.json")
        class_attr = page.get_attribute("#upload-status", "class") or ""
        assert "error" not in class_attr

    def test_export_buttons_enabled_after_upload(self, page: Page):
        upload_fixture(page, "minimal.json")
        assert page.get_attribute("#btn-export-png", "disabled") is None
        assert page.get_attribute("#btn-export-pdf", "disabled") is None

    def test_empty_state_disappears_after_upload(self, page: Page):
        upload_fixture(page, "minimal.json")
        assert page.locator("#empty-state").count() == 0

    def test_product_cards_rendered(self, page: Page):
        upload_fixture(page, "minimal.json")
        assert page.locator(".product-card").count() == 3

    def test_filter_section_visible_after_upload(self, page: Page):
        upload_fixture(page, "minimal.json")
        assert page.evaluate(
            "document.getElementById('section-filters').style.display"
        ) != "none"

    def test_uploading_second_file_replaces_first(self, page: Page):
        upload_fixture(page, "minimal.json")
        assert page.locator(".product-card").count() == 3

        upload_fixture(page, "multi_category.json")
        status = page.locator("#upload-status").inner_text()
        assert "10 products loaded" in status
        assert page.locator(".product-card").count() == 10

    def test_large_fixture_loads_all_products(self, page: Page):
        upload_fixture(page, "multi_category.json")
        status = page.locator("#upload-status").inner_text()
        assert "10 products loaded" in status


class TestUploadErrors:
    """Invalid files produce clear, recoverable error states."""

    def _upload_text(self, page: Page, content: str, suffix=".json") -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            path = f.name
        page.locator("#json-input").set_input_files(path)
        page.wait_for_function(
            "document.getElementById('upload-status').textContent !== 'Reading…'"
        )

    def test_invalid_json_shows_error_status(self, page: Page):
        self._upload_text(page, "this is not json")
        status = page.locator("#upload-status").inner_text()
        assert "error" in status.lower() or "Error" in status

    def test_invalid_json_status_has_error_class(self, page: Page):
        self._upload_text(page, "{ broken }")
        class_attr = page.get_attribute("#upload-status", "class") or ""
        assert "error" in class_attr

    def test_non_array_json_shows_error(self, page: Page):
        self._upload_text(page, '{"not": "an array"}')
        status = page.locator("#upload-status").inner_text()
        assert "Error" in status or "error" in status.lower()

    def test_export_buttons_stay_disabled_after_error(self, page: Page):
        self._upload_text(page, "bad json")
        assert page.get_attribute("#btn-export-png", "disabled") is not None
        assert page.get_attribute("#btn-export-pdf", "disabled") is not None

    def test_board_stays_empty_after_error(self, page: Page):
        self._upload_text(page, "bad json")
        assert page.locator(".product-card").count() == 0

    def test_empty_array_loads_zero_products(self, page: Page):
        upload_fixture(page, "empty.json")
        status = page.locator("#upload-status").inner_text()
        assert "0 products loaded" in status

    def test_empty_array_shows_empty_state(self, page: Page):
        upload_fixture(page, "empty.json")
        assert page.locator("#empty-state").count() == 1
