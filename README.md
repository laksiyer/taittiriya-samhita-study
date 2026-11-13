# Taittirīya Saṃhitā Study Vault

This folder is both an Obsidian vault and the source for a GitHub Pages site.

## Everyday workflow

1. Open this folder as a vault in Obsidian.
2. Edit or add anuvāka Markdown files under `TS/`.
3. Double-click `build-site.bat`.
4. Review the generated site in `docs/index.html`.
5. Commit and push when ready.

## Add a new anuvāka

Copy `NEW-ANUVAKA-TEMPLATE.md` to `TS/KK/PP/AA.md`.

Example for TS 1.6.11:

`TS/01/06/11.md`

Then change the metadata at the top.

## GitHub Pages

The public site is generated into `docs/`.

After pushing to GitHub:

1. Repository Settings
2. Pages
3. Deploy from a branch
4. Branch: `main`
5. Folder: `/docs`
6. Save

## Notes

Under `### Notes`, use headings such as:

`#### Pāṇini: दाशुषे`

`#### Grammar: क्वसु`

`#### Ritual: Āśrāvaṇa`

`#### Mīmāṃsā: Codaka`

`#### Cross-reference: TS 1.6.11`

`#### Personal: Question from class`

No HTML or JSON editing is required.
