"""
Tests for all sidebar controls: board info, layout, theme, fonts, and filters.

Note: many board elements have CSS text-transform:uppercase applied, so all
inner_text() comparisons are done case-insensitively.
"""
import pytest
from playwright.sync_api import Page

from conftest import upload_fixture


def text(locator) -> str:
    """Return inner_text() lowercased for case-insensitive assertions."""
    return locator.inner_text().lower()


@pytest.fixture(autouse=True)
def loaded(page):
    upload_fixture(page, "multi_category.json")


# ---------------------------------------------------------------------------
# Board info inputs
# ---------------------------------------------------------------------------
class TestBoardInfoInputs:

    def test_title_input_updates_cover(self, page: Page):
        page.fill("#input-title", "My Custom Title")
        page.locator("#input-title").dispatch_event("input")
        assert "my custom title" in text(page.locator(".cover-title"))

    def test_empty_title_falls_back_to_default(self, page: Page):
        page.fill("#input-title", "")
        page.locator("#input-title").dispatch_event("input")
        assert "furniture moodboard" in text(page.locator(".cover-title"))

    def test_subtitle_updates_eyebrow(self, page: Page):
        page.fill("#input-subtitle", "Spring Collection")
        page.locator("#input-subtitle").dispatch_event("input")
        assert "spring collection" in text(page.locator(".cover-eyebrow"))

    def test_empty_subtitle_shows_fallback_eyebrow(self, page: Page):
        page.fill("#input-subtitle", "")
        page.locator("#input-subtitle").dispatch_event("input")
        assert "curated selection" in text(page.locator(".cover-eyebrow"))

    def test_client_appears_in_cover_meta(self, page: Page):
        page.fill("#input-client", "Studio Acme")
        page.locator("#input-client").dispatch_event("input")
        assert "studio acme" in text(page.locator(".cover-meta"))

    def test_client_appears_in_footer_brand(self, page: Page):
        page.fill("#input-client", "Studio Acme")
        page.locator("#input-client").dispatch_event("input")
        assert "studio acme" in text(page.locator(".footer-brand"))

    def test_date_appears_in_cover_meta(self, page: Page):
        page.fill("#input-date", "1 January 2030")
        page.locator("#input-date").dispatch_event("input")
        assert "1 january 2030" in text(page.locator(".cover-meta"))

    def test_date_appears_in_footer(self, page: Page):
        page.fill("#input-date", "1 January 2030")
        page.locator("#input-date").dispatch_event("input")
        assert "1 january 2030" in text(page.locator("#board-footer-date"))

    def test_title_input_default_value(self, page: Page):
        assert page.input_value("#input-title") == "Furniture Selection"


# ---------------------------------------------------------------------------
# Layout controls
# ---------------------------------------------------------------------------
class TestLayoutControls:

    def _select_layout(self, page: Page, value: str):
        # Radio inputs are visually hidden; click the wrapping label instead
        page.locator(f"label.layout-option:has(input[value='{value}'])").click()
        page.wait_for_timeout(100)

    def test_default_layout_is_grid3(self, page: Page):
        grid = page.locator(".card-grid").first
        assert "layout-grid3" in (grid.get_attribute("class") or "")

    def test_grid2_applies_correct_class(self, page: Page):
        self._select_layout(page, "grid2")
        grid = page.locator(".card-grid").first
        assert "layout-grid2" in (grid.get_attribute("class") or "")

    def test_grid3_applies_correct_class(self, page: Page):
        self._select_layout(page, "grid2")  # switch away first
        self._select_layout(page, "grid3")
        grid = page.locator(".card-grid").first
        assert "layout-grid3" in (grid.get_attribute("class") or "")

    def test_editorial_applies_correct_class(self, page: Page):
        self._select_layout(page, "editorial")
        grid = page.locator(".card-grid").first
        assert "layout-editorial" in (grid.get_attribute("class") or "")

    def test_layout_change_preserves_cards(self, page: Page):
        count_before = page.locator(".product-card").count()
        self._select_layout(page, "grid2")
        assert page.locator(".product-card").count() == count_before

    def test_all_grids_have_layout_class(self, page: Page):
        """Every card-grid in the board must have a layout-* class."""
        self._select_layout(page, "editorial")
        for grid in page.locator(".card-grid").all():
            cls = grid.get_attribute("class") or ""
            assert "layout-editorial" in cls


