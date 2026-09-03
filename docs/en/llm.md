# Language model providers

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/llm.md)

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
think = false
```

`think` is read by the ollama provider only. A reasoning model asked to read a
wall of random letters can spend its whole output budget on reasoning and stop
with an empty answer, which reaches the screen as material and nothing else.
The default is `false`, so the model answers at once. Set it to `true` only
with a model and a context length that can afford it.

| Key | Default | What it is for |
|---|---|---|
| `temperature` | 0.8 | The answers want variety more than accuracy |
| `top_p` | 0.9 | The usual companion to the temperature |
| `repeat_penalty` | 1.1 | A model reading noise is prone to looping |
| `context_tokens` | 8192 | `num_ctx`. Too small and the server truncates the material without saying so |
| `max_tokens` | 400 | `num_predict`. The longest answer worth waiting for |
| `keep_alive` | `10m` | ollama only. A nine billion parameter model takes six seconds to load, and used to reload for every run |
| `fragment_chars` | 1200 | How much of the found material the model is shown |

Before this, no options were sent at all and the server's own defaults decided
everything, including a context window too small for a page of found material.
An OpenAI shaped service gets `temperature`, `top_p` and `max_tokens`, which is
all its API has; the rest are ollama's own.

The reading that uses all of this is [pythia](modules/pythia.md).

`api_key_env` is the **name of an environment variable**, not a key. Keys are
never read from the config file and never written to it.

## When a provider cannot be built

A misspelled provider name, or a hosted service with no key in the environment,
does not fail in the middle of a run. The `llm` capability is dropped at probe
time instead, so every reading that needs a model is left out of the choice and
`:checkhealth` says what is missing. The program keeps working with the readings
that need nothing.

## How the reading is asked for

Two things about the prompt are worth writing down, because both were wrong once
and the answers showed it.

**It asks for a reading, not an audit.** The prompt used to say "use only what is
in the fragment, do not invent". Handed a wall of random bytes, an honest model
then answered that the fragment contains no usable information. Correct, and
useless. An augur reading entrails knows they are entrails. The prompt now says
where the fragment came from, that it was written for nobody, and asks for one or
two concrete things noticed in it and what they mean for the question. Saying
that the fragment is random or insufficient is forbidden outright.

**It asks for the language of the question.** A Russian question was coming back
answered in English, because the whole prompt is in English and a model follows
what it reads. The question is now repeated as the last line of the message, with
the instruction attached to it: a model follows the last thing it read.

The answer arrives as a stream of fragments a few characters long, and a reading
yields lines, so `llm.base.lines` puts them back together. Without that, the
answer reached the screen one word per line.

## The rule that outranks all of this

**The model interprets the material. It never selects it.** A reading passes the
found material to the model and streams back what comes out. It does not ask the
model which page to open, which frequency to listen to, or which of several
findings to prefer. The moment a model chooses, the answer is generated rather
than found, and the program stops being what it claims to be.

## Dependencies

`requests`. Network access to whatever the provider points at, which for ollama
and llama.cpp means localhost.
