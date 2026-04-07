"""
Tests for the export-selection feature.

Covers:
  - Sidebar section visibility before/after upload
  - Default state (all products de-selected)
  - Card click to toggle selection (and badge visibility)
  - "Select visible" button
  - "Clear all" button
  - Interaction between selection and category/tier filters
  - Export blocked when nothing selected (alert, no overlay)
  - DOM filter applied during capture (non-selected cards hidden)
  - CSS 'exporting' class suppresses visual indicators
  - Selection preserved across layout re-renders
  - Selection reset when a new JSON file is loaded

Fixture data reference:
  minimal.json       – 3 products: Sofa A (Sofas/High-end),
                       Cloud Sofa (Sofas/Mid-range), Slab Table (Tables/High-end)
  multi_category.json – 10 products across 4 categories and 3 tier values
"""
import pytest
from playwright.sync_api import Page

from conftest import upload_fixture, FIXTURES_DIR


# ---------------------------------------------------------------------------
# Default autouse fixture — minimal.json (3 products, 2 categories)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def loaded(page):
    upload_fixture(page, "minimal.json")


# ============================================================
# Sidebar visibility
# ============================================================
class TestSidebarVisibility:

    def test_section_hidden_before_upload(self, browser_instance, app_url):
        """Section must not be visible on a fresh page with no data loaded."""
        ctx = browser_instance.new_context()
        pg = ctx.new_page()
        pg.goto(f"{app_url}/index.html")
        pg.wait_for_load_state("domcontentloaded")
        display = pg.evaluate(
            "document.getElementById('section-export-selection').style.display"
        )
        ctx.close()
        assert display == "none"

    def test_section_visible_after_upload(self, page: Page):
        display = page.evaluate(
            "document.getElementById('section-export-selection').style.display"
        )
        assert display != "none"

    def test_rule_visible_after_upload(self, page: Page):
        display = page.evaluate(
            "document.getElementById('rule-export-selection').style.display"
        )
        assert display != "none"

    def test_initial_count_text_no_products_selected(self, page: Page):
        text = page.locator("#export-sel-count").inner_text().lower()
        assert "no products selected" in text

    def test_select_visible_button_present(self, page: Page):
        assert page.locator("#btn-sel-visible").count() == 1

    def test_clear_all_button_present(self, page: Page):
        assert page.locator("#btn-sel-clear").count() == 1


# ============================================================
# Default state — all de-selected
# ============================================================
class TestDefaultState:

    def test_no_cards_selected_by_default(self, page: Page):
        count = page.evaluate("state.exportSelection.size")
        assert count == 0

    def test_no_cards_have_selected_class_by_default(self, page: Page):
        selected = page.locator(".product-card.export-selected").count()
        assert selected == 0

    def test_state_export_selection_is_empty_set(self, page: Page):
        is_set = page.evaluate("state.exportSelection instanceof Set")
        assert is_set
        size = page.evaluate("state.exportSelection.size")
        assert size == 0


