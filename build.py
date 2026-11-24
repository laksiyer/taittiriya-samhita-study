from pathlib import Path
import html
import shutil
import sys
import re
import posixpath
from html.parser import HTMLParser

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
TB = ROOT / "tb"
DOCS = ROOT / "docs"
SRAUTA = ROOT / "srauta"
SANDHYA = ROOT / "sandhyavandanam"

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
        collection = "tb" if "ashtaka" in mm else "ts"
        first_number = mm["ashtaka"] if collection == "tb" else mm["kanda"]
        return '../../../%s/%02d/%02d/%02d.html' % (
            collection, int(first_number), int(mm["prapathaka"]), int(mm["anuvaka"])
        )

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



def parse_tb_sections(body):
    """TB starter-format Markdown: ## units, ### interleaved textual layers."""
    fields = {
        "mūla (accented, excerpt verified against independent digital source; tb 1.1.1.1)": "samhita",
        "mūla": "samhita", "mūla (accented)": "samhita", "brāhmaṇa mūla": "samhita",
        "saṃhitā": "samhita", "samhita": "samhita",
        "english translation of the mūla": "mula_translation",
        "mūla translation": "mula_translation", "mula translation": "mula_translation",
        "sāyaṇa's bhāṣya": "sayana", "sāyaṇa": "sayana", "sayana": "sayana",
        "english translation of sāyaṇa (first portion, draft)": "sayana_translation",
        "english translation of sāyaṇa": "sayana_translation",
        "sāyaṇa translation": "sayana_translation",
        "sources and textual-status notes": "notes",
    }
    sections = []
    curr = None
    field = None
    buff = []
    def flush():
        nonlocal buff
        content = "\n".join(buff).strip()
        if content and curr is not None:
            if field == "notes":
                curr["notes"].append({"type": "Editorial", "title": "Sources and status", "text": content})
            elif field:
                curr[field] = (curr.get(field, "") + "\n" + content).strip()
            else:
                curr["mula_translation"] = (curr.get("mula_translation", "") + "\n" + content).strip()
        buff = []
    for raw in body.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            flush()
            if curr:
                sections.append(curr)
            curr = {"heading": line[3:].strip(), "notes": []}
            field = None
        elif line.startswith("### "):
            flush()
            lbl = line[4:].strip().lower()
            field = fields.get(lbl)
            if field is None:
                if lbl.startswith("mūla ("):
                    field = "samhita"
                elif lbl.startswith("english translation of sāyaṇa"):
                    field = "sayana_translation"
                else:
                    field = "notes"
        elif line.startswith("# "):
            continue
        else:
            buff.append(line)
    flush()
    if curr:
        sections.append(curr)
    return sections


def tb_page_html(item, prev_item, next_item):
    # Reuse the already proven Saṃhitā reader, transliteration and styling.
    markup = page_html(item, prev_item, next_item)
    markup = markup.replace('<span class="label">Saṃhitā</span>', '<span class="label">Brāhmaṇa mūla</span>')
    # No Sanskrit mūla should be inferred from Sāyaṇa's OCR transcription.
    return markup


def tb_index_chunks(items):
    blocks = ['<section class="intro" id="brahmana"><h2>Taittirīya Brāhmaṇa</h2><p>Accented mūla is kept distinct from the Sāyaṇa transcription. Draft and incomplete passages are marked in their source files.</p></section>']
    groups = {}
    for item in items:
        m = item["meta"]
        groups.setdefault(int(m["ashtaka"]), {}).setdefault(int(m["prapathaka"]), []).append(item)
    for k in sorted(groups):
        blocks.append('<section class="index-kanda"><h2>Aṣṭaka %d</h2>' % k)
        for p in sorted(groups[k]):
            blocks.append('<h3>Prapāṭhaka %d.%d</h3><div class="anuvaka-grid">' % (k, p))
            for item in groups[k][p]:
                m=item["meta"]
                a=int(m["anuvaka"])
                blocks.append('<a class="anuvaka-card" href="tb/%02d/%02d/%02d.html"><strong>TB %d.%d.%d</strong><span>Anuvāka %d</span><small>%s</small></a>' % (k,p,a,k,p,a,a,esc(m.get("status",""))))
            blocks.append('</div>')
        blocks.append('</section>')
    return blocks

