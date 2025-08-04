from typing import TypedDict

from openai import AsyncOpenAI

from settings import OPENAI_API_KEY

MODEL_NAME = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "You are an assistant that groups messages by topic and responds in JSON. "
    "Return only a JSON array where each item has 'text' with a short summary "
    "and 'links' containing the message links it references."
)


class SummaryItem(TypedDict):
    text: str
    links: list[str]


client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def summarize_messages(
    messages: list[tuple[str, str]],
) -> list[SummaryItem]:
    """Сгруппировать сообщения по темам и вернуть краткое резюме.

    :param messages: Список кортежей ``(text, link)``.
    :return: Список словарей ``{"text": str, "links": list[str]}``.
    """

    if not messages:
        return []

    prompt = "\n".join(
        f"[{idx}] {text}\nLink: {link}"
        for idx, (text, link) in enumerate(messages, start=1)
    )

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Messages:\n{prompt}"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "topics",
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "links": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["text", "links"],
                        "additionalProperties": False,
                    },
                },
            },
        },
    )

    return response.choices[0].message.parsed
