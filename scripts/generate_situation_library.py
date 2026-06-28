#!/usr/bin/env python3
from pathlib import Path
import html
import re


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "German-Learning-System"
SITUATIONS = PROJECT / "situations"
OUTPUT = PROJECT / "situation-library.html"
PAGES = PROJECT / "situation-pages"

DOMAIN_CONFIG = {
    "healthcare": ("Healthcare", "var(--pink)", 10),
    "government": ("Government", "var(--blue)", 20),
    "housing": ("Housing", "var(--purple)", 30),
    "daily_life": ("Daily Life", "var(--green)", 40),
    "family_school": ("Education", "var(--blue)", 50),
    "education": ("Education", "var(--blue)", 51),
    "work": ("Work", "var(--orange)", 60),
    "social": ("Social", "var(--pink)", 70),
    "transport": ("Transport", "var(--teal)", 80),
    "emergency": ("Emergency", "var(--red)", 90),
}


def esc(value):
    return html.escape(str(value), quote=True)


def extract_section(content, heading):
    pattern = rf"^## {re.escape(heading)}\n([\s\S]*?)(?=\n## |\n# |$)"
    match = re.search(pattern, content, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_description(content):
    overview = extract_section(content, "Overview")
    for block in re.split(r"\n\s*\n", overview):
        block = block.strip()
        if block and not block.startswith("|") and not block.startswith("The situation can grow"):
            return re.sub(r"\s+", " ", block)
    return "Open the situation file for dialogues, vocabulary, writing tasks, and real-life practice."


def extract_tags(content):
    section = extract_section(content, "Communication Functions Practiced")
    tags = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            tags.append(line[2:].strip())
    return tags[:3] or ["situation practice", "dialogues", "writing"]


def extract_level_range(content):
    order = ["A1", "A2", "B1", "B2", "C1"]
    found = re.findall(r"\|\s*(A1|A2|B1|B2|C1)\s*\|", content)
    unique = sorted(set(found), key=order.index)
    if not unique:
        return "A1-B2"
    if len(unique) == 1:
        return unique[0]
    return f"{unique[0]}-{unique[-1]}"


def page_path_for(source_path):
    relative = source_path.relative_to(SITUATIONS).with_suffix(".html")
    return PAGES / relative


def title_from_filename(path):
    return path.stem.replace("_", " ").title()


def read_situation(path):
    content = path.read_text(encoding="utf-8")
    relative = path.relative_to(PROJECT).as_posix()
    folder = path.relative_to(SITUATIONS).parts[0]
    domain, color, order = DOMAIN_CONFIG.get(folder, ("Other", "var(--teal)", 999))
    title_match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else title_from_filename(path)
    page_path = page_path_for(path)
    return {
        "title": title,
        "domain": domain,
        "domain_order": order,
        "color": color,
        "href": relative,
        "page_href": page_path.relative_to(PROJECT).as_posix(),
        "source_path": path,
        "page_path": page_path,
        "content": content,
        "level": extract_level_range(content),
        "description": extract_description(content),
        "tags": extract_tags(content),
    }


def render_card(item):
    tags = "".join(f'<span class="tag">{esc(tag)}</span>' for tag in item["tags"])
    return f'''        <a class="card" href="{esc(item["page_href"])}">
          <div>
            <div class="card-top"><h3>{esc(item["title"])}</h3><span class="level">{esc(item["level"])}</span></div>
            <p class="desc">{esc(item["description"])}</p>
            <div class="tags">{tags}</div>
          </div>
          <div class="path">{esc(item["href"])}</div>
        </a>'''


def render_inline(text):
    escaped = esc(text)
    code_chunks = []

    def hold_code(match):
        code_chunks.append(match.group(1))
        return f"@@CODE{len(code_chunks) - 1}@@"

    escaped = re.sub(r"`([^`]+)`", hold_code, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)

    for index, chunk in enumerate(code_chunks):
        escaped = escaped.replace(f"@@CODE{index}@@", f"<code>{chunk}</code>")
    return escaped


def split_table_row(line):
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def render_table(lines):
    rows = [split_table_row(line) for line in lines if line.strip()]
    rows = [row for row in rows if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)]
    if not rows:
        return ""

    header = rows[0]
    body = rows[1:]
    head_cells = "".join(f"<th>{render_inline(cell)}</th>" for cell in header)
    body_rows = "\n".join(
        "<tr>" + "".join(f"<td>{render_inline(cell)}</td>" for cell in row) + "</tr>"
        for row in body
    )
    return f"<table><thead><tr>{head_cells}</tr></thead><tbody>{body_rows}</tbody></table>"


