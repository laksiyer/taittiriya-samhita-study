# Script selector update

This update adds a Sanskrit-only script selector to every reading page.

Available choices:
- Devanagari
- IAST
- ITRANS
- Grantha
- Telugu
- Kannada
- Malayalam

## Design

The Markdown source remains canonical Devanagari.

When `build-site.bat` runs, Aksharamukha pre-generates alternate display forms. The live GitHub Pages site therefore does not need to contact Aksharamukha or any external transliteration service.

The selected script is remembered in the reader's browser.

Only Sanskrit source material changes:
- Saṃhitā
- Sāyaṇa
- Sanskrit passage headings

These do not change:
- Mūla Translation
- Sāyaṇa Translation / Explanation
- English study notes
- English interface labels

## Install

Copy these files into the root of the repository, replacing existing files when asked:

- build.py
- build-site.bat
- requirements.txt

Then double-click `build-site.bat`.

On the first run only, it will install Aksharamukha automatically. After the site opens, choose a script from the toolbar.

Then commit:
- build.py
- build-site.bat
- requirements.txt
- regenerated docs/

and push with GitHub Desktop.

## Vedic accents

The underlying Devanagari source remains unchanged. Aksharamukha performs the script conversion during the build. Vedic accent rendering can vary somewhat by target script and installed browser font, so representative accented passages should be visually checked in each script before treating every display as typographically final.
