from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

# 10-K ke Items ka official order aur official naam.
ITEM_TITLES = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "1C": "Cybersecurity",
    "2": "Properties",
    "3": "Legal Proceedings",
    "4": "Mine Safety Disclosures",
    "5": "Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities",
    "6": "[Reserved]",
    "7": "Management's Discussion and Analysis of Financial Condition and Results of Operations",
    "7A": "Quantitative and Qualitative Disclosures About Market Risk",
    "8": "Financial Statements and Supplementary Data",
    "9": "Changes in and Disagreements with Accountants on Accounting and Financial Disclosure",
    "9A": "Controls and Procedures",
    "9B": "Other Information",
    "9C": "Disclosure Regarding Foreign Jurisdictions that Prevent Inspections",
    "10": "Directors, Executive Officers and Corporate Governance",
    "11": "Executive Compensation",
    "12": "Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters",
    "13": "Certain Relationships and Related Transactions, and Director Independence",
    "14": "Principal Accountant Fees and Services",
    "15": "Exhibits and Financial Statement Schedules",
    "16": "Form 10-K Summary",
}

ITEM_ORDER = list(ITEM_TITLES)

ITEM_PATTERN = re.compile(
    r"^item\s+(\d{1,2}[A-C]?)\s*[.:\-–—]?\s*(.*)$",
    re.IGNORECASE,
)

# Har page ke upar chhapi "Item 7" jaisi line (running header), jisme heading ka naam nahi hota.
PAGE_HEADER = re.compile(
    r"^item\s+\d{1,2}[A-C]?(\s*,\s*(item\s+)?\d{1,2}[A-C]?)*$",
    re.IGNORECASE,
)

# Page number, "Table of Contents" aur "PART II" jaisi akeli lines kachra hain.
NOISE_LINE = re.compile(r"^(\d{1,3}|table of contents|part\s+[ivx]+)$", re.IGNORECASE)

BLOCK_TAGS = [
    "div", "p", "br", "tr", "li", "ul", "ol", "table",
    "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "blockquote",
]

TITLE_CONNECTORS = {"of", "and", "the", "for", "to", "in", "with", "on", "or", "related"}

MAX_HEADING_CHARS = 250
MAX_TITLE_CHARS = 200


def _clean_cell(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"([($])\s+", r"\1", text)
    text = re.sub(r"\s+([)%])", r"\1", text)
    return text


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
            _clean_cell(td.get_text(""))
            for td in tr.find_all(["td", "th"], recursive=False)
        ]
        cells = _merge_cells(cells)

        if cells:
            rows.append(" | ".join(cells))

    return "\n".join(rows)


def html_to_text(html_path: Path) -> str:
    """Convert an SEC filing HTML document into clean plain text.

    Nayi line sirf block elements (div, p, tr, ...) ke baad aati hai, span jaise inline
    tukdon ke baad nahi, jaise browser dikhata hai.
    """

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    for tag in soup.find_all(BLOCK_TAGS):
        tag.insert(0, "\n")
        tag.append("\n")

    for table in soup.find_all("table"):
        if table.find_parent("table"):
            continue
        table.replace_with(NavigableString("\n" + table_to_text(table) + "\n"))

    text = soup.get_text("")

    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if line and not NOISE_LINE.match(line):
            lines.append(line)

    return "\n".join(lines)


def _find_headings(lines: list[str]) -> list[tuple[int, str, str, int]]:
    """Un sab lines ko dhundho jo 'Item X' heading jaisi dikhti hain.

    Return: (line_number, item_key, title, body_start_line)
    """

    headings = []

    for i, line in enumerate(lines):
        if len(line) > MAX_HEADING_CHARS:
            continue

        cells = [cell.strip() for cell in line.split(" | ")]
        match = ITEM_PATTERN.match(cells[0])

        if not match:
            continue

        if len(cells) > 1 and cells[-1].isdigit():
            continue  # table of contents row: aakhir mein page number hota hai

        key = match.group(1).upper()

        if key not in ITEM_TITLES:
            continue

        title = match.group(2).strip()
        after_key = cells[0][match.end(1):].lstrip()
        has_delimiter = after_key[:1] in {".", ":", "-", "–", "—"}

        if not has_delimiter and (not title or title.startswith(",")):
            continue  # page ke upar chhapa "Item 7" jaisa running header, heading nahi

        if not title and len(cells) > 1:
            title = cells[1]

        body_start = i + 1
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        next_is_title_part = 0 < len(next_line) <= MAX_TITLE_CHARS and not ITEM_PATTERN.match(
            next_line
        )

        if not title and next_is_title_part:
            title = next_line
            body_start = i + 2
        elif title and title.split()[-1].lower().strip(",") in TITLE_CONNECTORS:
            if next_is_title_part:
                body_start = i + 2  # lamba naam agli line mein bhi chala gaya hai

        headings.append((i, key, title, body_start))

    return headings


def _choose_headings(headings: list[tuple[int, str, str, int]], lines: list[str]) -> list[int]:
    """Headings ki wo list chuno jo Item order mein badhti jaye aur jiske neeche sabse zyada text ho."""

    count = len(headings)
    ranks = [ITEM_ORDER.index(h[1]) for h in headings]

    weights = []

    for n, (_, _, _, body_start) in enumerate(headings):
        next_heading_line = headings[n + 1][0] if n + 1 < count else len(lines)
        weights.append(sum(len(line) for line in lines[body_start:next_heading_line]) + 1)

    score = list(weights)
    previous = [-1] * count

    for i in range(count):
        for j in range(i):
            if ranks[j] < ranks[i] and score[j] + weights[i] > score[i]:
                score[i] = score[j] + weights[i]
                previous[i] = j

    last = max(range(count), key=lambda i: score[i])
    chosen = []

    while last != -1:
        chosen.append(last)
        last = previous[last]

    chosen.reverse()
    return chosen


def extract_sections(text: str) -> list[dict[str, str]]:
    """Split a filing into SEC Item-based sections.

    Ek Item ki heading kai jagah dikh sakti hai (table of contents, cross-reference).
    Hum wo headings chunte hain jo sahi order mein hon aur jinke neeche sabse zyada text ho.
    Section ka naam hamesha official naam hota hai, taaki saari companies mein ek jaisa rahe.
    """

    lines = [line.strip() for line in text.splitlines()]
    headings = _find_headings(lines)

    if not headings:
        return []

    chosen = _choose_headings(headings, lines)
    sections = []

    for pos, n in enumerate(chosen):
        _, key, _, body_start = headings[n]
        end = headings[chosen[pos + 1]][0] if pos + 1 < len(chosen) else len(lines)
        body_lines = [line for line in lines[body_start:end] if not PAGE_HEADER.match(line)]
        body = "\n".join(body_lines).strip()

        if body:
            sections.append({"title": f"Item {key}. {ITEM_TITLES[key]}", "text": body})

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
