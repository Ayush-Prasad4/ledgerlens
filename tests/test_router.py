from types import SimpleNamespace

import pytest

from ledgerlens import router


def fake_llm(content=None, error=None):
    def create(**kwargs):
        if error is not None:
            raise error
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    completions = SimpleNamespace(create=create)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


@pytest.mark.parametrize(
    "text, expected",
    [
        ('{"route": "calculate"}', "calculate"),
        ('{"route": "lookup"}', "lookup"),
        ('{"route": "banana"}', "lookup"),
        ("not json at all", "lookup"),
        ('["calculate"]', "lookup"),
        ("null", "lookup"),
        (None, "lookup"),
    ],
)
def test_parse_route(text, expected):
    assert router.parse_route(text) == expected


def test_route_question_uses_llm_answer(monkeypatch):
    monkeypatch.setattr(router, "get_llm", lambda: fake_llm(content='{"route": "calculate"}'))
    assert router.route_question("how much did sales grow?") == "calculate"


def test_route_question_falls_back_to_lookup_on_error(monkeypatch):
    monkeypatch.setattr(router, "get_llm", lambda: fake_llm(error=RuntimeError("api down")))
    assert router.route_question("anything") == "lookup"
