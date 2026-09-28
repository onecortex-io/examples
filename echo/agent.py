"""
The smallest agent that is still a real one.

It calls no model and needs no credentials, which is the point: when a
deployment of this fails, the failure is in the platform and not in somebody's
API key. Swap the body for a real call once the path it travels is trusted.

Prints and raises on request, on purpose: proving the platform also means
proving what it does with an agent's own log output and an agent's own
exception, not just a clean response.

Before answering it reports one tool call of its own, as plain dicts, so the
dashboard chat and every surface show a tool row: the platform renders tool
calls, and this is the smallest agent that proves it.
"""

import json
import logging
from collections.abc import Iterator
from typing import Any

logger = logging.getLogger(__name__)


def agent(prompt: str) -> Iterator[Any]:
    """Counts the words with a tool of its own, then answers."""
    logger.info("received prompt: %s", prompt)
    if prompt.strip().lower() == "raise":
        raise ValueError("the agent was asked to raise")

    yield {"type": "tool_call_start", "id": "call_1", "name": "word_count"}
    yield {"type": "tool_call_args", "id": "call_1", "delta": json.dumps({"text": prompt})}
    yield {"type": "tool_call_end", "id": "call_1"}
    yield {"type": "tool_result", "id": "call_1", "output": str(len(prompt.split()))}

    answer = f"You said: {prompt}"
    print(f"answering: {answer}")
    yield answer
