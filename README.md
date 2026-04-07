# Moodboard Studio

Create print-ready furniture moodboards from a simple spreadsheet export. Upload a JSON file, customise the layout and style, then export to PDF or PNG — all in the browser, nothing to install.

**Open the app:** [lucaregnicoli.github.io/moodboard-studio](https://lucaregnicoli.github.io/moodboard-studio)

---

## How it works

1. Prepare a JSON file with your product selection (see format below)
2. Drag it onto the upload zone — the board populates instantly
3. Customise the title, client name, layout, colours, and fonts from the sidebar
4. Filter by category or tier to show only what you need
5. **Click product cards** to select which ones to include in the export — a ✓ badge marks each selected card
6. Export as **PDF** (A4, multi-page) or **PNG** — only the selected products are included

Your data never leaves your browser.

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
| `dimensions` | | Dimensions (e.g. `W 220 × D 95 × H 75 cm`). |
| `materials` | | Primary materials (e.g. `Solid oak, linen upholstery`). |
| `finishes` | | Available finishes or colour options (e.g. `Natural, Smoked, Lacquered white`). |
| `notes` | | Free-text notes — lead times, pricing, custom options, etc. |

### Tips

- **Image URLs** — use direct image addresses, not product page URLs. Right-click a product image and choose "Copy image address".
- **Images in exports** — some product websites block their images from being copied to other pages. Those images will appear in the app but may be blank in the exported PDF or PNG. If that happens, try downloading the image and hosting it yourself, or leave the field empty to show a placeholder.
- **Category names** — keep them consistent across products; they drive the section headings and filters.
- **Order** — products appear in the order listed in the file, within each category.
- **Export selection** — use **Select visible** to quickly select everything currently shown (respects active category and tier filters), or **Clear all** to start fresh. Products are de-selected by default when a file is loaded.

---

*Built for Katia — Part 1 Architectural Assistant.*
