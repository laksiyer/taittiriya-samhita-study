SANDHYAVANDANAM PUBLISHING PATCH

1. Back up your existing build.py.
2. Copy build.py into the repository root, replacing the old build.py.
3. Leave your existing build-site.bat and requirements.txt unchanged.
4. Make sure sandhyavandanam/index.html exists in the repository root's sandhyavandanam folder.
5. Run build-site.bat. The homepage should now link to Sandhyavandanam.
6. Check docs/sandhyavandanam/index.html; commit and push the changed build.py, docs/index.html, and docs/sandhyavandanam/index.html via GitHub Desktop.

This patch only copies the existing sandhyavandanam/index.html website prototype; it does not convert all Obsidian Markdown notes into website pages. It does not publish arbitrary files from the sandhyavandanam folder.

CAUTION: Generated docs/ content is recreated on each build. Do not store hand-edited pages exclusively inside docs/.
