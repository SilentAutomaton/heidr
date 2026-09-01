import pytest

from heidr import llm
from heidr.contracts import Unavailable
from heidr.llm import anthropic, base, ollama, openai_compat

ASK = [llm.Message("system", "read this"), llm.Message("user", "what now")]


class Reply:
    def __init__(self, lines):
        self.lines = lines
        self.sent = None

    def raise_for_status(self):
        return None

    def iter_lines(self):
        return iter(self.lines)


@pytest.fixture
def capture(monkeypatch):
    """Answer requests.post with fixed stream lines and keep what was sent."""
    sent = {}

    def install(module, lines):
        def post(url, **kwargs):
            sent["url"] = url
            sent.update(kwargs)
            return Reply(lines)

        monkeypatch.setattr(module, "requests", type("R", (), {"post": staticmethod(post)}))
        return sent

    return install


def test_ollama_reads_newline_delimited_json(default_config, capture):
    capture(
        ollama,
        [
            b'{"message":{"content":"the "},"done":false}',
            b"",
            b'{"message":{"content":"sky"},"done":false}',
            b'{"message":{"content":""},"done":true}',
            b'{"message":{"content":"never reached"},"done":false}',
        ],
    )
    provider = ollama.Ollama(default_config)

    assert "".join(provider.stream(ASK)) == "the sky"


def test_openai_compatible_reads_server_sent_events(default_config, capture):
    capture(
        openai_compat,
        [
            b'data: {"choices":[{"delta":{"content":"one"}}]}',
            b"",
            b'data: {"choices":[{"delta":{"role":"assistant"}}]}',
            b'data: {"choices":[{"delta":{"content":" two"}}]}',
            b"data: [DONE]",
        ],
    )
    provider = openai_compat.OpenAICompatible(default_config)

    assert "".join(provider.stream(ASK)) == "one two"


def test_openai_compatible_sends_the_key_when_there_is_one(default_config, capture, monkeypatch):
    monkeypatch.setenv("HEIDR_LLM_KEY", "secret-value")
    sent = capture(openai_compat, [b"data: [DONE]"])

    list(openai_compat.OpenAICompatible(default_config).stream(ASK))

    assert sent["headers"]["authorization"] == "Bearer secret-value"


def test_openai_compatible_works_without_a_key(default_config, capture, monkeypatch):
    monkeypatch.delenv("HEIDR_LLM_KEY", raising=False)
    sent = capture(openai_compat, [b"data: [DONE]"])

    list(openai_compat.OpenAICompatible(default_config).stream(ASK))

    assert "authorization" not in sent["headers"]


def test_anthropic_reads_content_block_deltas(default_config, capture, monkeypatch):
    monkeypatch.setenv("HEIDR_LLM_KEY", "secret-value")
    sent = capture(
        anthropic,
        [
            b'data: {"type":"message_start"}',
            b'data: {"type":"content_block_delta","delta":{"text":"a "}}',
            b'data: {"type":"content_block_delta","delta":{"text":"sign"}}',
            b'data: {"type":"message_stop"}',
        ],
    )
    provider = anthropic.Anthropic(default_config)

    assert "".join(provider.stream(ASK)) == "a sign"
    assert sent["json"]["system"] == "read this"
    assert [m["role"] for m in sent["json"]["messages"]] == ["user"]
    assert sent["headers"]["anthropic-version"] == anthropic.VERSION


def test_anthropic_says_which_variable_is_missing(default_config, monkeypatch):
    monkeypatch.delenv("HEIDR_LLM_KEY", raising=False)

    with pytest.raises(Unavailable) as refused:
        list(anthropic.Anthropic(default_config).stream(ASK))

    assert "HEIDR_LLM_KEY" in str(refused.value)


def test_build_returns_the_configured_provider(default_config):
    default_config.set("llm.provider", "openai_compat")
    assert llm.build(default_config).name == "openai_compat"


def test_build_lists_the_choices_when_the_name_is_wrong(default_config):
    default_config.set("llm.provider", "telepathy")

    with pytest.raises(Unavailable) as refused:
        llm.build(default_config)

    assert "ollama" in str(refused.value)


def test_broken_json_in_a_stream_is_skipped():
    lines = [b'data: {"choices":[{"delta":{"content":"kept"}}]}', b"data: {not json", b"noise"]
    assert [p for p in base.sse_payloads(iter(lines))]
