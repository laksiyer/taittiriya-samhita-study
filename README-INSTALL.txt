# Śrauta Rituals integration into the existing TS + TB site

Use this package in your EXISTING repository:
F:\github\taittiriya-samhita-vault\taittiriya-samhita-study

1. Before changing anything, copy your existing `build.py` somewhere safe OUTSIDE the repository (for example `F:\backup\build-before-srauta.py`).
2. Unzip this download somewhere temporary (Downloads is fine).
3. Copy the package's **build.py** into the repository ROOT above, replacing the current `build.py`. This build.py is based on the one you uploaded and preserves the TS/TB generation and script selector.
4. Copy the package's **srauta** folder into the same repository root (beside `TS`, `tb`, and `docs`). Do NOT put `srauta` inside `docs` manually.
5. Leave `build-site.bat` and `publish.bat` alone. Double-click your existing `build-site.bat` once. It will regenerate `docs/` including `docs/ts`, `docs/tb` and `docs/srauta`.
6. Open `docs/index.html` locally. It should show a new `श्रौतप्रयोगाः` section and a link to the Sākamedha Āprī lesson. Also check that older TS and TB pages still work.
7. In GitHub Desktop inspect all changes and ensure only expected sources, generated site files and build.py are present. Commit/push only when satisfied.

IMPORTANT: Your teacher's original PDF stays in a private folder **outside this Git repository**. Do not copy it into `srauta`, `docs`, `sources`, or any other repository folder. The builder copies only HTML/JSON/CSS/JS from srauta, but that whitelist does not make keeping the PDF in a public repository safe.

Why this is necessary: Your original build.py deletes and rebuilds docs/ on every run. Placing only the output files into docs/srauta would not survive rebuilding. This patch keeps the Srauta source separately and includes it at build time.

No need to change build-site.bat. The content is still publicly accessible to someone with the URL after a push; noindex is only a request to search engines.
