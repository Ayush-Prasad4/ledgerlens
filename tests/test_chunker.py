from ledgerlens.chunker import build_chunks, chunk_section

SECTION_TEXT = """Net sales increased during 2025.
Net sales by segment (dollars in millions):
2025 | Change | 2024
Americas | $178,353 | 7% | $167,045
Europe | 111,032 | 10% | 101,328
Americas net sales increased due to iPhone."""


def test_small_section_becomes_text_table_text():
    chunks = chunk_section(SECTION_TEXT)
    kinds = [kind for kind, _ in chunks]
    assert kinds == ["text", "table", "text"]


def test_table_gets_its_caption_and_caption_not_duplicated():
    chunks = chunk_section(SECTION_TEXT)
    table_text = chunks[1][1]
    assert table_text.startswith("Net sales by segment (dollars in millions):")
    assert "Americas | $178,353" in table_text
    assert "Net sales by segment" not in chunks[0][1]


def test_long_text_is_split_below_limit():
    text = "\n".join(["This is a sentence about risk. " * 10] * 20)
    chunks = chunk_section(text, max_chars=500)
    assert len(chunks) > 1
    assert all(len(t) <= 500 for _, t in chunks)


def test_big_table_is_split_and_header_repeats():
    rows = ["Year | Sales"] + [f"{2000 + i} | {i * 100}" for i in range(50)]
    chunks = chunk_section("\n".join(rows), max_chars=200)
    assert len(chunks) > 1
    assert all(kind == "table" for kind, _ in chunks)
    assert all(text.startswith("Year | Sales") for _, text in chunks)


def test_build_chunks_adds_label_and_unique_ids():
    sections = [
        {"title": "Item 1. Business", "text": "Apple designs products."},
        {"title": "Item 2. Properties", "text": "Apple owns facilities."},
    ]
    chunks = build_chunks("AAPL", 2025, sections)
    assert chunks[0]["text"].startswith("[AAPL 10-K FY2025 | Item 1. Business]\n")
    assert chunks[1]["section"] == "Item 2. Properties"
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
