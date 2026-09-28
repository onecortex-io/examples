"""
An expense assistant that converts what you paid into your home currency. Built
the way a pre-LangGraph LangChain agent is built: a tool calling agent run by an
AgentExecutor, with a scripted chat model in place of a real one.

What it shows:
- A tool call, `convert_currency`, with its arguments and result.
- The AgentExecutor's own error handling: a currency with no rate raises in the
  tool, the executor hands the error back to the model as the tool's answer, and
  the model explains. It reaches the stream as an ordinary result, because that is
  what the executor made of it.
- What it cannot show: the caller's params. An AgentExecutor passes its tools and
  model only callbacks, never the run's `configurable`, so what a caller sends
  stops at the executor. An agent that needs it is a LangGraph graph.
"""

import json
import re
from typing import Any

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import ToolException, tool

RATES_TO_GBP = {"GBP": 1.0, "USD": 0.7874, "EUR": 0.8547, "JPY": 0.0053}
SYMBOLS = {"GBP": "£", "USD": "$", "EUR": "€", "JPY": "¥"}
HOME_CURRENCY = "GBP"


@tool
def convert_currency(amount: float, currency: str) -> str:
    """Converts an amount in one currency into the traveller's home currency."""
    home = HOME_CURRENCY
    if currency not in RATES_TO_GBP:
        raise ToolException(f"No exchange rate for {currency}.")
    converted = round(amount * RATES_TO_GBP[currency] / RATES_TO_GBP.get(home, 1.0), 2)
    return json.dumps({"amount": converted, "currency": home if home in RATES_TO_GBP else "GBP"})


convert_currency.handle_tool_error = True


class ScriptedModel(BaseChatModel):
    """Converts the amount in the question, then reports it as an expense."""

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedModel":
        # A real model is told about the tools here; the scripted one already knows.
        return self

    def _generate(self, messages: list[BaseMessage], stop: Any = None, run_manager: Any = None, **kwargs: Any) -> ChatResult:
        question = next(str(m.content) for m in reversed(messages) if isinstance(m, HumanMessage))
        if question.strip().lower() == "raise":
            raise ValueError("the agent was asked to raise")
        paid = re.search(r"(\d+(?:\.\d+)?)\s*([A-Z]{3})", question)
        results = [m for m in messages if isinstance(m, ToolMessage)]
        if paid is None:
            message = AIMessage(content="How much did you pay, and in which currency? For example: 120 USD.")
        elif not results:
            message = AIMessage(content="", tool_calls=[{
                "name": "convert_currency", "id": "call_convert",
                "args": {"amount": float(paid.group(1)), "currency": paid.group(2)},
            }])
        else:
            try:
                converted = json.loads(str(results[-1].content))
            except json.JSONDecodeError:
                message = AIMessage(content=f"I have no exchange rate for {paid.group(2)}, so I could not convert it. Enter the amount in another currency.")
            else:
                symbol = SYMBOLS[converted["currency"]]
                message = AIMessage(content=f"That is {symbol}{converted['amount']:.2f}. I have added it to your expenses.")
        return ChatResult(generations=[ChatGeneration(message=message)])


prompt = ChatPromptTemplate.from_messages([
    ("system", "You record travel expenses. Convert every amount into the home currency."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

executor = AgentExecutor(
    agent=create_tool_calling_agent(ScriptedModel(), [convert_currency], prompt),
    tools=[convert_currency],
)
