import pytest
from fastapi import HTTPException

from ledgerlens import api


def test_empty_question_is_rejected():
    with pytest.raises(HTTPException) as e:
        api.ask(api.Question(question="   "))
    assert e.value.status_code == 400


def test_ask_returns_agent_output(monkeypatch):
    fake = {"question": "q", "route": "lookup", "answer": "a", "sources": []}
    monkeypatch.setattr(api, "run", lambda q: fake)
    assert api.ask(api.Question(question="q")) == fake


def test_question_is_stripped(monkeypatch):
    seen = []
    monkeypatch.setattr(api, "run", lambda q: seen.append(q) or {})
    api.ask(api.Question(question="  hello  "))
    assert seen == ["hello"]
