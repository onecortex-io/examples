# research-crew

Python, CrewAI. A Researcher and a Writer on two sequential tasks that share one `{topic}` placeholder, which your prompt fills. The model here does not stream, so the answer arrives as one reply with no tool rows: that is how every crew with a model that does not stream behaves.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `heat pumps`, `solar panels` or `tidal energy`

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `research-crew` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/crewai.

## Use a real model

Replace `StubLLM(model="stub")` with `LLM(model="...")` naming a real model, with streaming on to see its text as it arrives. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