# Sandhyavandanam Markdown-to-HTML publishing.
# This reader uses Python's standard library only; TS/TB rendering stays unchanged.
SANDHYA_FOLDERS = {"study", "sources", "procedures"}
SANDHYA_ROOT_NOTES = {"00-Start-Here.md", "01-Editorial-Principles.md",
    "02-Source-Register.md", "03-Tradition-Map.md", "04-Study-Roadmap.md"}


def sandhya_publishable_paths():
    if not SANDHYA.is_dir():
        return []
    paths = []
    for p in SANDHYA.rglob('*.md'):
        rel = p.relative_to(SANDHYA)
        if any(part.startswith('.') or part.startswith('_') for part in rel.parts):
            continue
        if rel.parts[0] in SANDHYA_FOLDERS or rel.name in SANDHYA_ROOT_NOTES and len(rel.parts) == 1:
            paths.append(p)
    return sorted(paths, key=lambda p: str(p.relative_to(SANDHYA)).casefold())


def sandhya_title(path):
    meta, body = frontmatter(path.read_text(encoding='utf-8-sig'))
    heading = re.search(r'^#\s+(.+)$', body, re.M)
    return meta.get('title') or (heading.group(1) if heading else path.stem.replace('-', ' '))


def sandhya_link(target, current, known_paths):
    '''Resolve Obsidian wiki targets relative to current note or by unique basename.'''
    raw = target.split('#', 1)[0].strip()
    anchor = ('#' + target.split('#', 1)[1]) if '#' in target else ''
    if not raw:
        return anchor or '#'
    raw = raw.replace('\\', '/')
    if not raw.endswith('.md'):
        raw += '.md'
    source_rel = current.relative_to(SANDHYA)
    candidate = posixpath.normpath(posixpath.join(source_rel.parent.as_posix(), raw))
    if candidate not in known_paths:
        root_candidate = posixpath.normpath(raw.lstrip('/'))
        if root_candidate in known_paths:
            candidate = root_candidate
        else:
            matching = [p for p in known_paths if p.endswith('/' + raw) or p == raw]
            if len(matching) == 1:
                candidate = matching[0]
            else:
                return None
    destination = posixpath.relpath(candidate[:-3] + '.html', source_rel.parent.as_posix())
    return destination + anchor


def sandhya_inline(text, current, known_paths):
    # Render escaped inline Markdown and Obsidian wiki links, no arbitrary raw HTML.
    tokens = []
    def wiki(match):
        raw, label = match.group(1), match.group(2)
        link = sandhya_link(raw, current, known_paths)
        display = label or raw.rsplit('/', 1)[-1].replace('.md', '')
        if link is None:
            return esc(display) + ' <small class="unresolved">[link unresolved]</small>'
        token = '__SANDHYALINK_%d__' % len(tokens)
        tokens.append('<a href="%s">%s</a>' % (esc(link), esc(display)))
        return token
    text = re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', wiki, text)
    def normal_link(m):
        name, href = m.group(1), m.group(2)
        if href.lower().startswith(('javascript:', 'data:')):
            return esc(name)
        if href.lower().endswith('.md') or '.md#' in href.lower():
            local = sandhya_link(href, current, known_paths)
            if local is None:
                return esc(name) + ' <small class="unresolved">[link unresolved]</small>'
            href = local
        token = '__SANDHYALINK_%d__' % len(tokens)
        tokens.append('<a href="%s">%s</a>' % (esc(href), esc(name)))
        return token
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', normal_link, text)
    out = esc(text)
    out = re.sub(r'`([^`]+)`', lambda m: '<code>' + m.group(1) + '</code>', out)
    out = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', out)
    out = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', out)
    for i, token in enumerate(tokens):
        out = out.replace('__SANDHYALINK_%d__' % i, token)
    return out