# ---------------------------------------------------------------------------
# Theme controls
# ---------------------------------------------------------------------------
class TestThemeControls:

    def _apply_theme(self, page: Page, theme: str):
        page.locator(f"button.theme-swatch[data-theme='{theme}']").click()
        page.wait_for_timeout(100)

    def _css_var(self, page: Page, var: str) -> str:
        return page.evaluate(
            f"getComputedStyle(document.documentElement).getPropertyValue('{var}').trim()"
        )

    def test_default_theme_is_noir(self, page: Page):
        assert "#1a1a18" in self._css_var(page, "--bg")

    def test_linen_theme_sets_bg(self, page: Page):
        self._apply_theme(page, "linen")
        assert "#faf9f6" in self._css_var(page, "--bg")

    def test_slate_theme_sets_bg(self, page: Page):
        self._apply_theme(page, "slate")
        assert "#f4f4f2" in self._css_var(page, "--bg")

    def test_chalk_theme_sets_bg(self, page: Page):
        self._apply_theme(page, "chalk")
        assert "#ffffff" in self._css_var(page, "--bg")

    def test_noir_theme_sets_ink(self, page: Page):
        self._apply_theme(page, "noir")
        assert "#faf9f6" in self._css_var(page, "--ink")

    def test_linen_theme_sets_ink(self, page: Page):
        self._apply_theme(page, "linen")
        assert "#1a1a18" in self._css_var(page, "--ink")

    def test_active_swatch_gets_active_class(self, page: Page):
        self._apply_theme(page, "linen")
        cls = page.locator("button.theme-swatch[data-theme='linen']").get_attribute("class") or ""
        assert "active" in cls

    def test_previous_swatch_loses_active_class(self, page: Page):
        self._apply_theme(page, "linen")
        cls = page.locator("button.theme-swatch[data-theme='noir']").get_attribute("class") or ""
        assert "active" not in cls

    def test_all_themes_set_distinct_bg(self, page: Page):
        """Each of the four themes must produce a unique --bg value."""
        bgs = set()
        for theme in ("linen", "slate", "chalk", "noir"):
            self._apply_theme(page, theme)
            bgs.add(self._css_var(page, "--bg"))
        assert len(bgs) == 4


# ---------------------------------------------------------------------------
# Font controls
# ---------------------------------------------------------------------------
class TestFontControls:

    def _apply_font(self, page: Page, name: str):
        page.locator(f"button.font-option[data-fonts='{name}']").click()
        page.wait_for_timeout(100)

    def _css_var(self, page: Page, var: str) -> str:
        return page.evaluate(
            f"getComputedStyle(document.documentElement).getPropertyValue('{var}').trim()"
        )

    def test_default_font_is_classic(self, page: Page):
        assert "Georgia" in self._css_var(page, "--serif")

    def test_modern_font_sets_serif(self, page: Page):
        self._apply_font(page, "modern")
        assert "Bodoni" in self._css_var(page, "--serif")

    def test_slab_font_sets_serif(self, page: Page):
        self._apply_font(page, "slab")
        assert "Rockwell" in self._css_var(page, "--serif")

    def test_classic_font_sets_sans(self, page: Page):
        self._apply_font(page, "classic")
        assert "Helvetica" in self._css_var(page, "--sans")

    def test_active_font_button_gets_active_class(self, page: Page):
        self._apply_font(page, "modern")
        cls = page.locator("button.font-option[data-fonts='modern']").get_attribute("class") or ""
        assert "active" in cls

    def test_previous_font_button_loses_active_class(self, page: Page):
        self._apply_font(page, "modern")
        cls = page.locator("button.font-option[data-fonts='classic']").get_attribute("class") or ""
        assert "active" not in cls

    def test_all_fonts_produce_different_serif(self, page: Page):
        serifs = set()
        for name in ("classic", "modern", "slab"):
            self._apply_font(page, name)
            serifs.add(self._css_var(page, "--serif"))
        assert len(serifs) == 3


