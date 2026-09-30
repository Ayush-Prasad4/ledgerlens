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

WITH_CROSS_REFERENCE = """
Item 1. Business
Apple designs products.
Item 7. Management's Discussion
Sales grew. Risks are described in
Item 1A. Risk Factors
of this report. Sales by segment are below.
Item 8. Financial Statements
Numbers go here.
"""


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


def test_cross_reference_does_not_break_a_section():
    sections = extract_sections(WITH_CROSS_REFERENCE)
    titles = [s["title"] for s in sections]
    assert "Item 1A. Risk Factors" not in titles
    item7 = next(s for s in sections if s["title"].startswith("Item 7"))
    assert "Sales by segment are below." in item7["text"]
