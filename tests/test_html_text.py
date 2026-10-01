from ledgerlens.processor import html_to_text, process_filing

MSFT_STYLE_HTML = """
<html><body>
<div>Table of Contents</div>
<table>
  <tr><td>Item 1.</td><td>Business</td><td>3</td></tr>
  <tr><td>Item 7.</td><td>Management Discussion</td><td>40</td></tr>
</table>
<div><span>ITEM 1. B</span><span>USINESS</span></div>
<div>Item 1</div>
<div>We build software and cloud services for people around the world every day.</div>
<div>36</div>
<div>PART II</div>
<div>Item 1</div>
<div>Competition is intense in every market where we operate our business today.</div>
<div><span>ITEM 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF</span></div>
<div>FINANCIAL CONDITION AND RESULTS OF OPERATIONS</div>
<div>Item 7</div>
<div>Industry Trends</div>
<div>Cloud demand grew a lot this year across all of our customer segments.</div>
<div>Item 7</div>
<div>RECENT ACCOUNTING GUIDANCE</div>
<div>Accounting rules changed during the year and we adopted them early.</div>
</body></html>
"""


def test_inline_spans_do_not_split_words(tmp_path):
    path = tmp_path / "f.html"
    path.write_text("<div><span>ITEM 1. B</span><span>USINESS</span></div><div>Next</div>")
    assert html_to_text(path).splitlines() == ["ITEM 1. BUSINESS", "Next"]


def test_page_numbers_and_table_of_contents_lines_are_dropped(tmp_path):
    path = tmp_path / "f.html"
    path.write_text("<div>Hello</div><div>36</div><div>Table of Contents</div><div>PART II</div>")
    assert html_to_text(path) == "Hello"


def test_microsoft_style_filing_gets_clean_official_sections(tmp_path):
    path = tmp_path / "f.html"
    path.write_text(MSFT_STYLE_HTML, encoding="utf-8")

    sections = process_filing(path)

    assert [s["title"] for s in sections] == [
        "Item 1. Business",
        "Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations",
    ]
    item1 = sections[0]["text"].splitlines()
    assert item1 == [
        "We build software and cloud services for people around the world every day.",
        "Competition is intense in every market where we operate our business today.",
    ]
    item7 = sections[1]["text"].splitlines()
    assert item7[0] == "Industry Trends"
    assert "Item 7" not in item7
    assert "FINANCIAL CONDITION AND RESULTS OF OPERATIONS" not in item7