# ---------------------------------------------------------------------------
# Filter controls  (multi_category.json: 4 categories, 3 tiers + no-tier)
# ---------------------------------------------------------------------------
class TestCategoryFilter:

    def test_all_categories_shown_by_default(self, page: Page):
        assert page.locator(".category-section").count() == 4

    def test_unchecking_category_hides_its_section(self, page: Page):
        sofas_cb = page.locator("#filter-categories label").filter(has_text="Sofas").locator("input")
        sofas_cb.uncheck()
        page.wait_for_timeout(200)
        headings = [h.inner_text().upper() for h in page.locator(".category-section h2").all()]
        assert "SOFAS" not in headings

    def test_unchecked_products_removed_from_count(self, page: Page):
        sofas_cb = page.locator("#filter-categories label").filter(has_text="Sofas").locator("input")
        sofas_cb.uncheck()
        page.wait_for_timeout(200)
        # 3 Sofas removed from 10 → 7 cards
        assert page.locator(".product-card").count() == 7

    def test_rechecking_category_restores_section(self, page: Page):
        sofas_cb = page.locator("#filter-categories label").filter(has_text="Sofas").locator("input")
        sofas_cb.uncheck()
        page.wait_for_timeout(100)
        sofas_cb.check()
        page.wait_for_timeout(200)
        headings = [h.inner_text().upper() for h in page.locator(".category-section h2").all()]
        assert "SOFAS" in headings

    def test_unchecking_all_categories_shows_no_match_message(self, page: Page):
        for cb in page.locator("#filter-categories input[type='checkbox']").all():
            cb.uncheck()
        page.wait_for_timeout(200)
        assert "No products match" in page.locator("#board").inner_text()

    def test_filter_checkboxes_all_checked_initially(self, page: Page):
        all_checked = page.evaluate("""
            Array.from(document.querySelectorAll('#filter-categories input[type="checkbox"]'))
                 .every(cb => cb.checked)
        """)
        assert all_checked

    def test_four_category_checkboxes_present(self, page: Page):
        count = page.locator("#filter-categories input[type='checkbox']").count()
        assert count == 4


class TestTierFilter:

    def test_all_tiers_shown_by_default(self, page: Page):
        assert page.locator(".product-card").count() == 10

    def test_unchecking_tier_hides_its_products(self, page: Page):
        tier_cb = page.locator("#filter-tiers label").filter(has_text="High-end").locator("input")
        tier_cb.uncheck()
        page.wait_for_timeout(200)
        # 2 high-end sofas + 1 high-end table = 3 removed from 10 → 7
        assert page.locator(".product-card").count() == 7

    def test_unchecking_no_tier_products(self, page: Page):
        # Chairs have tier="" → shown as "(no tier)" in filter
        no_tier_cb = page.locator("#filter-tiers label").filter(has_text="(no tier)").locator("input")
        no_tier_cb.uncheck()
        page.wait_for_timeout(200)
        assert page.locator(".product-card").count() == 8  # 2 chairs removed

    def test_combined_category_and_tier_filter(self, page: Page):
        sofas_cb = page.locator("#filter-categories label").filter(has_text="Sofas").locator("input")
        budget_cb = page.locator("#filter-tiers label").filter(has_text="Budget").locator("input")
        sofas_cb.uncheck()
        budget_cb.uncheck()
        page.wait_for_timeout(200)
        # 3 sofas + 3 lamps (budget) removed → 4 remaining (2 tables + 2 chairs)
        assert page.locator(".product-card").count() == 4
