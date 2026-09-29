"""
A refund desk that asks a person before it refunds anything.

The model looks the order up with a tool, then the `approve` node pauses the run
with `interrupt()`: what to ask, and the shape of the answer as a JSON Schema. The
run ends there, and Onecortex reports it as an `interrupt` event. The next call on
the same session carries the answer as a `resume`, and the graph continues from
`approve` rather than starting again:

- `{"approve": true, "note": "..."}` refunds;
- `{"approve": false}` declines;
- a cancelled resume reaches the graph as None, and cancels.

The pause is kept by the checkpointer compiled in below, keyed by the session.
In-memory is enough while the session lives; a pause that must survive longer
needs a durable checkpointer, such as Postgres.

A scripted model stands in for a real one, so every answer is exact.
"""

import json
import re
import time
from collections.abc import Iterator
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.tools import ToolException, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt
from typing_extensions import Annotated, TypedDict

TOKEN_PAUSE_S = 0.04

ORDERS = {
    "1042": {"item": "a desk lamp", "paid": "40.00 EUR"},
    "1043": {"item": "two mugs", "paid": "18.50 EUR"},
}

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "approve": {"type": "boolean", "description": "Refund the order"},
        "note": {"type": "string", "description": "A note for the customer"},
    },
    "required": ["approve"],
}


@tool
def lookup_order(order_id: str) -> str:
    """Looks up an order by its four digit number."""
    order = ORDERS.get(order_id)
    if order is None:
        raise ToolException(f"No order {order_id} exists.")
    return json.dumps(order)


def order_number(messages: list[BaseMessage]) -> str | None:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            found = re.search(r"\b(\d{4})\b", str(message.content))
            if found:
                return found.group(1)
    return None


def words(text: str) -> list[AIMessageChunk]:
    return [AIMessageChunk(content=word if i == 0 else f" {word}") for i, word in enumerate(text.split(" "))]


class ScriptedModel(BaseChatModel):
    """Looks up the order the customer named, or asks which one."""

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def _chunks(self, messages: list[BaseMessage]) -> list[AIMessageChunk]:
        order_id = order_number(messages)
        if order_id is None:
            return words("Which order should I refund? Give me the four digit number from your confirmation email.")
        return [
            AIMessageChunk(content="", tool_call_chunks=[
                {"name": "lookup_order", "args": '{"order_id": ', "id": "call_lookup", "index": 0},
            ]),
            AIMessageChunk(content="", tool_call_chunks=[
                {"name": None, "args": f'"{order_id}"}}', "id": None, "index": 0},
            ]),
        ]

    def _stream(self, messages: list[BaseMessage], stop: Any = None, run_manager: Any = None, **kwargs: Any) -> Iterator[ChatGenerationChunk]:
        for chunk in self._chunks(messages):
            time.sleep(TOKEN_PAUSE_S)
            yield ChatGenerationChunk(message=chunk)

    def _generate(self, messages: list[BaseMessage], stop: Any = None, run_manager: Any = None, **kwargs: Any) -> ChatResult:
        chunks = self._chunks(messages)
        whole = chunks[0]
        for chunk in chunks[1:]:
            whole = whole + chunk
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=whole.content, tool_calls=whole.tool_calls))])


class State(TypedDict):
    messages: Annotated[list, add_messages]


def agent(state: State) -> dict:
    if str(state["messages"][-1].content).strip() == "raise":
        raise ValueError("the agent was asked to raise")
    return {"messages": [ScriptedModel().invoke(state["messages"])]}


def approve(state: State) -> dict:
    """Asks a person, then refunds, declines or cancels on their answer."""
    lookup = state["messages"][-1]
    order_id = order_number(state["messages"])
    if not isinstance(lookup, ToolMessage) or lookup.status == "error":
        return {"messages": [AIMessage(content=f"I could not find order {order_id}. Check the number on your confirmation email.")]}
    order = json.loads(str(lookup.content))
    answer = interrupt({
        "reason": "approval",
        "message": f"Refund {order['paid']} for order {order_id} ({order['item']}) to the original payment method?",
        "responseSchema": ANSWER_SCHEMA,
    })
    if answer is None:
        text = f"Refund for order {order_id} cancelled. Nothing was refunded."
    elif isinstance(answer, dict) and answer.get("approve") is True:
        text = f"Refunded {order['paid']} for order {order_id}. Reference RF-{order_id}."
        if answer.get("note"):
            text += f" Note for the customer: {answer['note']}"
    else:
        text = f"Refund for order {order_id} declined. Nothing was refunded."
    return {"messages": [AIMessage(content=text)]}


builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode([lookup_order], handle_tool_errors=True))
builder.add_node("approve", approve)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
builder.add_edge("tools", "approve")
builder.add_edge("approve", END)

graph = builder.compile(checkpointer=InMemorySaver())
