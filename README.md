# Moodboard Studio

Client-side furniture moodboard generator for interior architects. Upload a JSON file to render a print-ready moodboard grouped by category, with PDF and PNG export. No backend, no dependencies, no installation.

**Live site:** [lucaregnicoli.github.io/moodboard-studio](https://lucaregnicoli.github.io/moodboard-studio)

---

## What it does

- Upload a JSON file containing your furniture selection
- The app renders a styled moodboard grouped by category
- Customise the board title, subtitle, client name, and date from the sidebar
- Filter visible categories and tiers with checkboxes
- Switch between three layout modes: 2-column, 3-column, or editorial
- Choose from four colour themes (Linen, Slate, Chalk, Noir) and three font pairings
- Upload an optional header image as a full-width banner
- Export the finished board as PDF (A4 landscape, multi-page) or PNG

Everything runs in the browser. No data leaves your machine.

---

## Sample file

`furnitures.json` is included in this repository and can be used immediately to try the app. It contains **100 products across 19 categories**:

Armchairs · Beds · Benches, Daybeds & Ottomans · Coffee Tables · Consoles · Desks · Dining Tables · Lighting · Mirrors · Outdoor · Shelving & Bookcases · Side Tables · Sideboards · Sofas · Stools · Swings · and more.

To use it: open the app, drag `furnitures.json` onto the upload zone (or click "browse file"), and the board will populate instantly.

---

## JSON format

The app expects a JSON array where each object represents one product.

```json
[
  {
    "category": "Sofas",
    "tier": "High-end",
    "name": "Tufty-Time Sofa",
    "url": "https://www.bebitalia.com/en/tufty-time",
    "image_url": "https://www.bebitalia.com/media/tufty-time.jpg"
  },
  {
    "category": "Coffee Tables",
    "tier": "Mid-range",
    "name": "Slab Table",
    "url": "https://www.example.com/slab-table",
    "image_url": "https://www.example.com/slab-table.jpg"
  }
]
```

| Field | Type | Required | Description |
|---|---|---|---|
| `category` | string | yes | Groups products into sections on the board. All products sharing the same category appear together under a heading. Case-sensitive — `"Sofas"` and `"SOFAS"` are treated as separate categories. |
| `tier` | string | no | Optional budget or quality tier (e.g. `High-end`, `Mid-range`, `Budget`). Displayed as a small label on the card and available as a filter. Leave as `""` if not applicable. |
| `name` | string | yes | Product name displayed on the card, in serif type. |
| `url` | string | yes | Product page URL. Shown as a "View product →" link on the card, opens in a new tab. |
| `image_url` | string | yes | Direct URL to the product image (not the product page). Must point to the image file itself (`.jpg`, `.webp`, `.png`, etc). If the URL is empty or the image fails to load, a placeholder is shown automatically. |

### Tips for good results

- **Images**: use direct image URLs, not product page URLs. Right-click an image on a product page and choose "Copy image address" to get the direct URL.
- **CORS**: images hosted on servers that don't allow cross-origin requests will load in the browser but may appear blank in exported PNG/PDF files. This is a server-side restriction outside the app's control.
- **Categories**: keep category names consistent across products — they drive the grouping headings on the board.
- **Order**: products appear in the order they appear in the JSON file, within each category.

---

## Usage

1. Open the site (or `index.html` directly in a browser)
2. Drag your JSON file onto the upload zone, or click "browse file"
3. Edit the board title, subtitle, client name, and date in the sidebar
4. Select a layout (2-column, 3-column, or editorial)
5. Pick a colour theme and font pairing
6. Use the category and tier filters to show or hide specific groups
7. Optionally upload a header image (displayed as a full-width banner)
8. Click **Export PDF** or **Export PNG** to download

---

## Technical notes

- Single HTML file — no build step, no bundler, no framework
- Images loaded with `crossOrigin="anonymous"` to support canvas-based export
- PDF export via [jsPDF](https://github.com/parallax/jsPDF) — multi-page A4 landscape
- PNG export via [html2canvas](https://html2canvas.hertzen.com) — rendered at 3× resolution
- Both libraries loaded from cdnjs; all other logic is vanilla JS

---

*Built for Katia — Part 1 Architectural Assistant. :-)*
