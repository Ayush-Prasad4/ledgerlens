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


def test_long_paragraph_is_split_at_sentence_boundaries():
    paragraph = " ".join(f"Sentence number {i} is here." for i in range(200))
    chunks = chunk_section(paragraph, max_chars=300)
    assert len(chunks) > 1
    assert all(len(t) <= 300 for _, t in chunks)
    assert all(t.startswith("Sentence") and t.endswith(".") for _, t in chunks)


def test_heading_stays_with_the_paragraph_below_it():
    heading = "Commitments and contingencies (Note 7)"
    paragraph = " ".join(f"We have commitment number {i}." for i in range(40))
    chunks = chunk_section(f"{heading}\n{paragraph}", max_chars=300)
    assert all(text != heading for _, text in chunks)
    assert chunks[0][1].startswith(heading + "\n")


def test_heading_is_not_left_at_the_end_of_the_previous_chunk():
    intro = "This is an ordinary sentence about the business. " * 5
    heading = "Legal Proceedings"
    paragraph = " ".join(f"A case was filed in year {i}." for i in range(30))
    chunks = chunk_section(f"{intro.strip()}\n{heading}\n{paragraph}", max_chars=300)
    first = chunks[0][1]
    assert not first.endswith(heading)
    assert any(text.startswith(heading) for _, text in chunks)


def test_very_long_table_rows_are_split_below_limit():
    rows = [
        "Description of the Matter | " + "Tax rules are complex. " * 40,
        "How We Addressed the Matter | " + "We tested the controls. " * 40,
    ]
    chunks = chunk_section("\n".join(rows), max_chars=500)
    assert len(chunks) > 2
    assert all(kind == "table" for kind, _ in chunks)
    assert all(len(text) <= 500 for _, text in chunks)


def test_label_row_between_table_rows_stays_inside_the_table():
    text = "\n".join(
        [
            "Cash flows (in millions):",
            "Net income | 30,425 | 59,248",
            "OPERATING ACTIVITIES:",
            "Depreciation | 1,000 | 2,000",
        ]
    )
    chunks = chunk_section(text)
    assert [kind for kind, _ in chunks] == ["table"]
    assert "OPERATING ACTIVITIES:" in chunks[0][1]