# ============================================================
# Card click — toggle
# ============================================================
class TestCardClickToggle:

    def test_clicking_card_adds_export_selected_class(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        cls = page.locator(".product-card").first.get_attribute("class") or ""
        assert "export-selected" in cls

    def test_clicking_card_increments_state_set(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 1

    def test_clicking_selected_card_removes_class(self, page: Page):
        card = page.locator(".product-card").first
        card.click()
        page.wait_for_timeout(100)
        card.click()
        page.wait_for_timeout(100)
        cls = card.get_attribute("class") or ""
        assert "export-selected" not in cls

    def test_clicking_selected_card_decrements_state_set(self, page: Page):
        card = page.locator(".product-card").first
        card.click()
        page.wait_for_timeout(100)
        card.click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 0

    def test_multiple_cards_selectable(self, page: Page):
        cards = page.locator(".product-card").all()
        for card in cards:
            card.click()
            page.wait_for_timeout(50)
        assert page.evaluate("state.exportSelection.size") == len(cards)

    def test_count_text_updates_on_select(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        text = page.locator("#export-sel-count").inner_text().lower()
        assert "1 product" in text

    def test_count_text_updates_on_deselect(self, page: Page):
        card = page.locator(".product-card").first
        card.click()
        page.wait_for_timeout(100)
        card.click()
        page.wait_for_timeout(100)
        text = page.locator("#export-sel-count").inner_text().lower()
        assert "no products selected" in text

    def test_count_text_uses_plural_for_multiple(self, page: Page):
        for card in page.locator(".product-card").all():
            card.click()
            page.wait_for_timeout(50)
        text = page.locator("#export-sel-count").inner_text().lower()
        assert "products selected" in text

    def test_count_text_uses_singular_for_one(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        text = page.locator("#export-sel-count").inner_text()
        assert "1 product selected" in text
        assert "products" not in text  # must be singular

    def test_link_click_inside_card_does_not_toggle(self, page: Page):
        """Clicking a <a> inside a card must not trigger selection toggle."""
        result = page.evaluate("""() => {
            const link = document.querySelector('.spec-link');
            if (!link) return -1;
            // Dispatch a bubbling click from the anchor
            link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            return state.exportSelection.size;
        }""")
        assert result == 0


# ============================================================
# Checkmark badge visibility
# ============================================================
class TestSelectionBadge:

    def test_badge_not_visible_on_unselected_card(self, page: Page):
        badge = page.locator(".product-card").first.locator(".export-sel-badge")
        opacity = badge.evaluate("el => parseFloat(getComputedStyle(el).opacity)")
        assert opacity == 0.0

    def test_badge_visible_on_selected_card(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(300)  # allow CSS transition (0.12 s) to settle
        badge = page.locator(".product-card.export-selected").first.locator(".export-sel-badge")
        opacity = badge.evaluate("el => parseFloat(getComputedStyle(el).opacity)")
        assert opacity > 0.9

    def test_badge_disappears_when_card_deselected(self, page: Page):
        card = page.locator(".product-card").first
        card.click()
        page.wait_for_timeout(300)
        card.click()
        page.wait_for_timeout(300)  # allow CSS transition (0.12 s) to settle
        badge = card.locator(".export-sel-badge")
        opacity = badge.evaluate("el => parseFloat(getComputedStyle(el).opacity)")
        assert opacity < 0.1

    def test_badge_contains_checkmark(self, page: Page):
        badge = page.locator(".product-card").first.locator(".export-sel-badge")
        assert "✓" in badge.inner_text()


# ============================================================
# "Select visible" button
# ============================================================
class TestSelectVisibleButton:

    def test_select_visible_selects_all_products(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 3  # minimal.json

    def test_select_visible_adds_class_to_all_cards(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        total = page.locator(".product-card").count()
        selected = page.locator(".product-card.export-selected").count()
        assert selected == total

    def test_select_visible_updates_count_text(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        text = page.locator("#export-sel-count").inner_text().lower()
        assert "3 products selected" in text

    def test_select_visible_respects_category_filter(self, page: Page):
        """'Select visible' after hiding a category must not select those products."""
        upload_fixture(page, "multi_category.json")  # 10 products, 4 categories
        # Hide Sofas (3 products)
        sofas_cb = page.locator("#filter-categories label").filter(has_text="Sofas").locator("input")
        sofas_cb.uncheck()
        page.wait_for_timeout(200)
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        # 10 - 3 Sofas = 7 should be selected
        assert page.evaluate("state.exportSelection.size") == 7

    def test_select_visible_respects_tier_filter(self, page: Page):
        """'Select visible' after hiding a tier must not select those products."""
        upload_fixture(page, "multi_category.json")
        # Hide Budget tier (3 Lamps)
        budget_cb = page.locator("#filter-tiers label").filter(has_text="Budget").locator("input")
        budget_cb.uncheck()
        page.wait_for_timeout(200)
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        # 10 - 3 Budget = 7 selected
        assert page.evaluate("state.exportSelection.size") == 7

    def test_select_visible_is_idempotent(self, page: Page):
        """Clicking 'Select visible' twice should not double-count."""
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 3


# ============================================================
# "Clear all" button
# ============================================================
class TestClearAllButton:

    def test_clear_all_removes_all_selections(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        page.locator("#btn-sel-clear").click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 0

    def test_clear_all_removes_selected_class_from_all_cards(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        page.locator("#btn-sel-clear").click()
        page.wait_for_timeout(100)
        assert page.locator(".product-card.export-selected").count() == 0

    def test_clear_all_resets_count_text(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        page.locator("#btn-sel-clear").click()
        page.wait_for_timeout(100)
        text = page.locator("#export-sel-count").inner_text().lower()
        assert "no products selected" in text

    def test_clear_all_when_nothing_selected_is_safe(self, page: Page):
        """Clear all on an empty selection must not raise or change state."""
        page.locator("#btn-sel-clear").click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 0
        text = page.locator("#export-sel-count").inner_text().lower()
        assert "no products selected" in text

    def test_select_then_clear_then_reselect(self, page: Page):
        """Full cycle: select → clear → re-select should work correctly."""
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        page.locator("#btn-sel-clear").click()
        page.wait_for_timeout(100)
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 3


# ============================================================
# Export blocked when nothing is selected
# ============================================================
class TestExportBlockedWithNoSelection:

    def _capture_alert(self, page: Page, btn_id: str) -> str:
        alerts = []
        page.once("dialog", lambda d: alerts.append(d.message))
        page.locator(btn_id).click()
        page.wait_for_timeout(500)
        return alerts[0] if alerts else ""

    def test_png_export_shows_alert_when_nothing_selected(self, page: Page):
        msg = self._capture_alert(page, "#btn-export-png")
        assert msg != "", "Expected an alert when no products are selected"

    def test_pdf_export_shows_alert_when_nothing_selected(self, page: Page):
        msg = self._capture_alert(page, "#btn-export-pdf")
        assert msg != "", "Expected an alert when no products are selected"

    def test_png_alert_message_mentions_select(self, page: Page):
        msg = self._capture_alert(page, "#btn-export-png")
        assert "select" in msg.lower()

    def test_pdf_alert_message_mentions_select(self, page: Page):
        msg = self._capture_alert(page, "#btn-export-pdf")
        assert "select" in msg.lower()

    def test_png_export_overlay_never_appears_when_nothing_selected(self, page: Page):
        page.locator("#btn-export-png").click()
        page.wait_for_timeout(500)
        display = page.evaluate(
            "document.getElementById('export-overlay').style.display"
        )
        assert display == "none"

    def test_pdf_export_overlay_never_appears_when_nothing_selected(self, page: Page):
        page.locator("#btn-export-pdf").click()
        page.wait_for_timeout(500)
        display = page.evaluate(
            "document.getElementById('export-overlay').style.display"
        )
        assert display == "none"

    def test_export_buttons_remain_enabled_after_blocked_export(self, page: Page):
        page.locator("#btn-export-png").click()
        page.wait_for_timeout(500)
        assert page.get_attribute("#btn-export-png", "disabled") is None
        assert page.get_attribute("#btn-export-pdf", "disabled") is None


# ============================================================
# DOM filter applied during capture
# ============================================================
class TestExportDOMFilter:
    """
    Tests that call applyExportFilter / restoreExportFilter directly to verify
    the DOM manipulation without triggering a full html2canvas render.
    """

    def test_apply_filter_hides_non_selected_cards(self, page: Page):
        # Select only first card (1 of 3)
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        hidden_count = page.evaluate("""() => {
            const { hiddenCards, hiddenSections } = applyExportFilter();
            const n = hiddenCards.length;
            restoreExportFilter(hiddenCards, hiddenSections);
            return n;
        }""")
        assert hidden_count == 2  # 3 total − 1 selected

    def test_apply_filter_keeps_selected_cards_visible(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        visible = page.evaluate("""() => {
            const { hiddenCards, hiddenSections } = applyExportFilter();
            const visible = document.querySelectorAll(
                '#board .product-card:not([style*="display: none"])'
            ).length;
            restoreExportFilter(hiddenCards, hiddenSections);
            return visible;
        }""")
        assert visible == 1

    def test_apply_filter_hides_empty_category_sections(self, page: Page):
        # Select only Table card (only product in Tables category)
        # → Sofas category should be fully hidden
        cards = page.locator(".product-card").all()
        # Click the last card (Slab Table is the 3rd product)
        cards[-1].click()
        page.wait_for_timeout(100)
        hidden_sections = page.evaluate("""() => {
            const { hiddenCards, hiddenSections } = applyExportFilter();
            const n = hiddenSections.length;
            restoreExportFilter(hiddenCards, hiddenSections);
            return n;
        }""")
        assert hidden_sections == 1  # Sofas section is empty → hidden

    def test_apply_filter_does_not_hide_non_empty_category_sections(self, page: Page):
        # Select one Sofa → Sofas section has a visible card → should NOT be hidden
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        hidden_sections = page.evaluate("""() => {
            const { hiddenCards, hiddenSections } = applyExportFilter();
            const n = hiddenSections.length;
            restoreExportFilter(hiddenCards, hiddenSections);
            return n;
        }""")
        # Tables section is empty, Sofas has 1 visible card
        assert hidden_sections == 1

    def test_restore_filter_brings_back_all_cards(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        page.evaluate("""() => {
            const { hiddenCards, hiddenSections } = applyExportFilter();
            restoreExportFilter(hiddenCards, hiddenSections);
        }""")
        page.wait_for_timeout(100)
        visible = page.locator(".product-card").count()
        assert visible == 3

    def test_restore_filter_brings_back_all_sections(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        page.evaluate("""() => {
            const { hiddenCards, hiddenSections } = applyExportFilter();
            restoreExportFilter(hiddenCards, hiddenSections);
        }""")
        page.wait_for_timeout(100)
        sections = page.locator(".category-section").count()
        assert sections == 2  # Sofas + Tables

    def test_apply_filter_all_selected_hides_nothing(self, page: Page):
        """When all products are selected, nothing should be hidden."""
        for card in page.locator(".product-card").all():
            card.click()
            page.wait_for_timeout(50)
        result = page.evaluate("""() => {
            const { hiddenCards, hiddenSections } = applyExportFilter();
            const r = { cards: hiddenCards.length, sections: hiddenSections.length };
            restoreExportFilter(hiddenCards, hiddenSections);
            return r;
        }""")
        assert result["cards"] == 0
        assert result["sections"] == 0


# ============================================================
# CSS 'exporting' class suppresses visual indicators
# ============================================================
class TestExportingCSS:

    def test_exporting_class_hides_badge(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        page.evaluate("document.body.classList.add('exporting')")
        display = page.locator(".product-card.export-selected .export-sel-badge").first.evaluate(
            "el => getComputedStyle(el).display"
        )
        page.evaluate("document.body.classList.remove('exporting')")
        assert display == "none"

    def test_exporting_class_removes_box_shadow(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        page.evaluate("document.body.classList.add('exporting')")
        shadow = page.locator(".product-card.export-selected").first.evaluate(
            "el => getComputedStyle(el).boxShadow"
        )
        page.evaluate("document.body.classList.remove('exporting')")
        assert shadow in ("none", "")

    def test_badge_visible_again_after_exporting_class_removed(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(300)
        page.evaluate("document.body.classList.add('exporting')")
        page.evaluate("document.body.classList.remove('exporting')")
        page.wait_for_timeout(300)  # allow CSS transition (0.12 s) to settle
        opacity = page.locator(".product-card.export-selected .export-sel-badge").first.evaluate(
            "el => parseFloat(getComputedStyle(el).opacity)"
        )
        assert opacity > 0.9

    def test_box_shadow_restored_after_exporting_class_removed(self, page: Page):
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        shadow_before = page.locator(".product-card.export-selected").first.evaluate(
            "el => getComputedStyle(el).boxShadow"
        )
        page.evaluate("document.body.classList.add('exporting')")
        page.evaluate("document.body.classList.remove('exporting')")
        shadow_after = page.locator(".product-card.export-selected").first.evaluate(
            "el => getComputedStyle(el).boxShadow"
        )
        assert shadow_after == shadow_before
        assert shadow_after not in ("none", "")


# ============================================================
# Selection persistence across re-renders
# ============================================================
class TestSelectionPersistence:

    def test_selection_survives_layout_change(self, page: Page):
        """Switching layout triggers renderBoard(); selection must persist."""
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        # Switch to 2-col layout (triggers full re-render)
        page.locator("label.layout-option:has(input[value='grid2'])").click()
        page.wait_for_timeout(200)
        assert page.evaluate("state.exportSelection.size") == 1
        assert page.locator(".product-card.export-selected").count() == 1

    def test_selection_survives_theme_change(self, page: Page):
        """Changing theme does not wipe selection."""
        page.locator(".product-card").first.click()
        page.wait_for_timeout(100)
        page.locator("button.theme-swatch[data-theme='linen']").click()
        page.wait_for_timeout(200)
        assert page.evaluate("state.exportSelection.size") == 1

    def test_products_filtered_out_remain_in_state_selection(self, page: Page):
        """
        Products removed from the board by a filter are still in exportSelection
        (they were selected before the filter was applied).
        """
        upload_fixture(page, "multi_category.json")
        # Select all 10 products
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 10
        # Now hide Sofas — the 3 sofa product objects stay in the Set
        sofas_cb = page.locator("#filter-categories label").filter(has_text="Sofas").locator("input")
        sofas_cb.uncheck()
        page.wait_for_timeout(200)
        # State set still holds 10 (objects are not removed when filtered out)
        assert page.evaluate("state.exportSelection.size") == 10

    def test_count_text_reflects_full_selection_even_when_filtered(self, page: Page):
        """Count shows total selected, not just visible-selected."""
        upload_fixture(page, "multi_category.json")
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        sofas_cb = page.locator("#filter-categories label").filter(has_text="Sofas").locator("input")
        sofas_cb.uncheck()
        page.wait_for_timeout(200)
        text = page.locator("#export-sel-count").inner_text()
        assert "10 products selected" in text


# ============================================================
# Selection reset on new upload
# ============================================================
class TestSelectionResetOnUpload:

    def test_selection_cleared_on_new_upload(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        assert page.evaluate("state.exportSelection.size") == 3
        # Upload a new file
        upload_fixture(page, "multi_category.json")
        assert page.evaluate("state.exportSelection.size") == 0

    def test_no_cards_selected_after_new_upload(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        upload_fixture(page, "multi_category.json")
        assert page.locator(".product-card.export-selected").count() == 0

    def test_count_text_resets_after_new_upload(self, page: Page):
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        upload_fixture(page, "multi_category.json")
        text = page.locator("#export-sel-count").inner_text().lower()
        assert "no products selected" in text

    def test_export_blocked_after_new_upload_until_selected(self, page: Page):
        """After a new upload selection is empty, so export must be blocked."""
        page.locator("#btn-sel-visible").click()
        page.wait_for_timeout(100)
        upload_fixture(page, "multi_category.json")

        alerts = []
        page.once("dialog", lambda d: alerts.append(d.message))
        page.locator("#btn-export-png").click()
        page.wait_for_timeout(500)
        assert len(alerts) == 1
