from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString


ITEM_ORDER = [
    "1", "1A", "1B", "1C", "2", "3", "4", "5", "6", "7", "7A", "8",
    "9", "9A", "9B", "9C", "10", "11", "12", "13", "14", "15", "16",
]

ITEM_PATTERN = re.compile(
    r"^item\s+(\d{1,2}[A-C]?)\s*[.:\-–—]?\s*(.*)$",
    re.IGNORECASE,
)

MAX_HEADING_CHARS = 250
MAX_TITLE_CHARS = 200


def _merge_cells(cells: list[str]) -> list[str]:
    """SEC tables split '$', '7', '%' and ')' into separate cells; glue them back."""

    merged = []
    prefix = ""

    for cell in cells:
        if not cell:
            continue

        if cell in {"$", "("}:
            prefix += cell
            continue

        if cell in {"%", ")", ")%"} and merged:
            merged[-1] += cell
            continue

        merged.append(prefix + cell)
        prefix = ""

    return merged


def table_to_text(table) -> str:
    """Turn an HTML table into text: one row per line, cells separated by ' | '."""

    rows = []

    for tr in table.find_all("tr"):
        if tr.find_parent("table") is not table:
            continue

        cells = [
            re.sub(r"\s+", " ", td.get_text(" ")).strip()
            for td in tr.find_all(["td", "th"], recursive=False)
        ]
        cells = _merge_cells(cells)

        if cells:
            rows.append(" | ".join(cells))

    return "\n".join(rows)


def html_to_text(html_path: Path) -> str:
    """Convert an SEC filing HTML document into clean plain text."""

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    for table in soup.find_all("table"):
        if table.find_parent("table"):
            continue
        table.replace_with(NavigableString("\n" + table_to_text(table) + "\n"))

    text = soup.get_text("\n")

    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def _find_headings(lines: list[str]) -> list[tuple[int, str, str, int]]:
    """Un sab lines ko dhundho jo 'Item X' heading jaisi dikhti hain.

    Return: (line_number, item_key, title, body_start_line)
    """

    headings = []

    for i, line in enumerate(lines):
        match = ITEM_PATTERN.match(line)

        if not match or " | " in line or len(line) > MAX_HEADING_CHARS:
            continue

        key = match.group(1).upper()

        if key not in ITEM_ORDER:
            continue

        title = match.group(2).strip()
        body_start = i + 1

        if not title and i + 1 < len(lines):
            next_line = lines[i + 1]

            if 0 < len(next_line) <= MAX_TITLE_CHARS and not ITEM_PATTERN.match(next_line):
                title = next_line
                body_start = i + 2

        headings.append((i, key, title, body_start))

    return headings


def extract_sections(text: str) -> list[dict[str, str]]:
    """Split a filing into SEC Item-based sections.

    Ek Item ki heading kai jagah dikh sakti hai (table of contents, cross-reference).
    Asli heading wo hai jiske baad sabse zyada text aata hai.
    """

    lines = [line.strip() for line in text.splitlines()]
    headings = _find_headings(lines)

    if not headings:
        return []

    spans = []

    for n, (_, _, _, body_start) in enumerate(headings):
        next_heading_line = headings[n + 1][0] if n + 1 < len(headings) else len(lines)
        spans.append(sum(len(line) for line in lines[body_start:next_heading_line]))

    best = {}

    for n, (_, key, _, _) in enumerate(headings):
        if key not in best or spans[n] > spans[best[key]]:
            best[key] = n

    chosen = []
    last_rank = -1

    for n in sorted(best.values()):
        rank = ITEM_ORDER.index(headings[n][1])

        if rank > last_rank:
            chosen.append(n)
            last_rank = rank

    sections = []

    for pos, n in enumerate(chosen):
        _, key, title, body_start = headings[n]
        end = headings[chosen[pos + 1]][0] if pos + 1 < len(chosen) else len(lines)
        body = "\n".join(lines[body_start:end]).strip()

        if body:
            label = f"Item {key}. {title}" if title else f"Item {key}"
            sections.append({"title": label, "text": body})

    return sections


def process_filing(html_path: str | Path) -> list[dict[str, str]]:
    """Parse an SEC filing into structured sections."""

    path = Path(html_path)

    if not path.exists():
        raise FileNotFoundError(f"Filing not found: {path}")

    if path.suffix.lower() not in {".html", ".htm"}:
        raise ValueError(f"Expected HTML file, got: {path.suffix}")

    text = html_to_text(path)
    return extract_sections(text)


if __name__ == "__main__":
    sample = Path("data/raw/AAPL/2025_10-K.html")

    sections = process_filing(sample)

    print(f"Found {len(sections)} sections\n")

    for index, section in enumerate(sections, start=1):
        print(f"{index}. {section['title']}")
        print(f"   Characters: {len(section['text']):,}")
