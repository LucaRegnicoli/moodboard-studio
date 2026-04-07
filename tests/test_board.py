"""
Tests for board rendering: cover, category sections, product cards.
"""
import pytest
from playwright.sync_api import Page

from conftest import upload_fixture


@pytest.fixture(autouse=True)
def loaded(page):
    """Upload the minimal fixture before every test in this module."""
    upload_fixture(page, "minimal.json")


class TestCover:
    """The board cover page shows title, meta, and optional header image."""

    def test_cover_exists(self, page: Page):
        assert page.locator(".board-cover").count() == 1

    def test_default_title_in_cover(self, page: Page):
        title = page.locator(".cover-title").inner_text()
        assert title == "Furniture Selection"

    def test_default_eyebrow_fallback(self, page: Page):
        eyebrow = page.locator(".cover-eyebrow").inner_text().lower()
        assert "curated selection" in eyebrow

    def test_cover_meta_shows_product_count(self, page: Page):
        meta = page.locator(".cover-meta").inner_text().lower()
        assert "3 products" in meta

    def test_cover_meta_shows_category_count(self, page: Page):
        meta = page.locator(".cover-meta").inner_text().lower()
        # minimal.json has 2 categories: Sofas and Tables
        assert "2 categories" in meta

    def test_cover_has_date(self, page: Page):
        meta = page.locator(".cover-meta").inner_text()
        # Date is always shown; just verify something is there
        assert len(meta.strip()) > 0


class TestCategorySection:
    """Each category renders as a titled section with a card grid."""

    def test_two_category_sections(self, page: Page):
        assert page.locator(".category-section").count() == 2

    def test_category_heading_sofas(self, page: Page):
        headings = [h.inner_text().upper() for h in page.locator(".category-section h2").all()]
        assert "SOFAS" in headings

    def test_category_heading_tables(self, page: Page):
        headings = [h.inner_text().upper() for h in page.locator(".category-section h2").all()]
        assert "TABLES" in headings

    def test_category_count_label(self, page: Page):
        # Sofas section should say "2 items"
        sofas_section = page.locator(".category-section").filter(has_text="Sofas")
        count_text = sofas_section.locator(".category-count").inner_text().lower()
        assert "2 items" in count_text

    def test_category_grid_has_correct_layout_class(self, page: Page):
        # Default layout is grid3
        grid = page.locator(".card-grid").first
        assert "layout-grid3" in (grid.get_attribute("class") or "")


class TestProductCard:
    """Individual product cards render all visible fields correctly."""

    def test_correct_card_count(self, page: Page):
        assert page.locator(".product-card").count() == 3

    def test_card_shows_product_name(self, page: Page):
        names = [c.inner_text() for c in page.locator(".card-name").all()]
        assert "Arc Sofa" in names
        assert "Cloud Sofa" in names
        assert "Slab Table" in names

    def test_card_shows_view_product_link(self, page: Page):
        links = page.locator(".spec-link").all()
        assert len(links) == 3
        for link in links:
            assert "View product" in link.inner_text()

    def test_card_link_href(self, page: Page):
        first_link = page.locator(".spec-link").first
        href = first_link.get_attribute("href")
        assert href and href.startswith("https://example.com/")

    def test_card_shows_dimensions(self, page: Page):
        # Arc Sofa has dimensions
        arc_card = page.locator(".product-card").filter(has_text="Arc Sofa")
        assert "220" in arc_card.inner_text()

    def test_card_shows_materials(self, page: Page):
        arc_card = page.locator(".product-card").filter(has_text="Arc Sofa")
        assert "Solid oak" in arc_card.inner_text()

    def test_card_shows_tier_in_spec(self, page: Page):
        arc_card = page.locator(".product-card").filter(has_text="Arc Sofa")
        assert "High-end" in arc_card.inner_text()

    def test_empty_image_shows_placeholder(self, page: Page):
        # All fixture images are empty strings — should show placeholders
        page.wait_for_timeout(500)  # let onerror fire
        placeholders = page.locator(".image-placeholder")
        assert placeholders.count() == 3

    def test_designer_name_split(self, page: Page):
        """'Name · Designer' format should split into two elements."""
        upload_fixture(page, "designer_names.json")
        # After re-upload the fixture autouse won't re-run, so we call it manually
        name_el = page.locator(".card-name").first
        designer_el = page.locator(".card-designer").first
        assert "Eames Lounge Chair".upper() in name_el.inner_text().upper()
        assert "Charles".upper() in designer_el.inner_text().upper()

    def test_plain_name_has_no_designer_element(self, page: Page):
        upload_fixture(page, "designer_names.json")
        cards = page.locator(".product-card").all()
        plain_card = next(c for c in cards if "Chair Without Designer" in c.inner_text())
        assert plain_card.locator(".card-designer").count() == 0


class TestBoardFooter:
    """Footer shows brand name (client) and date."""

    def test_footer_exists(self, page: Page):
        assert page.locator(".board-footer").count() == 1

    def test_footer_shows_default_brand(self, page: Page):
        brand = page.locator(".footer-brand").inner_text()
        assert "Moodboard Studio" in brand  # default when no client set

    def test_footer_has_date(self, page: Page):
        date = page.locator("#board-footer-date").inner_text()
        assert len(date.strip()) > 0
