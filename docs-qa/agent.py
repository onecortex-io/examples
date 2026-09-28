"""
A documentation assistant for a home router: it searches the product docs in
docs/ and answers with the page it used. Built the way a LlamaIndex agent is built,
a FunctionAgent with a search tool, and LlamaIndex's own scripted model in place of
a real one.

What it shows:
- A retrieval tool, `search_docs`, with its arguments and the passage it found.
- A tool that fails when nothing matches, and the agent saying so.
- What the caller sent, read from the workflow Context store: send
  `"detail": "full"` and the answer quotes the whole passage.
"""

import json
import pathlib
import re
from collections.abc import Sequence
from typing import Any

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import ChatMessage, MockFunctionCallingLLM
from llama_index.core.tools import ToolSelection
from llama_index.core.workflow import Context

DOCS = {path.name: path.read_text() for path in sorted((pathlib.Path(__file__).parent / "docs").glob("*.md"))}
STOP = {"the", "a", "an", "how", "do", "i", "my", "to", "is", "what", "on", "up", "set", "can"}


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP}


async def search_docs(ctx: Context, query: str) -> str:
    """Finds the documentation page that best answers a question."""
    sent = await ctx.store.get("onecortex", default={})
    detail = (sent or {}).get("params", {}).get("detail", "short")
    scored = sorted(((len(words(query) & words(text)), name) for name, text in DOCS.items()), reverse=True)
    score, name = scored[0]
    if score == 0:
        raise ValueError(f"No page in the documentation matches '{query}'.")
    body = [line for line in DOCS[name].splitlines()[1:] if line.strip()]
    passage = " ".join(body) if detail == "full" else body[0]
    return json.dumps({"page": name, "passage": passage})


def reply(messages: Sequence[ChatMessage], **kwargs: Any) -> ChatMessage:
    """The whole model: search for the question, then answer from the passage."""
    last = messages[-1]
    question = next(str(m.content) for m in reversed(messages) if m.role.value == "user")
    if question.strip().lower() == "raise":
        raise ValueError("the agent was asked to raise")
    if last.role.value == "tool":
        try:
            found = json.loads(str(last.content))
        except json.JSONDecodeError:
            return ChatMessage(role="assistant", content="The documentation does not cover that. Try asking about resetting, firmware or the guest network.")
        return ChatMessage(role="assistant", content=f"{found['passage']} (source: {found['page']})")
    call = ToolSelection(tool_id="call_search", tool_name="search_docs", tool_kwargs={"query": question})
    return ChatMessage(role="assistant", content="", additional_kwargs={"tool_calls": [call]})


agent = FunctionAgent(
    name="docs",
    description="Answers questions about the Halo router from its documentation.",
    system_prompt="Search the documentation before answering, and cite the page.",
    tools=[search_docs],
    llm=MockFunctionCallingLLM(response_generator=reply),
)
