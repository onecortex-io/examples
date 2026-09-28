"""
A customer support triage graph: classify the message, look the order up when it
is about one, and answer. Built the way a LangGraph agent is built, with a model
node, a tool node and a checkpointer, and a scripted model in place of a real one.

The scripted model streams its tool call in pieces and its answer token by token,
with a short pause, so the stream looks like a real model's. It never leaves the
process and every answer is exact.

What it shows:
- Each node is a step: classify, agent, tools, agent again.
- The model's tool call, and a failed lookup coming back as an error result.
- Memory within a session, from the builder's own checkpointer: say "my order is
  1042", then ask "when will it arrive?".
- What the caller sent, read from `config["configurable"]["onecortex"]`: send
  `"model": "..."` and the answer says which model answered.
"""

import json
import re
import time
from collections.abc import Iterator
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ToolException, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import Annotated, TypedDict

TOKEN_PAUSE_S = 0.04

ORDERS = {
    "1042": {"status": "shipped", "carrier": "DHL", "shipped_on": "24 September", "arrives_on": "28 September"},
    "1043": {"status": "processing", "ready_by": "27 September"},
}


@tool
def lookup_order(order_id: str) -> str:
    """Looks up an order by its four digit number."""
    order = ORDERS.get(order_id)
    if order is None:
        raise ToolException(f"No order {order_id} exists.")
    return json.dumps(order)


def order_number(messages: list[BaseMessage]) -> str | None:
    """The most recent order number the customer mentioned, in this message or an earlier one."""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            found = re.search(r"\b(\d{4})\b", str(message.content))
            if found:
                return found.group(1)
    return None


def answer_from(result: ToolMessage, order_id: str) -> str:
    if result.status == "error":
        return f"I could not find order {order_id}. Check the number on your confirmation email."
    order = json.loads(str(result.content))
    if order["status"] == "shipped":
        return (f"Order {order_id} shipped with {order['carrier']} on {order['shipped_on']} "
                f"and should arrive on {order['arrives_on']}.")
    return f"Order {order_id} is still being packed and will be ready to ship by {order['ready_by']}."


class ScriptedModel(BaseChatModel):
    """Calls lookup_order for the order in question, then answers from what it returned."""

    model_name: str = "scripted"

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def _chunks(self, messages: list[BaseMessage]) -> list[AIMessageChunk]:
        last = messages[-1]
        order_id = order_number(messages)
        if isinstance(last, ToolMessage) and order_id is not None:
            text = answer_from(last, order_id)
            if self.model_name != "scripted":
                text += f" (answered by {self.model_name})"
            words = text.split(" ")
            return [AIMessageChunk(content=word if i == 0 else f" {word}") for i, word in enumerate(words)]
        if order_id is None:
            text = "Which order do you mean? Give me the four digit number from your confirmation email."
            return [AIMessageChunk(content=word if i == 0 else f" {word}") for i, word in enumerate(text.split(" "))]
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
    intent: str


def classify(state: State) -> dict:
    """Decides what the message is about. A real graph would ask a model; keywords are enough here."""
    text = str(state["messages"][-1].content).lower()
    if text.strip() == "raise":
        raise ValueError("the agent was asked to raise")
    if "refund" in text:
        return {"intent": "refund"}
    if re.search(r"\b\d{4}\b", text) or any(word in text for word in ("order", "parcel", "arrive", "deliver", "shipped")):
        return {"intent": "order"}
    return {"intent": "other"}


def agent(state: State, config: RunnableConfig) -> dict:
    """Asks the model, which is whichever one the caller named, if they named one."""
    params = config.get("configurable", {}).get("onecortex", {}).get("params", {})
    # A real model is given the tools with bind_tools; the scripted one knows its only tool.
    model = ScriptedModel(model_name=str(params.get("model", "scripted")))
    return {"messages": [model.invoke(state["messages"])]}


def respond(state: State) -> dict:
    """Everything that is not about an order gets a fixed answer, the way a policy node would."""
    if state["intent"] == "refund":
        text = "Refunds go back to the original payment method within five working days of the return arriving."
    else:
        text = "I can help with orders and refunds. Tell me your order number or ask about a refund."
    return {"messages": [AIMessage(content=text)]}


builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode([lookup_order]))
builder.add_node("respond", respond)
builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", lambda state: "agent" if state["intent"] == "order" else "respond")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
builder.add_edge("respond", END)

graph = builder.compile(checkpointer=InMemorySaver())
