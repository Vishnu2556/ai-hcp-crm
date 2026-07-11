import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# gemma2-9b-it: fast + cheap, used for the conversational agent loop
# (entity extraction, tool routing, chat replies)
CHAT_MODEL = "llama-3.1-8b-instant"

# llama-3.3-70b-versatile: heavier reasoning, used sparingly for
# things like nuanced sentiment/summary passes where quality > latency
REASONING_MODEL = "llama-3.3-70b-versatile"

_client = Groq(api_key=GROQ_API_KEY)


def get_groq_client() -> Groq:
    return _client


def chat_completion(messages, model: str = CHAT_MODEL, temperature: float = 0.2,
                     max_tokens: int = 1024, response_format: str | None = None):
    """
    Thin wrapper so the rest of the codebase never talks to the Groq SDK
    directly. `response_format="json_object"` is used when we need
    structured extraction (entities, sentiment) back from the LLM.
    """
    kwargs = dict(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}

    completion = _client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content