def sandhya_markdown_to_html(text, current, known_paths):
    '''Small predictable Markdown subset for our Obsidian study notes.'''
    lines = text.splitlines()
    out, para, entries = [], [], []
    mode, code_lines, list_tag = None, [], None
    def flush_para():
        if para:
            out.append('<p>' + '<br>'.join(sandhya_inline(x, current, known_paths) for x in para) + '</p>')
            para.clear()
    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append('</%s>' % list_tag)
            list_tag = None
    def flush_table():
        if not entries:
            return
        out.append('<div class="table-scroll"><table>')
        for i, cells in enumerate(entries):
            out.append('<tr>' + ''.join('<%s>%s</%s>' % ('th' if i == 0 else 'td', sandhya_inline(c, current, known_paths), 'th' if i == 0 else 'td') for c in cells) + '</tr>')
        out.append('</table></div>')
        entries.clear()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith('```'):
            flush_para(); close_list(); flush_table()
            if mode == 'code':
                out.append('<pre><code>' + esc('\n'.join(code_lines)) + '</code></pre>')
                mode, code_lines = None, []
            else:
                mode, code_lines = 'code', []
            i += 1; continue
        if mode == 'code':
            code_lines.append(line); i += 1; continue
        if line.startswith('|') and line.endswith('|') and line.count('|') >= 3:
            cells = [c.strip() for c in line.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                i += 1; continue
            flush_para(); close_list()
            entries.append(cells); i += 1; continue
        flush_table()
        # Whitelisted Obsidian disclosure syntax. Do not pass arbitrary HTML through.
        disclosure = re.fullmatch(r'<details><summary>(IAST \(source transcription\) · 41\.\d+\.\d+|Accented Śaunaka IAST · [^<>]{1,120})</summary>', line.strip())
        if disclosure:
            flush_para(); close_list()
            out.append('<details class="sandhya-iast"><summary>' + esc(disclosure.group(1)) + '</summary>')
            i += 1; continue
        if line.strip() == '</details>':
            flush_para(); close_list()
            out.append('</details>')
            i += 1; continue
        if not line.strip():
            flush_para(); close_list(); i += 1; continue
        heading = re.match(r'^(#{1,6})\s+(.*)$', line)
        if heading:
            flush_para(); close_list()
            n = len(heading.group(1))
            out.append('<h%d>%s</h%d>' % (n, sandhya_inline(heading.group(2), current, known_paths), n))
            i += 1; continue
        if line.startswith('> [!'):
            flush_para(); close_list()
            kind = re.match(r'> \[!([^\]]+)\]\s*(.*)', line)
            out.append('<div class="sandhya-callout"><strong>%s</strong> %s</div>' % (esc(kind.group(1)), sandhya_inline(kind.group(2), current, known_paths)))
            i += 1; continue
        if line.startswith('> '):
            flush_para(); close_list()
            out.append('<blockquote>' + sandhya_inline(line[2:], current, known_paths) + '</blockquote>')
            i += 1; continue
        ordered = re.match(r'^\s*\d+\.\s+(.*)', line)
        unordered = re.match(r'^\s*[-*+]\s+(.*)', line)
        if ordered or unordered:
            flush_para()
            desired = 'ol' if ordered else 'ul'
            if list_tag != desired:
                close_list(); out.append('<%s>' % desired); list_tag = desired
            out.append('<li>' + sandhya_inline((ordered or unordered).group(1), current, known_paths) + '</li>')
            i += 1; continue
        close_list()
        if line.strip() in {'---', '***'}:
            flush_para(); out.append('<hr>'); i += 1; continue
        para.append(line)
        i += 1
    flush_para(); close_list(); flush_table()
    if mode == 'code':
        out.append('<pre><code>' + esc('\n'.join(code_lines)) + '</code></pre>')
    return '\n'.join(out)


class _SandhyaScriptWrapper(HTMLParser):
    '''Convert Sanskrit text nodes only, leaving English and HTML tags untouched.'''
    sanskrit_run = re.compile(r'[\u0900-\u097f\u1cd0-\u1cff\ua8e0-\ua8ff]+(?:[\s\u0964\u0965\u200c\u200d\u0900-\u097f\u1cd0-\u1cff\ua8e0-\ua8ff]*[\u0900-\u097f\u1cd0-\u1cff\ua8e0-\ua8ff])?')
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.no_convert = 0
    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}: self.no_convert += 1
        self.parts.append('<' + tag + ''.join(' %s="%s"' % (k, esc(v or '')) for k, v in attrs) + '>')
    def handle_endtag(self, tag):
        self.parts.append('</' + tag + '>')
        if tag in {'script', 'style'}: self.no_convert = max(0, self.no_convert-1)
    def handle_startendtag(self, tag, attrs):
        self.parts.append('<' + tag + ''.join(' %s="%s"' % (k, esc(v or '')) for k, v in attrs) + '/>')
    def handle_entityref(self, name): self.parts.append('&' + name + ';')
    def handle_charref(self, name): self.parts.append('&#' + name + ';')
    def handle_data(self, data):
        if self.no_convert or not contains_devanagari(data):
            self.parts.append(data); return
        def sub(m):
            original = m.group(0)
            variants = []
            for name, target in SCRIPT_TARGETS:
                try:
                    converted = transliterate_text(original, target)
                except Exception:
                    converted = original
                variants.append('<span class="script-variant" data-script="%s"%s>%s</span>' % (
                    esc(name), '' if name == 'Devanagari' else ' hidden', esc(converted)))
            return '<span class="script-switch">' + ''.join(variants) + '</span>'
        self.parts.append(self.sanskrit_run.sub(sub, data))
    def get_html(self): return ''.join(self.parts)


