from ledgerlens.processor import html_to_text

TABLE_HTML = """
<html><body>
<p>Net sales by reportable segment (dollars in millions):</p>
<table>
  <tr><td></td><td>2025</td><td>Change</td><td>2024</td></tr>
  <tr><td>Americas</td><td>$</td><td>178,353</td><td>7</td><td>%</td><td>$</td><td>167,045</td></tr>
  <tr><td>Greater China</td><td>64,377</td><td>(4</td><td>)</td><td>%</td><td>66,952</td></tr>
</table>
<p>Americas net sales increased.</p>
</body></html>
"""


def test_table_rows_stay_on_one_line(tmp_path):
    path = tmp_path / "filing.html"
    path.write_text(TABLE_HTML, encoding="utf-8")

    text = html_to_text(path)

    assert "2025 | Change | 2024" in text
    assert "Americas | $178,353 | 7% | $167,045" in text
    assert "Greater China | 64,377 | (4)% | 66,952" in text
    assert "Americas net sales increased." in text
