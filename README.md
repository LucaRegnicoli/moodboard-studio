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

The file must be a JSON array where each object is one product. Only `category`, `name`, `url`, and `image_url` are required — all other fields are optional and can be omitted or left as `""`.

```json
[
  {
    "category":   "Sofas",
    "tier":       "High-end",
    "name":       "Tufty-Time Sofa · B&B Italia",
    "url":        "https://www.bebitalia.com/en/tufty-time",
    "image_url":  "https://www.bebitalia.com/media/tufty-time.jpg",
    "dimensions": "W 220 × D 95 × H 75 cm",
    "materials":  "Solid oak frame, linen upholstery",
    "finishes":   "Natural, Smoked, Lacquered white",
    "notes":      "12 week lead time. Custom configurations available."
  },
  {
    "category":   "Coffee Tables",
    "tier":       "",
    "name":       "Slab Table",
    "url":        "https://www.example.com/slab-table",
    "image_url":  "https://www.example.com/slab-table.jpg",
    "dimensions": "",
    "materials":  "",
    "finishes":   "",
    "notes":      ""
  }
]
```

### Fields

| Field | Required | Description |
|---|:---:|---|
| `category` | ✓ | Groups products into sections. Case-sensitive — `"Sofas"` and `"SOFAS"` are separate groups. |
| `name` | ✓ | Product name. To add a designer credit, use `"Name · Designer"` — the part after ` · ` renders as a smaller secondary line. |
| `url` | ✓ | Product page URL, shown as a "View product →" link on the card. |
| `image_url` | ✓ | Direct URL to the image file (`.jpg`, `.webp`, `.png`). Empty or broken URLs show a placeholder automatically. |
| `tier` | | Budget or quality label (e.g. `High-end`, `Mid-range`, `Budget`). Shown on the card and available as a sidebar filter. |
| `dimensions` | | Dimensions string (e.g. `W 220 × D 95 × H 75 cm`). |
| `materials` | | Primary materials (e.g. `Solid oak, linen upholstery`). |
| `finishes` | | Available finishes or colour options (e.g. `Natural, Smoked, Lacquered white`). |
| `notes` | | Free-text notes — lead times, pricing, custom options, etc. |

### Tips

- **Image URLs** — use direct image addresses, not product page URLs. Right-click a product image and choose "Copy image address".
- **CORS** — some image servers block cross-origin requests. Images will display in the browser but may be blank in exported files. This is a server-side restriction the app cannot work around.
- **Category names** — keep them consistent across products; they drive the section headings and filters.
- **Order** — products appear in the order listed in the file, within each category.

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
