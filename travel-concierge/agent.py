"""
A travel concierge: a triage agent that hands flight requests to a booking agent,
which searches flights and answers with the cheapest one. Built the way an OpenAI
Agents SDK app is built, with a handoff and a function tool, and the SDK's own
scripted model in place of a real one.

What it shows:
- A handoff: the run moves from Triage to Booking, and each is a step.
- A tool call, `search_flights`, with arguments and a result.
- What the caller sent, read from the run context: send `"currency": "EUR"` and
  prices are converted.
"""

import json
import pathlib
import re
from typing import Any

from agents import Agent, ModelResponse, RunContextWrapper, function_tool, set_tracing_disabled
from agents.testing import ScriptedModel, assistant_message, function_call

# Traces go to the model provider by default, which for an agent that never leaves
# the process means a key and a network call to report that nothing happened.
set_tracing_disabled(True)

FLIGHTS = json.loads((pathlib.Path(__file__).parent / "flights.json").read_text())
RATES = {"GBP": 1.0, "EUR": 1.17, "USD": 1.27}
SYMBOLS = {"GBP": "£", "EUR": "€", "USD": "$"}


@function_tool
def search_flights(ctx: RunContextWrapper[Any], origin: str, destination: str, date: str) -> str:
    """Searches direct flights between two cities on a date, cheapest first."""
    params = (ctx.context or {}).get("onecortex", {}).get("params", {})
    currency = str(params.get("currency", "GBP")).upper()
    rate = RATES.get(currency, 1.0)
    found = FLIGHTS.get(f"{origin.lower()}-{destination.lower()}", [])
    return json.dumps({
        "date": date,
        "currency": currency if currency in RATES else "GBP",
        "flights": [
            {**{k: v for k, v in f.items() if k != "price_gbp"}, "price": round(f["price_gbp"] * rate)}
            for f in sorted(found, key=lambda f: f["price_gbp"])
        ],
    })


def conversation(items: Any) -> list[dict[str, Any]]:
    return items if isinstance(items, list) else [{"role": "user", "content": items}]


def question(items: list[dict[str, Any]]) -> str:
    return next(str(item["content"]) for item in items if isinstance(item, dict) and item.get("role") == "user")


class TriageModel(ScriptedModel):
    """Hands anything about flights to Booking, and answers the rest itself."""

    def _next(self, items: list[dict[str, Any]]) -> None:
        text = question(items)
        if text.strip().lower() == "raise":
            raise ValueError("the agent was asked to raise")
        if "flight" in text.lower():
            self.enqueue([function_call("transfer_to_booking", "{}", call_id="call_handoff")])
        else:
            self.enqueue([assistant_message("I can find and compare flights for you. Tell me where from, where to, and when.")])

    async def get_response(self, system_instructions: Any, input: Any, *args: Any, **kwargs: Any) -> ModelResponse:
        self._next(conversation(input))
        return await super().get_response(system_instructions, input, *args, **kwargs)

    async def stream_response(self, system_instructions: Any, input: Any, *args: Any, **kwargs: Any) -> Any:
        self._next(conversation(input))
        async for event in super().stream_response(system_instructions, input, *args, **kwargs):
            yield event


class BookingModel(TriageModel):
    """Searches the route in the question, then recommends the cheapest flight."""

    def _next(self, items: list[dict[str, Any]]) -> None:
        results = [i for i in items if isinstance(i, dict) and i.get("type") == "function_call_output" and i.get("call_id") == "call_search"]
        text = question(items)
        route = re.search(r"from (\w+) to (\w+)", text, re.IGNORECASE)
        if not results:
            if route is None:
                self.enqueue([assistant_message("Which cities are you flying between?")])
                return
            date = re.search(r"on (\d{1,2} \w+)", text)
            args = {"origin": route.group(1), "destination": route.group(2), "date": date.group(1) if date else "the next available day"}
            self.enqueue([function_call("search_flights", json.dumps(args), call_id="call_search")])
            return
        found = json.loads(results[-1]["output"])
        origin, destination = route.group(1).title(), route.group(2).title()  # type: ignore[union-attr]
        if not found["flights"]:
            self.enqueue([assistant_message(f"There are no direct flights from {origin} to {destination} on {found['date']}.")])
            return
        best = found["flights"][0]
        symbol = SYMBOLS[found["currency"]]
        self.enqueue([assistant_message(
            f"The cheapest direct flight from {origin} to {destination} on {found['date']} is {best['flight']}, "
            f"leaving at {best['departs']} and landing at {best['arrives']}, for {symbol}{best['price']}."
        )])


booking = Agent(
    name="Booking",
    instructions="Search flights with search_flights and recommend the cheapest.",
    model=BookingModel(),
    tools=[search_flights],
)

agent = Agent(
    name="Triage",
    instructions="Hand flight requests to Booking. Answer anything else briefly.",
    model=TriageModel(),
    handoffs=[booking],
)
