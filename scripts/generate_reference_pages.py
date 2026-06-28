#!/usr/bin/env python3
from pathlib import Path
import html
import re


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "German-Learning-System"

REFERENCE_PAGES = [
    ("FOUNDATION_REFERENCE.md", "foundation-reference.html", "Foundation Reference", "The learner's map of how German works."),
    ("GRAMMAR_MAP.md", "grammar-map.html", "Grammar Map", "German grammar as a connected system."),
    ("SENTENCE_ARCHITECTURE_MAP.md", "sentence-architecture-map.html", "Sentence Architecture Map", "How German sentences are built and connected."),
    ("COMMUNICATION_FUNCTIONS.md", "communication-functions.html", "Communication Functions", "What learners can do with German."),
    ("LEARNING_MODEL.md", "learning-model.html", "Learning Model", "How a lesson moves from real life to confidence."),
    ("LESSON_BLUEPRINT.md", "lesson-blueprint.html", "Lesson Blueprint", "The repeatable structure for every situation lesson."),
]


def esc(value):
    return html.escape(str(value), quote=True)


def slugify(text):
    text = text.lower()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "section"


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
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


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
    has_sentence_slots = any(
        marker in code_text
        for marker in ("Position", "Hauptsatz", "Nebensatz", "Verb", "Subject", "Connector")
    )

    if normalized_lang in ("text", "txt", ""):
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


def collect_toc(markdown):
    headings = []
    seen = {}
    for line in markdown.splitlines():
        match = re.match(r"^(#{2,4})\s+(.+)$", line.strip())
        if not match:
            continue
        level = len(match.group(1))
        title = re.sub(r"`([^`]+)`", r"\1", match.group(2)).strip()
        slug = slugify(title)
        if slug in seen:
            seen[slug] += 1
            slug = f"{slug}-{seen[slug]}"
        else:
            seen[slug] = 1
        headings.append({"level": level, "title": title, "slug": slug})
    return headings


def markdown_to_html(markdown):
    html_parts = []
    lines = markdown.splitlines()
    heading_slugs = {}
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

    def unique_slug(title):
        slug = slugify(title)
        if slug in heading_slugs:
            heading_slugs[slug] += 1
            return f"{slug}-{heading_slugs[slug]}"
        heading_slugs[slug] = 1
        return slug

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
            text = heading.group(2)
            slug = unique_slug(re.sub(r"`([^`]+)`", r"\1", text))
            html_parts.append(f'<h{level} id="{esc(slug)}">{render_inline(text)}</h{level}>')
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


def render_reference_nav(current_output):
    links = []
    for _, output, label, _ in REFERENCE_PAGES:
        active = " active" if output == current_output else ""
        links.append(f'<a class="doc-link{active}" href="{esc(output)}">{esc(label)}</a>')
    return "\n".join(links)


def render_toc(toc):
    if not toc:
        return ""
    links = []
    for item in toc:
        indent = f" level-{item['level']}"
        links.append(f'<a class="toc-link{indent}" href="#{esc(item["slug"])}">{esc(item["title"])}</a>')
    return "\n".join(links)


