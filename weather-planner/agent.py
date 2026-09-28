"""
A day planner that checks the forecast before suggesting a plan. Built the way a
Strands agent is built, with a tool and a model, and a stub model in place of a
real one that streams its tool call as it forms and its answer word by word.

What it shows:
- A tool call, `get_forecast`, whose arguments stream in pieces.
- A tool that fails for a city it has no forecast for, reported as an error result,
  and the agent recovering from it.
- A streamed answer around the tool call.
"""

import asyncio
import json
import pathlib
import re
from collections.abc import AsyncIterable
from typing import Any

from strands import Agent, tool
from strands.models.model import Model

TOKEN_PAUSE_S = 0.04
FORECASTS = json.loads((pathlib.Path(__file__).parent / "forecasts.json").read_text())


@tool
def get_forecast(city: str) -> str:
    """Tomorrow's forecast for a city."""
    forecast = FORECASTS.get(city.lower())
    if forecast is None:
        raise ValueError(f"No forecast is available for {city}.")
    return json.dumps(forecast)


def plan(city: str, forecast: dict[str, Any]) -> str:
    if forecast["sky"] == "sunny":
        return (f"Tomorrow in {city} will be sunny with a high of {forecast['high_c']}°C and {forecast['wind']} wind. "
                "A good beach day: go in the afternoon and take sunscreen.")
    return (f"Tomorrow in {city} brings {forecast['sky']}, {forecast['high_c']}°C and {forecast['wind']} wind. "
            "Plan something indoors: a museum in the morning and a long lunch.")


class StubModel(Model):
    """Checks the forecast for the city in the question, then plans around it."""

    def update_config(self, **model_config: Any) -> None:
        return None

    def get_config(self) -> dict[str, Any]:
        return {"model_id": "stub"}

    async def structured_output(self, output_model: Any, prompt: Any, system_prompt: Any = None, **kwargs: Any) -> AsyncIterable[dict[str, Any]]:
        yield {"output": output_model()}

    async def _say(self, text: str) -> AsyncIterable[dict[str, Any]]:
        yield {"contentBlockStart": {"start": {}}}
        for index, word in enumerate(text.split(" ")):
            await asyncio.sleep(TOKEN_PAUSE_S)
            yield {"contentBlockDelta": {"delta": {"text": word if index == 0 else f" {word}"}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}

    async def stream(self, messages: Any, tool_specs: Any = None, system_prompt: Any = None, **kwargs: Any) -> AsyncIterable[dict[str, Any]]:
        # A Strands agent keeps its conversation, so the question is the latest one
        # the user asked, not the first.
        question = next(block["text"] for message in reversed(messages) if message["role"] == "user"
                        for block in message["content"] if "text" in block)
        if question.strip().lower() == "raise":
            raise ValueError("the agent was asked to raise")
        results = [block["toolResult"] for block in messages[-1]["content"] if "toolResult" in block]
        city_match = re.search(r"\bin ([A-Z][a-z]+)", question)
        yield {"messageStart": {"role": "assistant"}}
        if city_match is None:
            async for event in self._say("Which city are you planning for?"):
                yield event
        elif not results:
            city = city_match.group(1)
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "call_forecast", "name": "get_forecast"}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": '{"city": '}}}}
            await asyncio.sleep(TOKEN_PAUSE_S)
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": f'"{city}"}}'}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            city = city_match.group(1)
            result = results[0]
            if result["status"] == "error":
                text = f"I do not have a forecast for {city}, so I cannot plan around the weather there yet."
            else:
                text = plan(city, json.loads(result["content"][0]["text"]))
            async for event in self._say(text):
                yield event
        yield {"metadata": {"usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2}, "metrics": {"latencyMs": 0}}}


agent = Agent(
    model=StubModel(),
    tools=[get_forecast],
    system_prompt="Check the forecast with get_forecast, then suggest a plan for the day.",
    callback_handler=None,
)
