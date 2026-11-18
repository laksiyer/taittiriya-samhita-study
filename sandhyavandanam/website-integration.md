# Website integration

This package is intended to be unzipped into the existing `taittiriya-samhita-study` repository, yielding:

```text
taittiriya-samhita-study/
├── index.html                   # existing TS homepage (not included)
├── ts/                          # existing TS content (not included)
└── sandhyavandanam/
    ├── index.html               # current standalone prototype
    ├── README.md
    ├── 00-Start-Here.md
    ├── study/
    ├── procedures/
    └── templates/
```

The Markdown files are the **editable Obsidian source**. The current `index.html` is a self-contained research portal mock-up and does not ingest Markdown automatically. **Editing a Markdown note will not update the HTML page yet.** This integration should be implemented when the existing TS website's build and script-selector code can be inspected without guesswork.

Proposed navigation: add one top-level `Sandhyāvandanam` link in the existing TS site (not modified by this ZIP). Proposed URL after publishing: `https://laksiyer.github.io/taittiriya-samhita-study/sandhyavandanam/`.

Eventually share the TS script selector (Devanāgarī, IAST, ITRANS, Grantha, Telugu, Kannada, Malayalam), transliterating Sanskrit only and leaving English untouched. Retain Markdown notes and real rendered page content, including nested headings and study notes.

## Suggested Git workflow

After extraction into the repository, inspect the added folder in Obsidian, then add/commit/push with your normal Git client. This archive neither alters the existing files nor publishes changes itself.
