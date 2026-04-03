# Moodboard Studio

Client-side furniture moodboard generator for interior architects. Upload a JSON file to render a print-ready moodboard grouped by category and tier, with PDF and PNG export. No backend, no dependencies, no installation.

**Live site:** [lucaregnicoli.github.io/moodboard-studio](https://lucaregnicoli.github.io/moodboard-studio)

---

## What it does

- Upload a JSON file containing your furniture selection
- The app renders a styled moodboard grouped by category and tier level
- Customise the board title, subtitle, client name, and date from the sidebar
- Filter visible categories and tiers with checkboxes
- Switch between three layout modes: 2-column, 3-column, or editorial
- Upload an optional header image as a full-width banner
- Export the finished board as PDF (A4 landscape) or PNG

Everything runs in the browser. No data leaves your machine.

---

## JSON format

The app expects a JSON array. Each object represents one product:

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

| Field | Type | Description |
|---|---|---|
| `category` | string | Product category, used for grouping and filtering (e.g. Sofas, Chairs, Lighting) |
| `tier` | string | Budget tier (e.g. High-end, Mid-range, Budget) |
| `name` | string | Product name, displayed in the card |
| `url` | string | Product page URL, linked from the card |
| `image_url` | string | Direct URL to the product image |

All fields are required. Images are loaded directly from `image_url` — use direct image URLs, not product page URLs.

---

## Usage

1. Open the site
2. Click **Upload JSON** in the sidebar and select your furniture file
3. Edit the board title, client name, and date as needed
4. Use the layout picker and category/tier filters to refine the view
5. Optionally upload a header image
6. Click **Export PDF** or **Export PNG** to download

---

## Hosting

The site is a single file (`moodboard.html`) hosted on GitHub Pages. To deploy your own copy:

1. Fork this repository
2. Go to **Settings > Pages**
3. Set source to the `main` branch
4. Your site will be available at `https://<your-username>.github.io/moodboard-studio`

To update the app, replace `moodboard.html` via the GitHub web interface or by pushing a commit. GitHub Pages redeploys automatically within ~30 seconds.

---

## Technical notes

- No build step, no bundler, no framework
- Images loaded with `crossOrigin="anonymous"` to support canvas-based export
- PDF export via [jsPDF](https://github.com/parallax/jsPDF) (loaded from cdnjs)
- PNG export via [html2canvas](https://html2canvas.hertzen.com) (loaded from cdnjs)
- All other logic is vanilla JS

---

*Built for [Katia](https://github.com/LucaRegnicoli) — interior architect.*
