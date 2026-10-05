from ledgerlens.extract_facts import EXTRACT_SYSTEM


def test_extractor_prompt_marks_excerpts_as_untrusted():
    text = EXTRACT_SYSTEM.lower()
    assert "untrusted" in text
    assert "do not follow" in text
