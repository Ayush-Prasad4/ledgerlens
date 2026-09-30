from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString


ITEM_PATTERN = re.compile(
    r"^(Item\s+\d+[A-Z]?(?:\.\s*|\s+).+)$",
    re.IGNORECASE,
)


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


def extract_sections(text: str) -> list[dict[str, str]]:
    """Split a filing into SEC Item-based sections."""

    lines = text.splitlines()

    sections = []
    current_title = None
    current_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        match = ITEM_PATTERN.match(line)

        if match:
            if current_title and current_lines:
                sections.append(
                    {
                        "title": current_title,
                        "text": "\n".join(current_lines).strip(),
                    }
                )

            current_title = match.group(1).strip()
            current_lines = []

        elif current_title:
            current_lines.append(line)

    if current_title and current_lines:
        sections.append(
            {
                "title": current_title,
                "text": "\n".join(current_lines).strip(),
            }
        )

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
