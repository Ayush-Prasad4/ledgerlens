from pathlib import Path

from ledgerlens.processor import extract_sections, html_to_text


def test_html_to_text_removes_scripts(tmp_path: Path):
    html = """
    <html>
        <body>
            <script>bad_code()</script>
            <h1>Item 1. Business</h1>
            <p>Apple designs products.</p>
        </body>
    </html>
    """

    file = tmp_path / "test.html"
    file.write_text(html, encoding="utf-8")

    text = html_to_text(file)

    assert "bad_code" not in text
    assert "Apple designs products." in text


def test_extract_sections():
    text = """
    Item 1. Business
    Apple designs products.

    Item 1A. Risk Factors
    Competition is a risk.

    Item 2. Properties
    Apple owns facilities.
    """

    sections = extract_sections(text)

    assert len(sections) == 3
    assert sections[0]["title"] == "Item 1. Business"
    assert sections[1]["title"] == "Item 1A. Risk Factors"
    assert "Competition is a risk." in sections[1]["text"]
