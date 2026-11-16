from pathlib import Path
import html
import shutil
import sys

try:
    from aksharamukha import transliterate
except ImportError:
    print()
    print("Aksharamukha is required for the Sanskrit script selector.")
    print("Run build-site.bat again with an internet connection.")
    print("The batch file will install it automatically.")
    print()
    raise

ROOT = Path(__file__).parent
TS = ROOT / "TS"
DOCS = ROOT / "docs"

SCRIPT_TARGETS = [
    ("Devanagari", "Devanagari"),
    ("IAST", "IAST"),
    ("ITRANS", "ITRANS"),
    ("Grantha", "Grantha"),
    ("Telugu", "Telugu"),
    ("Kannada", "Kannada"),
    ("Malayalam", "Malayalam"),
]

def frontmatter(text):
    meta = {}
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            for line in text[4:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
            body = text[end+5:]
    return meta, body

def parse_sections(body):
    sections = []
    current = None
    field = None
    note = None
    buf = []

    def flush():
        nonlocal buf, note
        txt = "\n".join(buf).strip()
        if txt:
            if note is not None:
                note["text"] = txt
            elif current is not None and field and field != "notes":
                current[field] = txt
        buf = []

    mapping = {
        "saṃhitā": "samhita",
        "samhita": "samhita",
        "mūla translation": "mula_translation",
        "mula translation": "mula_translation",
        "sāyaṇa": "sayana",
        "sayana": "sayana",
        "sāyaṇa translation": "sayana_translation",
        "sayana translation": "sayana_translation",
        "notes": "notes",
    }

    for raw in body.splitlines():
        line = raw.rstrip()

        if line.startswith("## ") and not line.startswith("### "):
            flush()
            if note is not None and current is not None:
                current["notes"].append(note)
                note = None
            if current is not None:
                sections.append(current)
            current = {"heading": line[3:].strip(), "notes": []}
            field = None
            continue

        if line.startswith("### "):
            flush()
            if note is not None and current is not None:
                current["notes"].append(note)
                note = None
            label = line[4:].strip().lower()
            field = mapping.get(label, label.replace(" ", "_"))
            continue

        if line.startswith("#### ") and current is not None and field == "notes":
            flush()
            if note is not None:
                current["notes"].append(note)
            label = line[5:].strip()
            if ":" in label:
                typ, title = label.split(":", 1)
                note = {"type": typ.strip(), "title": title.strip(), "text": ""}
            else:
                note = {"type": label, "title": "", "text": ""}
            continue

        if line.startswith("# ") and not line.startswith("## "):
            continue

        buf.append(line)

    flush()
    if note is not None and current is not None:
        current["notes"].append(note)
    if current is not None:
        sections.append(current)
    return sections

def esc(s):
    return html.escape(s or "")

def plain_div_block(text, cls=""):
    if not text:
        return ""
    txt = esc(text).replace("\n\n", "</p><p>").replace("\n", "<br>")
    return '<div class="' + cls + '"><p>' + txt + '</p></div>'

def transliterate_text(text, target):
    if target == "Devanagari":
        return text
    return transliterate.process("Devanagari", target, text)

def script_variants(text, cls="sanskrit"):
    """Render only Sanskrit source text as switchable script variants."""
    if not text:
        return ""
    blocks = []
    for key, target in SCRIPT_TARGETS:
        converted = transliterate_text(text, target)
        rendered = esc(converted).replace("\n\n", "</p><p>").replace("\n", "<br>")
        hidden = "" if key == "Devanagari" else " hidden"
        blocks.append(
            '<div class="script-variant script-' + key.lower() + '" '
            'data-script="' + esc(key) + '"' + hidden + '><p>' + rendered + '</p></div>'
        )
    return '<div class="' + cls + ' script-switch">' + "".join(blocks) + '</div>'

def contains_devanagari(text):
    return any("\u0900" <= ch <= "\u097f" or "\ua8e0" <= ch <= "\ua8ff" for ch in (text or ""))

def script_heading(text):
    """Switch headings only when they actually contain Devanagari/Sanskrit."""
    if not text:
        return ""
    if not contains_devanagari(text):
        return esc(text)
    spans = []
    for key, target in SCRIPT_TARGETS:
        converted = transliterate_text(text, target)
        hidden = "" if key == "Devanagari" else " hidden"
        spans.append(
            '<span class="script-variant" data-script="' + esc(key) + '"' + hidden + '>'
            + esc(converted) + '</span>'
        )
    return '<span class="script-switch script-heading">' + "".join(spans) + '</span>'

def details(title, body, cls=""):
    if not body:
        return ""
    return '<details class="' + cls + '"><summary>' + esc(title) + '</summary><div class="details-body">' + body + '</div></details>'

def page_html(item, prev_item, next_item):
    m = item["meta"]
    title = m.get("title", "TS")
    subtitle = m.get("subtitle", "")
    parts = []

    for sec in item["sections"]:
        notes = []
        for n in sec.get("notes", []):
            label = n.get("type", "Note")
            if n.get("title"):
                label += ": " + n["title"]
            # Notes deliberately remain exactly as written.
            notes.append(details(label, plain_div_block(n.get("text", "")), "study-note"))

        parts.append(
            '<article class="passage">'
            '<h2 class="passage-title">' + script_heading(sec.get("heading","")) + '</h2>'
            '<span class="label">Saṃhitā</span>'
            + script_variants(sec.get("samhita",""), "sanskrit")
            + details("Mūla translation", plain_div_block(sec.get("mula_translation","")), "translation")
            + '<div class="sayana"><span class="label">Sāyaṇa</span>'
            + script_variants(sec.get("sayana",""), "sanskrit") + '</div>'
            + details("Sāyaṇa translation / explanation", plain_div_block(sec.get("sayana_translation","")), "translation")
            + "".join(notes)
            + '</article>'
        )

    def href(x):
        if x is None:
            return "#"
        mm = x["meta"]
        return '../../../ts/%02d/%02d/%02d.html' % (int(mm["kanda"]), int(mm["prapathaka"]), int(mm["anuvaka"]))

    prev_html = '<a href="' + href(prev_item) + '">&larr; Previous</a>' if prev_item else '<span></span>'
    next_html = '<a href="' + href(next_item) + '">Next &rarr;</a>' if next_item else '<span></span>'

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="../../../assets/style.css">
</head>
<body>
<header class="reader-header">
<a class="home-link" href="../../../index.html">&larr; Contents</a>
<h1>__TITLE__</h1>
<p class="subtitle">__SUBTITLE__</p>
</header>
<nav class="toolbar">
<label class="script-control">Script:
<select id="scriptSelector" onchange="setScript(this.value)">
<option value="Devanagari">Devanagari</option>
<option value="IAST">IAST</option>
<option value="ITRANS">ITRANS</option>
<option value="Grantha">Grantha</option>
<option value="Telugu">Telugu</option>
<option value="Kannada">Kannada</option>
<option value="Malayalam">Malayalam</option>
</select>
</label>
<span class="toolbar-divider"></span>
<button onclick="setOpen('details.translation',true)">Show all translations</button>
<button onclick="setOpen('details.translation',false)">Hide all translations</button>
<button onclick="setOpen('details.study-note',true)">Show all notes</button>
<button onclick="setOpen('details.study-note',false)">Hide all notes</button>
</nav>
<main class="reader">__BODY__</main>
<nav class="page-nav">__PREV__<a href="../../../index.html">Contents</a>__NEXT__</nav>
<script>
const SCRIPT_KEY='ts-study-script';

function setOpen(selector,value){
  document.querySelectorAll(selector).forEach(d=>d.open=value);
}

function setScript(script){
  const allowed=['Devanagari','IAST','ITRANS','Grantha','Telugu','Kannada','Malayalam'];
  if(!allowed.includes(script)) script='Devanagari';

  document.querySelectorAll('.script-variant').forEach(el=>{
    el.hidden = el.dataset.script !== script;
  });

  document.documentElement.dataset.script=script;
  const selector=document.getElementById('scriptSelector');
  if(selector) selector.value=script;
  try { localStorage.setItem(SCRIPT_KEY,script); } catch(e) {}
}

(function(){
  let chosen='Devanagari';
  try { chosen=localStorage.getItem(SCRIPT_KEY)||'Devanagari'; } catch(e) {}
  setScript(chosen);
})();
</script>
</body>
</html>""".replace("__TITLE__", esc(title)).replace("__SUBTITLE__", esc(subtitle)).replace("__BODY__", "".join(parts)).replace("__PREV__", prev_html).replace("__NEXT__", next_html)

def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "assets").mkdir(parents=True)

    items = []
    for path in TS.rglob("*.md"):
        meta, body = frontmatter(path.read_text(encoding="utf-8"))
        if all(x in meta for x in ("kanda","prapathaka","anuvaka")):
            items.append({"meta": meta, "sections": parse_sections(body)})

    items.sort(key=lambda x: (int(x["meta"]["kanda"]), int(x["meta"]["prapathaka"]), int(x["meta"]["anuvaka"])))

    for i, item in enumerate(items):
        m = item["meta"]
        dest = DOCS / "ts" / ("%02d" % int(m["kanda"])) / ("%02d" % int(m["prapathaka"])) / ("%02d.html" % int(m["anuvaka"]))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page_html(item, items[i-1] if i else None, items[i+1] if i+1 < len(items) else None), encoding="utf-8")

    groups = {}
    for item in items:
        m = item["meta"]
        k, p = int(m["kanda"]), int(m["prapathaka"])
        groups.setdefault(k, {}).setdefault(p, []).append(item)

    chunks = ['<section class="intro"><h2>Study Index</h2><p>Saṃhitā and Sāyaṇa stay visible. Translations and notes open when requested. Sanskrit script can be changed on any reading page.</p></section>']
    for k in sorted(groups):
        chunks.append('<section class="index-kanda"><h2>Kāṇḍa %d</h2>' % k)
        for p in sorted(groups[k]):
            chunks.append('<h3>Prapāṭhaka %d.%d</h3><div class="anuvaka-grid">' % (k,p))
            for item in groups[k][p]:
                m = item["meta"]
                a = int(m["anuvaka"])
                chunks.append(
                    '<a class="anuvaka-card" href="ts/%02d/%02d/%02d.html"><strong>%d.%d.%d</strong><span>Anuvāka %d</span><small>%s</small></a>'
                    % (k,p,a,k,p,a,a,esc(m.get("status","")))
                )
            chunks.append('</div>')
        chunks.append('</section>')

    index = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Taittirīya Saṃhitā Study</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site-header">
<h1>Taittirīya Saṃhitā Study</h1>
<p class="subtitle">Saṃhitā | Sāyaṇa | Translation | Personal Study Notes</p>
</header>
<main class="home">__INDEX__</main>
</body>
</html>""".replace("__INDEX__", "".join(chunks))
    (DOCS / "index.html").write_text(index, encoding="utf-8")

    css = """
:root { --bg:#fbfaf6; --paper:#fff; --text:#25221d; --muted:#6d675e; --line:#ddd6ca; --accent:#6b3f25; --soft:#f3eee5; --note:#f8f5ed; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font-family:Georgia,"Noto Serif",serif; line-height:1.65; }
.site-header,.reader-header { padding:1.4rem max(1rem,calc((100% - 980px)/2)); border-bottom:1px solid var(--line); background:var(--paper); }
.site-header h1,.reader-header h1 { margin:0; font-size:1.65rem; }
.subtitle { color:var(--muted); margin:.25rem 0 0; }
.home,.reader { max-width:980px; margin:0 auto; padding:2rem 1rem 4rem; }
.intro { margin-bottom:2rem; }
.index-kanda { margin:2rem 0 3rem; }
.anuvaka-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.8rem; margin-bottom:1.5rem; }
.anuvaka-card { display:flex; flex-direction:column; padding:1rem; border:1px solid var(--line); border-radius:8px; background:var(--paper); color:var(--text); text-decoration:none; }
.anuvaka-card:hover { border-color:var(--accent); }
.anuvaka-card small { color:var(--muted); margin-top:.3rem; }
.toolbar { position:sticky; top:0; z-index:10; display:flex; flex-wrap:wrap; align-items:center; gap:.5rem; padding:.7rem max(1rem,calc((100% - 980px)/2)); border-bottom:1px solid var(--line); background:rgba(251,250,246,.96); }
button,select { border:1px solid var(--line); background:var(--paper); padding:.45rem .7rem; border-radius:5px; cursor:pointer; font:inherit; }
button:hover,select:hover { border-color:var(--accent); }
.script-control { display:flex; align-items:center; gap:.45rem; font-size:.88rem; font-weight:600; color:var(--muted); }
.toolbar-divider { width:1px; height:1.7rem; background:var(--line); margin:0 .15rem; }
.passage { background:var(--paper); border:1px solid var(--line); border-radius:10px; padding:1.25rem 1.35rem; margin:0 0 1.2rem; }
.passage-title { margin:0 0 .8rem; font-size:1.05rem; color:var(--accent); }
.label { display:inline-block; font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin-bottom:.3rem; }
.sanskrit { font-family:"Noto Serif Devanagari","Noto Serif Grantha","Noto Serif Telugu","Noto Serif Kannada","Noto Serif Malayalam","Nirmala UI","Mangal",serif; font-size:1.27rem; line-height:1.9; margin:.2rem 0 1rem; }
.script-variant[hidden] { display:none !important; }
html[data-script="IAST"] .sanskrit,
html[data-script="ITRANS"] .sanskrit { font-family:Georgia,"Noto Serif",serif; line-height:1.75; }
html[data-script="Grantha"] .sanskrit { font-family:"Noto Serif Grantha","Noto Sans Grantha",serif; }
html[data-script="Telugu"] .sanskrit { font-family:"Noto Serif Telugu","Noto Sans Telugu","Nirmala UI",serif; }
html[data-script="Kannada"] .sanskrit { font-family:"Noto Serif Kannada","Noto Sans Kannada","Nirmala UI",serif; }
html[data-script="Malayalam"] .sanskrit { font-family:"Noto Serif Malayalam","Noto Sans Malayalam","Nirmala UI",serif; }
.sayana { padding-top:.85rem; border-top:1px solid var(--line); }
.sayana .sanskrit { font-size:1.12rem; }
details { margin-top:.75rem; border:1px solid var(--line); border-radius:7px; overflow:hidden; }
summary { cursor:pointer; padding:.65rem .8rem; font-weight:600; background:var(--soft); }
.details-body { padding:.8rem 1rem; }
.study-note summary { background:var(--note); }
.home-link,.page-nav a { color:var(--accent); text-decoration:none; }
.home-link { display:inline-block; margin-bottom:.6rem; }
.page-nav { max-width:980px; margin:0 auto 3rem; padding:0 1rem; display:flex; justify-content:space-between; }
@media (max-width:620px) {
  .sanskrit { font-size:1.16rem; }
  .toolbar button,.script-control,select { font-size:.8rem; }
  .toolbar-divider { display:none; }
}
"""
    (DOCS / "assets" / "style.css").write_text(css.strip(), encoding="utf-8")
    print("Built", len(items), "anuvāka pages.")
    print("Script selector: Devanagari, IAST, ITRANS, Grantha, Telugu, Kannada, Malayalam.")
    print("Open:", DOCS / "index.html")

if __name__ == "__main__":
    main()
