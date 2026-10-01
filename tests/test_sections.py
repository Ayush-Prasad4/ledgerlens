from ledgerlens.processor import extract_sections

TOC_WITH_PIPES = """
Table of Contents
Item 1. | Business | 3
Item 1A. | Risk Factors | 9
Item 2. | Properties | 24
ITEM 1.
BUSINESS
We build search products.
ITEM 1A.
RISK FACTORS
Competition is intense.
ITEM 2.
PROPERTIES
We own offices.
"""

TOC_WITHOUT_PIPES = """
Item 1.
Business
3
Item 1A.
Risk Factors
9
Item 2.
Properties
24
Item 1. Business
We build social apps.
Item 1A. Risk Factors
Privacy rules may change.
Item 2. Properties
We lease data centers.
"""

HEADINGS_AS_TABLE_ROWS = """
Item 1. | Business | 3
Item 1A. | Risk Factors | 9
Item 2. | Properties | 24
Item 1. | Business
We sell books and cloud services.
Item 1A. | Risk Factors
Our business is competitive.
Item 2. | Properties
We lease warehouses.
"""

WITH_CROSS_REFERENCE = """
Item 1. Business
Apple designs products.
Item 1A. Risk Factors
Competition is intense.
Item 7. Management's Discussion
Sales grew. Risks are described in
Item 1A. Risk Factors
of this report. Sales by segment are below.
Item 8. Financial Statements
Numbers go here.
"""

LONG_FRONT_MATTER = (
    """
Item 1.
Business
3
Item 2.
Properties
24
"""
    + "Forward-looking statements matter. " * 20
    + """
Item 1. Business
"""
    + "We build many products and sell them worldwide. " * 40
    + """
Item 2. Properties
"""
    + "We own and lease offices. " * 30
)


def test_toc_with_pipes_is_ignored_and_split_title_is_joined():
    sections = extract_sections(TOC_WITH_PIPES)
    assert [s["title"] for s in sections] == [
        "Item 1. BUSINESS",
        "Item 1A. RISK FACTORS",
        "Item 2. PROPERTIES",
    ]
    assert sections[0]["text"] == "We build search products."


def test_toc_without_pipes_is_ignored_too():
    sections = extract_sections(TOC_WITHOUT_PIPES)
    assert [s["title"] for s in sections] == [
        "Item 1. Business",
        "Item 1A. Risk Factors",
        "Item 2. Properties",
    ]
    assert sections[1]["text"] == "Privacy rules may change."


def test_headings_that_are_table_rows_are_found():
    sections = extract_sections(HEADINGS_AS_TABLE_ROWS)
    assert [s["title"] for s in sections] == [
        "Item 1. Business",
        "Item 1A. Risk Factors",
        "Item 2. Properties",
    ]
    assert sections[2]["text"] == "We lease warehouses."


def test_cross_reference_does_not_break_a_section():
    sections = extract_sections(WITH_CROSS_REFERENCE)
    titles = [s["title"] for s in sections]
    assert titles == [
        "Item 1. Business",
        "Item 1A. Risk Factors",
        "Item 7. Management's Discussion",
        "Item 8. Financial Statements",
    ]
    item7 = sections[2]
    assert "Sales by segment are below." in item7["text"]


def test_text_between_toc_and_first_item_does_not_steal_a_section():
    sections = extract_sections(LONG_FRONT_MATTER)
    assert [s["title"] for s in sections] == ["Item 1. Business", "Item 2. Properties"]
    assert sections[1]["text"].startswith("We own and lease offices.")
