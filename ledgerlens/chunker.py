from __future__ import annotations

import json
import re

from ledgerlens.config import RAW_DIR
from ledgerlens.processor import process_filing

MAX_CHARS = 1800
MAX_CAPTION_CHARS = 200
MAX_HEADING_LINE = 120
SENTENCE_END = re.compile(r"[.!?][\"”’)]*\s")


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    """Bahut lamba paragraph ho to use vaakya (sentence) ki border pe kaato."""

    pieces = []

    while len(paragraph) > max_chars:
        window = paragraph[:max_chars]
        cut = -1

        for match in SENTENCE_END.finditer(window):
            cut = match.end()

        if cut < max_chars // 2:
            cut = window.rfind(" ")

            if cut == -1:
                cut = max_chars

        pieces.append(paragraph[:cut].strip())
        paragraph = paragraph[cut:].strip()

    if paragraph:
        pieces.append(paragraph)

    return pieces


def _looks_like_heading(line: str) -> bool:
    """Chhoti line jo vaakya ki tarah khatam nahi hoti, wo aam taur par heading hoti hai."""

    line = line.strip()
    return 0 < len(line) <= MAX_HEADING_LINE and line[-1] not in ".!?"


def split_blocks(text: str) -> list[tuple[str, list[str]]]:
    """Text ko 'text' aur 'table' blocks mein baanto. Table row = jis line mein ' | ' ho."""

    blocks = []
    current_kind = None
    current_lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        kind = "table" if " | " in line else "text"

        if kind != current_kind and current_lines:
            blocks.append((current_kind, current_lines))
            current_lines = []

        current_kind = kind
        current_lines.append(line)

    if current_lines:
        blocks.append((current_kind, current_lines))

    fixed = []

    for kind, lines in blocks:
        if kind == "table" and len(lines) < 2:
            kind = "text"
        fixed.append((kind, lines))

    return fixed


def _split_table(rows: list[str], caption: str, max_chars: int) -> list[str]:
    """Badi table ko rows ke hisaab se todo, har tukde mein header row dohrao."""

    prefix = caption + "\n" if caption else ""
    header = rows[0] if len(rows[0]) <= max_chars // 3 else ""
    body = rows[1:] if header else rows
    head_lines = [header] if header else []
    limit = max(200, max_chars - len(prefix) - len(header) - 2)

    pieces = []

    for row in body:
        pieces.extend(_split_long_paragraph(row, limit))

    parts = []
    current = list(head_lines)

    for row in pieces:
        candidate = prefix + "\n".join(current + [row])

        if len(candidate) > max_chars and len(current) > len(head_lines):
            parts.append(prefix + "\n".join(current))
            current = list(head_lines)

        current.append(row)

    parts.append(prefix + "\n".join(current))
    return parts


def chunk_section(text: str, max_chars: int = MAX_CHARS) -> list[tuple[str, str]]:
    """Ek section ke text ko (kind, text) tukdon mein todo."""

    chunks = []
    buffer = []

    def flush():
        if buffer:
            chunks.append(("text", "\n".join(buffer)))
            buffer.clear()

    for kind, lines in split_blocks(text):
        if kind == "text":
            for paragraph in lines:
                for piece in _split_long_paragraph(paragraph, max_chars):
                    if len("\n".join(buffer + [piece])) > max_chars:
                        if not all(_looks_like_heading(b) for b in buffer):
                            carry = []

                            while _looks_like_heading(buffer[-1]):
                                carry.insert(0, buffer.pop())

                            flush()
                            buffer.extend(carry)

                    buffer.append(piece)
        else:
            caption = ""

            if buffer and len(buffer[-1]) <= MAX_CAPTION_CHARS:
                caption = buffer.pop()

            flush()

            for part in _split_table(lines, caption, max_chars):
                chunks.append(("table", part))

    flush()
    return chunks


def build_chunks(ticker, fiscal_year, sections, max_chars: int = MAX_CHARS) -> list[dict]:
    """Filing ke saare sections ko label lage chunks mein badlo."""

    chunks = []

    for section in sections:
        label = f"[{ticker} 10-K FY{fiscal_year} | {section['title']}]"

        for kind, text in chunk_section(section["text"], max_chars):
            chunks.append(
                {
                    "chunk_id": f"{ticker}-{fiscal_year}-{len(chunks):04d}",
                    "ticker": ticker,
                    "fiscal_year": fiscal_year,
                    "section": section["title"],
                    "kind": kind,
                    "text": f"{label}\n{text}",
                }
            )

    return chunks


def chunk_all_filings() -> None:
    out_dir = RAW_DIR.parent / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "chunks.jsonl"

    total = 0

    with out_path.open("w", encoding="utf-8") as f:
        for html_path in sorted(RAW_DIR.glob("*/*_10-K.html")):
            ticker = html_path.parent.name
            fiscal_year = int(html_path.stem.split("_")[0])

            sections = process_filing(html_path)
            chunks = build_chunks(ticker, fiscal_year, sections)

            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

            total += len(chunks)
            print(f"{ticker} FY{fiscal_year}: {len(sections)} sections, {len(chunks)} chunks")

    print(f"\nTotal {total} chunks -> {out_path}")


if __name__ == "__main__":
    chunk_all_filings()
