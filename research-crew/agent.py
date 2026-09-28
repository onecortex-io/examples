"""
A two person research crew: a Researcher gathers the facts on a topic and a Writer
turns them into a short brief. Built the way a CrewAI crew is built, two agents and
two sequential tasks sharing one `{topic}` placeholder, with a stub model in place
of a real one.

What it shows, honestly: a crew whose model does not stream. CrewAI reports tool
calls and text only as the model streams them, and a stub model streams nothing,
so the platform answers with the crew's final result as one reply. That is the
path every non streaming crew takes. The Researcher's notes live in NOTES below.
"""

import os

# Telemetry goes to the framework's own servers by default, a network call and a
# background thread to report that nothing happened.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from typing import Any  # noqa: E402

from crewai import Agent, BaseLLM, Crew, Task  # noqa: E402

NOTES = {
    "heat pumps": [
        "A heat pump moves heat rather than making it, so it delivers three to four units of heat per unit of electricity.",
        "Air source models work down to about minus 15°C.",
        "Running costs are lowest in a well insulated home with large radiators or underfloor heating.",
    ],
    "solar panels": [
        "A typical 4 kW home system produces about 3,400 kWh a year in southern England.",
        "Panels lose roughly half a percent of output each year.",
        "A battery raises the share of solar power a home uses itself from about a third to about two thirds.",
    ],
}


def notes_for(topic: str) -> list[str] | None:
    return next((facts for name, facts in NOTES.items() if name in topic.lower()), None)


class StubLLM(BaseLLM):
    """Plays whichever crew member is asking: research notes for the Researcher, a brief for the Writer."""

    def call(self, messages: Any, tools: Any = None, callbacks: Any = None, available_functions: Any = None, **kwargs: Any) -> str:
        text = "\n".join(str(m["content"]) for m in messages) if isinstance(messages, list) else str(messages)
        topic = text.split("TOPIC: ")[-1].split("\n")[0].strip()
        if topic.lower() == "raise":
            raise ValueError("the agent was asked to raise")
        facts = notes_for(topic)
        if "You are Researcher" in text:
            body = "\n".join(f"- {fact}" for fact in facts) if facts else "- No notes found on this topic."
            return f"Final Answer: {body}"
        if facts is None:
            return f"Final Answer: There is not enough research on {topic} for a brief yet."
        return f"Final Answer: Brief on {topic}: {' '.join(facts)}"

    def supports_function_calling(self) -> bool:
        return False


researcher = Agent(
    role="Researcher",
    goal="Gather the key facts on a topic",
    backstory="You collect facts and never speculate.",
    llm=StubLLM(model="stub"),
)
writer = Agent(
    role="Writer",
    goal="Turn research into a short, plain brief",
    backstory="You write briefly for a general reader.",
    llm=StubLLM(model="stub"),
)

research = Task(
    description="Research this topic and list the key facts.\nTOPIC: {topic}",
    expected_output="A bulleted list of facts.",
    agent=researcher,
)
brief = Task(
    description="Write a brief from the research.\nTOPIC: {topic}",
    expected_output="One short paragraph.",
    agent=writer,
    context=[research],
)

crew = Crew(agents=[researcher, writer], tasks=[research, brief])
