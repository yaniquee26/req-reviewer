import pytest
import requests

from req_reviewer.llm import LLMError, OllamaClient


class FakeResponse:
    def __init__(self, status=200, data=None):
        self.status_code = status
        self._data = data or {"message": {"content": " ответ "}}

    def json(self):
        return self._data


def test_payload_contains_temperature_and_seed(monkeypatch):
    sent = {}

    def fake_post(url, json, timeout):
        sent.update(json)
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    answer = OllamaClient(temperature=0.0, seed=42).chat("sys", "usr")
    assert answer == "ответ"
    assert sent["options"]["temperature"] == 0.0
    assert sent["options"]["seed"] == 42


def test_no_seed_by_default(monkeypatch):
    sent = {}

    def fake_post(url, json, timeout):
        sent.update(json)
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    OllamaClient().chat("sys", "usr")
    assert "seed" not in sent["options"]


def test_model_not_found_hint(monkeypatch):
    monkeypatch.setattr(
        requests, "post", lambda url, json, timeout: FakeResponse(status=404)
    )
    with pytest.raises(LLMError, match="ollama pull"):
        OllamaClient(model="nope").chat("s", "u")


def test_connection_error_is_wrapped(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(LLMError, match="не отвечает"):
        OllamaClient().chat("s", "u")