def render_page(source_file, output_file, label, description):
    markdown = (PROJECT / source_file).read_text(encoding="utf-8")
    toc = collect_toc(markdown)
    content = markdown_to_html(markdown)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(label)} | German Learning System</title>
  <style>
    :root {{
      --bg: #faf9f5;
      --ink: #18181b;
      --muted: #71717a;
      --line: #e8e4dc;
      --card: #ffffff;
      --teal: #11b5a4;
      --blue: #2563eb;
    }}

    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.62;
    }}

    a {{ color: inherit; }}

    .shell {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 34px 28px 80px;
    }}

    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 42px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      color: var(--ink);
      font-weight: 750;
      text-decoration: none;
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

    .toplinks {{
      display: flex;
      align-items: center;
      gap: 16px;
      color: var(--muted);
      font-size: 14px;
      font-weight: 700;
    }}

    .toplinks a {{
      text-decoration: none;
      border-bottom: 1px solid transparent;
    }}

    .toplinks a:hover {{
      color: var(--ink);
      border-bottom-color: var(--teal);
    }}

    .hero {{
      max-width: 840px;
      margin-bottom: 34px;
    }}

    .eyebrow {{
      color: var(--teal);
      font-size: 12px;
      font-weight: 850;
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

    .layout {{
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
      gap: 28px;
      align-items: start;
    }}

    .sidebar {{
      position: sticky;
      top: 18px;
      display: grid;
      gap: 18px;
    }}

    .panel {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}

    .panel-title {{
      color: var(--muted);
      font-size: 11px;
      font-weight: 850;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 12px;
    }}

    .doc-link,
    .toc-link {{
      display: block;
      color: #52525b;
      text-decoration: none;
      font-size: 13px;
      font-weight: 700;
      padding: 8px 10px;
      border-radius: 7px;
    }}

    .doc-link:hover,
    .toc-link:hover {{
      color: var(--ink);
      background: #f4f4f5;
    }}

    .doc-link.active {{
      color: #fff;
      background: var(--teal);
    }}

    .toc-link.level-3 {{ padding-left: 22px; font-weight: 650; }}
    .toc-link.level-4 {{ padding-left: 34px; font-weight: 600; color: var(--muted); }}

    article {{
      min-width: 0;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 44px;
    }}

    article h1 {{
      font-size: clamp(38px, 6vw, 62px);
      margin-bottom: 28px;
    }}

    h2 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: 34px;
      line-height: 1.08;
      margin: 50px 0 16px;
      padding-top: 26px;
      border-top: 1px solid var(--line);
    }}

    h3 {{
      font-size: 22px;
      line-height: 1.2;
      margin: 34px 0 12px;
    }}

    h4 {{
      color: var(--blue);
      font-size: 16px;
      margin: 26px 0 10px;
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
      margin: 18px 0 28px;
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

    strong {{ color: var(--ink); }}

    @media (max-width: 980px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .sidebar {{ position: static; }}
      .panel.toc {{ max-height: 280px; overflow: auto; }}
    }}

    @media (max-width: 680px) {{
      .shell {{ padding: 24px 14px 54px; }}
      .topbar {{ align-items: flex-start; flex-direction: column; }}
      .toplinks {{ flex-wrap: wrap; }}
      article {{ padding: 26px 18px; }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
  <link rel="stylesheet" href="styles/design-system.css">
</head>
<body class="reference-page">
  <main class="shell">
    <nav class="topbar" aria-label="Project navigation">
      <a class="brand" href="index.html">
        <span class="mark">D</span>
        <span>German Learning System</span>
      </a>
      <div class="toplinks">
        <a href="foundation-reference.html">Foundation</a>
        <a href="situation-library.html">Situations</a>
        <a href="design-system.html">Design System</a>
      </div>
    </nav>

    <section class="hero">
      <div class="eyebrow">Reference System</div>
      <h1>{esc(label)}</h1>
      <p class="lead">{esc(description)}</p>
    </section>

    <div class="layout">
      <aside class="sidebar">
        <section class="panel">
          <div class="panel-title">Reference Docs</div>
{render_reference_nav(output_file)}
        </section>
        <section class="panel toc">
          <div class="panel-title">On This Page</div>
{render_toc(toc)}
        </section>
      </aside>

      <article>
{content}
      </article>
    </div>
  </main>
</body>
</html>
'''


def main():
    generated = []
    for source_file, output_file, label, description in REFERENCE_PAGES:
        source = PROJECT / source_file
        if not source.exists():
            continue
        output = PROJECT / output_file
        output.write_text(render_page(source_file, output_file, label, description), encoding="utf-8")
        generated.append(output.name)
    print(f"Generated {len(generated)} reference pages: {', '.join(generated)}")


if __name__ == "__main__":
    main()