def code_block_class(code_lang, code_text):
    normalized_lang = code_lang.strip().lower()
    lines = [line for line in code_text.splitlines() if line.strip()]
    has_tree = any(marker in code_text for marker in ("├", "└", "│", "→", "↓"))
    has_metadata = any(
        marker in code_text
        for marker in (
            "Situation Name:",
            "Situation Category:",
            "Description:",
            "Typical Participants:",
            "Confidence Outcome:",
        )
    )
    has_sentence_slots = any(
        marker in code_text
        for marker in ("Hauptsatz", "Nebensatz", "W-question", "Yes-no", "Modal verb", "Perfekt")
    )

    if normalized_lang in ("text", "txt", ""):
        if has_metadata:
            return "metadata-block"
        if has_tree or len(lines) >= 10:
            return "system-map"
        if has_sentence_slots or len(lines) <= 8:
            return "pattern-block"
        return "reference-block"
    return "code-block"


def render_code_block(code_lang, code_lines):
    code_text = chr(10).join(code_lines)
    block_class = code_block_class(code_lang, code_text)
    lang_class = f" language-{esc(code_lang)}" if code_lang else ""
    return (
        f'<pre class="{block_class}"><code class="{lang_class.strip()}">'
        f"{esc(code_text)}"
        "</code></pre>"
    )


def markdown_to_html(markdown):
    html_parts = []
    lines = markdown.splitlines()
    in_code = False
    code_lang = ""
    code_lines = []
    list_open = False
    table_lines = []

    def close_list():
        nonlocal list_open
        if list_open:
            html_parts.append("</ul>")
            list_open = False

    def close_table():
        nonlocal table_lines
        if table_lines:
            html_parts.append(render_table(table_lines))
            table_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            close_table()
            close_list()
            if in_code:
                html_parts.append(render_code_block(code_lang, code_lines))
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                in_code = True
                code_lang = stripped[3:].strip()
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            close_table()
            close_list()
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            close_list()
            table_lines.append(stripped)
            continue

        close_table()

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            close_list()
            level = len(heading.group(1))
            text = render_inline(heading.group(2))
            html_parts.append(f"<h{level}>{text}</h{level}>")
            continue

        if stripped.startswith("- "):
            if not list_open:
                html_parts.append("<ul>")
                list_open = True
            html_parts.append(f"<li>{render_inline(stripped[2:].strip())}</li>")
            continue

        close_list()
        html_parts.append(f"<p>{render_inline(stripped)}</p>")

    close_table()
    close_list()
    if in_code:
        html_parts.append(render_code_block(code_lang, code_lines))
    return "\n".join(part for part in html_parts if part)


