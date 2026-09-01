# Language model providers

A reading may want a model to interpret what was found. Which model, and where
it runs, is one line of configuration.

## The contract

Every provider is one class with one method:

```python
def stream(self, messages: list[Message]) -> Iterator[str]
```

It yields text as it arrives. Nothing buffers a whole answer, which is why the
interpretation appears on screen word by word rather than in one lump at the
end.

## What ships

| `llm.provider` | Talks to | Notes |
|---|---|---|
| `ollama` | a local ollama daemon | `POST /api/chat`, newline delimited JSON |
| `openai_compat` | anything speaking `/v1/chat/completions` | the llama.cpp server, OpenAI, and the hosted services that copied its shape |
| `anthropic` | the Anthropic messages API | the system prompt travels in its own field, not as a message |

Choosing between a llama.cpp server and a hosted service is the same edit:
change `base_url` and `model`.

## Configuration

```toml
[llm]
provider = "ollama"
model = "qwen3.5:9B"
base_url = "http://localhost:11434"
api_key_env = "HEIDR_LLM_KEY"
timeout = 120
max_tokens = 1024
```

`api_key_env` is the **name of an environment variable**, not a key. Keys are
never read from the config file and never written to it.

## When a provider cannot be built

A misspelled provider name, or a hosted service with no key in the environment,
does not fail in the middle of a rite. The `llm` capability is dropped at probe
time instead, so every reading that needs a model quietly leaves the lottery and
`:checkhealth` says what is missing. The oracle keeps working with the readings
that need nothing.

## The rule that outranks all of this

**The model interprets the material. It never selects it.** A reading passes the
found material to the model and streams back what comes out. It does not ask the
model which page to open, which frequency to listen to, or which of several
findings to prefer. The moment a model chooses, the answer is generated rather
than found, and the program is no longer an oracle.

## Dependencies

`requests`. Network access to whatever the provider points at — which for
ollama and llama.cpp means localhost.
