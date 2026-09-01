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


def test_ollama_keeps_a_reasoning_model_quiet_by_default(default_config, capture):
    """A model that thinks over a wall of noise answers with nothing at all."""
    sent = capture(ollama, [b'{"message":{"content":"here"},"done":true}'])
    list(ollama.Ollama(default_config).stream(ASK))

    assert sent["json"]["think"] is False


def test_ollama_thinks_when_the_configuration_asks_for_it(default_config, capture):
    sent = capture(ollama, [b'{"message":{"content":"here"},"done":true}'])
    default_config.set("llm.think", True)
    list(ollama.Ollama(default_config).stream(ASK))

    assert sent["json"]["think"] is True


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


def test_a_daemon_that_is_not_listening_is_not_available(default_config):
    default_config.set("llm.base_url", "http://127.0.0.1:1")
    assert ollama.Ollama(default_config).available() is False


def test_a_hosted_service_needs_a_key_to_count(default_config, monkeypatch):
    default_config.set("llm.base_url", "https://api.groq.com/openai")
    monkeypatch.delenv("HEIDR_LLM_KEY", raising=False)
    assert openai_compat.OpenAICompatible(default_config).available() is False

    monkeypatch.setenv("HEIDR_LLM_KEY", "secret-value")
    assert openai_compat.OpenAICompatible(default_config).available() is True


def test_anthropic_counts_only_with_a_key(default_config, monkeypatch):
    monkeypatch.delenv("HEIDR_LLM_KEY", raising=False)
    assert anthropic.Anthropic(default_config).available() is False


# A stream of fragments is not a list of lines


def test_fragments_become_one_line():
    pieces = iter(["Eat what ", "you did not ", "choose.\n"])

    assert list(base.lines(pieces)) == ["Eat what you did not choose."]


def test_a_break_inside_a_fragment_splits_it():
    assert list(base.lines(iter(["one\ntwo\nthr", "ee"]))) == ["one", "two", "three"]


def test_the_tail_without_a_break_still_arrives():
    assert list(base.lines(iter(["no break at all"]))) == ["no break at all"]


def test_a_stream_of_nothing_yields_nothing():
    assert list(base.lines(iter(["   ", "\n"]))) == ["   "]


@pytest.mark.asyncio
async def test_the_reading_gives_the_screen_lines_not_words(default_config, stub_context):
    from heidr.contracts import Material
    from heidr.reading import pythia

    class Chatty:
        name = "fake"

        def stream(self, messages):
            yield from ["Eat what ", "you did not ", "choose.\n", "The first ", "thought.\n"]

    stub_context.llm = Chatty()
    scoped = stub_context.for_module("pythia", {})
    scoped.llm = Chatty()
    said = list(pythia.run(scoped, "what now", Material("found", source="fake")))

    assert said == ["Eat what you did not choose.", "The first thought."]


# What the model is told about its own sampling


def test_ollama_sends_the_sampling_settings(default_config, capture):
    sent = capture(ollama, [b'{"message":{"content":"here"},"done":true}'])
    default_config.set("llm.temperature", 0.5)
    default_config.set("llm.context_tokens", 4096)
    list(ollama.Ollama(default_config).stream(ASK))

    assert sent["json"]["options"]["temperature"] == 0.5
    assert sent["json"]["options"]["num_ctx"] == 4096
    assert sent["json"]["options"]["num_predict"] == 400
    assert sent["json"]["keep_alive"] == "10m"


def test_an_openai_shape_gets_only_what_it_understands(default_config, capture):
    sent = capture(openai_compat, [b'data: {"choices":[{"delta":{"content":"x"}}]}'])
    list(openai_compat.OpenAICompatible(default_config).stream(ASK))

    assert sent["json"]["temperature"] == 0.8
    assert sent["json"]["max_tokens"] == 400
    assert "options" not in sent["json"]


def test_the_defaults_are_the_ones_the_settings_list_shows(default_config):
    for key, value in base.DEFAULTS.items():
        assert default_config.get(f"llm.{key}") == value