def render_situation_page(item):
    content = markdown_to_html(item["content"])
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(item["title"])} | German Learning System</title>
  <style>
    :root {{
      --bg: #faf9f5;
      --ink: #18181b;
      --muted: #71717a;
      --line: #e8e4dc;
      --card: #ffffff;
      --accent: {item["color"]};
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.62;
    }}

    a {{ color: inherit; }}

    .shell {{
      max-width: 920px;
      margin: 0 auto;
      padding: 38px 24px 80px;
    }}

    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 44px;
    }}

    .back {{
      color: var(--muted);
      font-size: 14px;
      font-weight: 700;
      text-decoration: none;
    }}

    .back:hover {{ color: var(--accent); }}

    .source {{
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      text-align: right;
      word-break: break-word;
    }}

    article {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 44px;
    }}

    h1 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(40px, 8vw, 68px);
      line-height: 0.95;
      margin: 0 0 28px;
      letter-spacing: -0.025em;
    }}

    h2 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: 32px;
      line-height: 1.1;
      margin: 46px 0 16px;
      padding-top: 24px;
      border-top: 1px solid var(--line);
    }}

    h3 {{
      font-size: 21px;
      line-height: 1.2;
      margin: 30px 0 12px;
    }}

    h4 {{
      font-size: 16px;
      margin: 24px 0 10px;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    p, li {{
      color: #3f3f46;
      font-size: 16px;
    }}

    ul {{
      margin: 0 0 20px;
      padding-left: 22px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 18px 0 26px;
      font-size: 14px;
    }}

    th, td {{
      border: 1px solid var(--line);
      padding: 10px 12px;
      vertical-align: top;
      text-align: left;
    }}

    th {{
      background: #f4f4f5;
      color: #27272a;
    }}

    pre {{
      overflow-x: auto;
      background: #18181b;
      color: #fafafa;
      border-radius: 8px;
      padding: 18px;
      margin: 18px 0 24px;
      line-height: 1.5;
    }}

    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.92em;
    }}

    p code, li code {{
      background: #f4f4f5;
      color: #27272a;
      padding: 2px 5px;
      border-radius: 5px;
    }}

    strong {{ color: #18181b; }}
    em {{ color: #52525b; }}

    @media (max-width: 680px) {{
      .shell {{ padding: 24px 14px 52px; }}
      .topbar {{ align-items: flex-start; flex-direction: column; }}
      .source {{ text-align: left; }}
      article {{ padding: 26px 18px; }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
  <link rel="stylesheet" href="../../styles/design-system.css">
</head>
<body class="situation-page">
  <main class="shell">
    <nav class="topbar" aria-label="Situation navigation">
      <a class="back" href="../../situation-library.html">Back to Situation Library</a>
      <div class="source">{esc(item["href"])}</div>
    </nav>
    <article>
{content}
    </article>
  </main>
</body>
</html>
'''


def render_domain(domain, items):
    color = items[0]["color"]
    label = "situation" if len(items) == 1 else "situations"
    cards = "\n".join(render_card(item) for item in items)
    return f'''    <section class="domain" style="--accent: {color};">
      <div class="domain-head">
        <h2>{esc(domain)}</h2>
        <div class="domain-meta">{len(items)} {label}</div>
      </div>
      <div class="grid">
{cards}
      </div>
    </section>'''


def render_page(situations):
    grouped = {}
    for item in situations:
        grouped.setdefault(item["domain"], []).append(item)

    domains = sorted(
        grouped.items(),
        key=lambda pair: (pair[1][0]["domain_order"], pair[0]),
    )
    domains = [
        (domain, sorted(items, key=lambda item: item["title"].casefold()))
        for domain, items in domains
    ]
    domain_sections = "\n\n".join(render_domain(domain, items) for domain, items in domains)

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Situation Library | German Learning System</title>
  <style>
    :root {{
      --bg: #faf9f5;
      --ink: #18181b;
      --muted: #71717a;
      --line: #e8e4dc;
      --card: #ffffff;
      --teal: #11b5a4;
      --blue: #2563eb;
      --pink: #db2777;
      --green: #16a34a;
      --orange: #ea580c;
      --purple: #7c3aed;
      --red: #dc2626;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}

    a {{ color: inherit; text-decoration: none; }}

    .shell {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 56px 28px 72px;
    }}

    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 52px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 750;
      letter-spacing: -0.01em;
    }}

    .mark {{
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: var(--teal);
      color: #fff;
      display: grid;
      place-items: center;
      font-family: Georgia, serif;
      font-size: 22px;
      font-weight: 700;
    }}

    .navlink {{
      color: var(--muted);
      font-size: 14px;
      font-weight: 650;
      border-bottom: 1px solid transparent;
    }}

    .navlink:hover {{
      color: var(--ink);
      border-bottom-color: var(--teal);
    }}

    .toplinks {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .hero {{
      max-width: 860px;
      margin-bottom: 42px;
    }}

    .eyebrow {{
      color: var(--teal);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      margin-bottom: 14px;
    }}

    h1 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(42px, 7vw, 76px);
      line-height: 0.94;
      margin: 0 0 20px;
      letter-spacing: -0.025em;
    }}

    .lead {{
      max-width: 720px;
      color: #3f3f46;
      font-size: 18px;
      margin: 0;
    }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 36px 0 54px;
    }}

    .summary-item {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px 20px;
    }}

    .summary-number {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: 34px;
      line-height: 1;
      margin-bottom: 8px;
    }}

    .summary-label {{
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
    }}

    .domain {{
      margin-top: 48px;
      padding-top: 28px;
      border-top: 1px solid var(--line);
    }}

    .domain-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 18px;
    }}

    h2 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: 32px;
      line-height: 1;
      margin: 0;
      letter-spacing: -0.015em;
    }}

    .domain-meta {{
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      white-space: nowrap;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
    }}

    .card {{
      min-height: 218px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 22px;
      transition: transform 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
    }}

    .card:hover {{
      transform: translateY(-2px);
      border-color: var(--accent);
      box-shadow: 0 12px 32px rgba(24, 24, 27, 0.08);
    }}

    .card-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 16px;
    }}

    h3 {{
      font-size: 20px;
      line-height: 1.12;
      margin: 0;
      letter-spacing: -0.01em;
    }}

    .level {{
      flex: 0 0 auto;
      color: var(--accent);
      background: #f4f4f5;
      border-radius: 7px;
      padding: 5px 8px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.04em;
    }}

    .desc {{
      color: var(--muted);
      font-size: 14px;
      margin: 0 0 18px;
    }}

    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-bottom: 18px;
    }}

    .tag {{
      color: #3f3f46;
      background: #f4f4f5;
      border-radius: 999px;
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 650;
    }}

    .path {{
      color: var(--accent);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      word-break: break-word;
    }}

    .note {{
      margin-top: 54px;
      background: #fffbeb;
      border: 1px solid #fde8b0;
      border-radius: 8px;
      padding: 22px 24px;
      color: #3f3f46;
      max-width: 820px;
    }}

    .note strong {{ color: #92400e; }}

    @media (max-width: 900px) {{
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}

    @media (max-width: 640px) {{
      .shell {{ padding: 34px 18px 54px; }}
      .topbar,
      .domain-head {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .summary,
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
  <link rel="stylesheet" href="styles/design-system.css">
</head>
<body>
  <main class="shell">
    <nav class="topbar" aria-label="Project navigation">
      <a class="brand" href="index.html">
        <span class="mark">D</span>
        <span>German Learning System</span>
      </a>
      <div class="toplinks">
        <a class="navlink" href="foundation-reference.html">Foundation</a>
        <a class="navlink" href="design-system.html">Design System</a>
      </div>
    </nav>

    <section class="hero">
      <div class="eyebrow">Situation Library</div>
      <h1>Real-life German, grouped by domain.</h1>
      <p class="lead">This page is generated from the Markdown files in <code>situations/</code>. Add a new situation file, run <code>python3 scripts/generate_situation_library.py</code>, and it will appear here automatically.</p>
    </section>

    <section class="summary" aria-label="Library summary">
      <div class="summary-item">
        <div class="summary-number">{len(situations)}</div>
        <div class="summary-label">available situation files</div>
      </div>
      <div class="summary-item">
        <div class="summary-number">{len(domains)}</div>
        <div class="summary-label">real-life domains</div>
      </div>
      <div class="summary-item">
        <div class="summary-number">A1-C1</div>
        <div class="summary-label">full system range</div>
      </div>
      <div class="summary-item">
        <div class="summary-number">1</div>
        <div class="summary-label">situation-first system</div>
      </div>
    </section>

{domain_sections}

    <section class="note">
      <strong>Generated page:</strong> this library is rebuilt from the contents of <code>situations/</code>. To refresh it after adding or editing situation files, run <code>python3 scripts/generate_situation_library.py</code>.
    </section>
  </main>
</body>
</html>
'''


def main():
    situations = [read_situation(path) for path in sorted(SITUATIONS.rglob("*.md"))]
    for item in situations:
        item["page_path"].parent.mkdir(parents=True, exist_ok=True)
        item["page_path"].write_text(render_situation_page(item), encoding="utf-8")
    OUTPUT.write_text(render_page(situations), encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)} and {len(situations)} situation pages.")


if __name__ == "__main__":
    main()