def sandhya_article_html(path, known_paths):
    text = path.read_text(encoding='utf-8-sig')
    meta, body = frontmatter(text)
    title = sandhya_title(path)
    rendered = sandhya_markdown_to_html(body, path, known_paths)
    wrapper = _SandhyaScriptWrapper()
    wrapper.feed(rendered)
    rel = path.relative_to(SANDHYA)
    homepage = posixpath.relpath('index.html', rel.parent.as_posix())
    sitehome = posixpath.relpath('index.html', 'sandhyavandanam/' + rel.parent.as_posix())
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ | Sandhyāvandanam</title>
<link rel="stylesheet" href="__CSS__"></head><body>
<header class="reader-header"><a href="__HOME__">← Sandhyāvandanam</a> · <a href="__SITEHOME__">Vedic Study</a>
<h1>__TITLE__</h1><p class="subtitle">Obsidian source: __PATH__</p></header>
<nav class="toolbar"><label class="script-control">Script: <select id="scriptSelector" onchange="setScript(this.value)">
<option>Devanagari</option><option>IAST</option><option>ITRANS</option><option>Grantha</option><option>Telugu</option><option>Kannada</option><option>Malayalam</option>
</select></label></nav><main class="reader sandhya-reading">__BODY__</main>
<script>
function setScript(s){const allowed=['Devanagari','IAST','ITRANS','Grantha','Telugu','Kannada','Malayalam'];if(!allowed.includes(s))s='Devanagari';document.querySelectorAll('.script-variant').forEach(e=>e.hidden=e.dataset.script!==s);document.documentElement.dataset.script=s;document.getElementById('scriptSelector').value=s;try{localStorage.setItem('ts-study-script',s)}catch(e){}}
let selected='Devanagari';try{selected=localStorage.getItem('ts-study-script')||selected}catch(e){}setScript(selected);
</script></body></html>'''.replace('__TITLE__', esc(title)).replace('__CSS__', posixpath.relpath('assets/style.css','sandhyavandanam/'+rel.parent.as_posix())).replace('__HOME__', esc(homepage)).replace('__SITEHOME__', esc(sitehome)).replace('__PATH__', esc(rel.as_posix())).replace('__BODY__', wrapper.get_html())


def build_sandhya_pages():
    '''Publish vetted Markdown categories, never source PDFs or arbitrary files.'''
    paths = sandhya_publishable_paths()
    known = {p.relative_to(SANDHYA).as_posix() for p in paths}
    output = DOCS / 'sandhyavandanam'
    output.mkdir(parents=True, exist_ok=True)
    cards = []
    for p in paths:
        rel = p.relative_to(SANDHYA)
        dest = output / rel.with_suffix('.html')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(sandhya_article_html(p, known), encoding='utf-8')
        title = sandhya_title(p)
        cards.append('<li><a href="%s">%s</a> <small>%s</small></li>' % (esc(rel.with_suffix('.html').as_posix()), esc(title), esc(rel.parent.as_posix())))
    # Preserve the authored Sandhyāvandanam landing page, but replace broken .md
    # links to source files with actual built .html links.
    landing = SANDHYA / 'index.html'
    if landing.is_file():
        html_text = landing.read_text(encoding='utf-8-sig')
        def fix_href(m):
            quote, href = m.group(1), m.group(2)
            if not href.lower().split('#')[0].endswith('.md'):
                return m.group(0)
            target = href.split('#',1)[0].lstrip('./')
            if target not in known:
                return m.group(0)  # unresolved links reported below
            return 'href=' + quote + target[:-3] + '.html' + quote
        html_text = re.sub(r'href=(['+ '\"' + "'" + r'])(.*?)\1', fix_href, html_text)
        index_marker = '</main>'
        library = '<section class="card sandhya-library" id="library"><h2>अध्ययनग्रन्थाः · Study Library</h2><p>Generated from the Obsidian Markdown notes. Devanāgarī source and other scripts can be selected on each reading page.</p><ul>' + ''.join(cards) + '</ul></section>'
        if index_marker in html_text:
            html_text = html_text.replace(index_marker, library + index_marker, 1)
        else:
            html_text = html_text.replace('</body>', '<main>' + library + '</main></body>', 1)
    else:
        html_text = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Sandhyāvandanam</title><link rel="stylesheet" href="../assets/style.css"><main class="reader"><h1>सन्ध्यावन्दनम्</h1><p>Source-critical study and prayoga manual</p><ul>' + ''.join(cards) + '</ul></main></html>'
    (output / 'index.html').write_text(html_text, encoding='utf-8')
    print('Built', len(paths), 'Sandhyāvandanam Markdown pages as HTML.')


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

    tb_items = []
    if TB.exists():
        for path in TB.rglob("*.md"):
            meta, body = frontmatter(path.read_text(encoding="utf-8-sig"))
            if all(x in meta for x in ("ashtaka", "prapathaka", "anuvaka")):
                tb_items.append({"meta": meta, "sections": parse_tb_sections(body)})
    tb_items.sort(key=lambda x: (int(x["meta"]["ashtaka"]), int(x["meta"]["prapathaka"]), int(x["meta"]["anuvaka"])))
    for i, item in enumerate(tb_items):
        m = item["meta"]
        dest = DOCS / "tb" / ("%02d" % int(m["ashtaka"])) / ("%02d" % int(m["prapathaka"])) / ("%02d.html" % int(m["anuvaka"]))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(tb_page_html(item, tb_items[i-1] if i else None, tb_items[i+1] if i+1 < len(tb_items) else None), encoding="utf-8")

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

    chunks.extend(tb_index_chunks(tb_items))

    if (SRAUTA / "index.html").is_file():
        chunks.append(
            '<section class="index-kanda" id="srauta">'
            '<h2>श्रौतप्रयोगाः · Śrauta Rituals</h2>'
            '<div class="anuvaka-grid">'
            '<a class="anuvaka-card" href="srauta/index.html">'
            '<strong>साकमेधाः</strong><span>Ritual and mantra study</span>'
            '<small>Viśvāmitra Āprī, Sāyaṇa, ritual notes</small></a>'
            '</div></section>'
        )

    # Sandhyavandanam is a separate HTML reader backed by Obsidian notes.
    # Do not expose the Markdown source tree or arbitrary PDFs in GitHub Pages.
    if SANDHYA.is_dir():
        chunks.append(
            '<section class="index-kanda" id="sandhyavandanam">'
            '<h2>सन्ध्यावन्दनम् · Sandhyāvandanam</h2>'
            '<div class="anuvaka-grid">'
            '<a class="anuvaka-card" href="sandhyavandanam/index.html">'
            '<strong>सन्ध्योपासना</strong><span>Source-critical study and ritual traditions</span>'
            '<small>Gopīnātha Dīkṣita · Vedic sources · Comparative study</small></a>'
            '</div></section>'
        )

    index = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Taittirīya Vedic Study</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site-header">
<h1>Taittirīya Saṃhitā and Brāhmaṇa Study</h1>
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
details.sandhya-iast { margin:.7rem 0 1.3rem; }
details.sandhya-iast > p { padding:0 .85rem; }
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
    css += """
.sandhya-reading { max-width: 920px; }
.sandhya-reading h1,.sandhya-reading h2,.sandhya-reading h3 { color: var(--accent); }
.sandhya-reading p,.sandhya-reading li { overflow-wrap:anywhere; }
.sandhya-reading blockquote,.sandhya-callout { border-left:3px solid var(--accent); padding:.7rem 1rem; background:var(--note); margin:1rem 0; }
.sandhya-reading pre { white-space:pre-wrap; background:var(--soft); border:1px solid var(--line); border-radius:8px; padding:1rem; font-size:1.12rem; }
.sandhya-reading code { white-space:pre-wrap; overflow-wrap:anywhere; }
.sandhya-reading a { color:var(--accent); }
.sandhya-reading .table-scroll { overflow-x:auto; }
.sandhya-reading table { width:100%;border-collapse:collapse; }
.sandhya-reading th,.sandhya-reading td { padding:.6rem;border:1px solid var(--line);vertical-align:top; }
.sandhya-reading .script-switch { font-family:'Noto Serif Devanagari','Nirmala UI',serif; font-size:1.06em; }
.sandhya-reading .script-variant[hidden] { display:none; }
.sandhya-library { margin:2rem auto; max-width:1100px; }
.sandhya-library li { margin:.3rem 0; }
.sandhya-library small { color:var(--muted); padding-left:.5em; }
.unresolved { color:#ad552f; }
"""
    (DOCS / "assets" / "style.css").write_text(css.strip(), encoding="utf-8")

    # Include the Śrauta web pages in the published build. Do not copy the
    # entire directory: private source PDFs and handwritten notes must never
    # be published accidentally. Only explicitly approved web-file extensions
    # are copied. Keep private research files completely outside the repo.
    if SRAUTA.exists():
        allowed = {".html", ".json", ".css", ".js"}
        count = 0
        for path in SRAUTA.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in allowed:
                continue
            rel = path.relative_to(SRAUTA)
            if any(part.startswith(".") for part in rel.parts):
                continue
            dest = DOCS / "srauta" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            count += 1
        print("Built", count, "Śrauta web assets (restricted file types).")
    # Publish only this explicitly approved scholarly PDF. Never copy arbitrary PDFs
    # from the Śrauta source tree, especially any teacher's private manual.
    approved_pdf = SRAUTA / "sakamedha" / "Visvamitra_Apri_RV_3_4_Sayana_Scholarly_Study.pdf"
    if approved_pdf.is_file():
        pdf_dest = DOCS / "srauta" / "sakamedha" / approved_pdf.name
        pdf_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(approved_pdf, pdf_dest)
        print("Published approved Apri study PDF.")
    build_sandhya_pages()
    print("Built", len(items), "Saṃhitā pages and", len(tb_items), "Brāhmaṇa pages.")
    print("Script selector: Devanagari, IAST, ITRANS, Grantha, Telugu, Kannada, Malayalam.")
    print("Open:", DOCS / "index.html")

if __name__ == "__main__":
    main()
