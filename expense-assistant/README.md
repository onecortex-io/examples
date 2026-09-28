# expense-assistant

Python, LangChain. A tool calling agent run by an `AgentExecutor`. It converts what you paid into pounds with `convert_currency` and records it. Caller fields do not reach an `AgentExecutor`'s tools: an agent that needs them is a LangGraph graph (see `support-triage`).

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `I paid 120 USD for a hotel in New York.` or `Lunch was 3000 JPY.`
- `The taxi cost 40 XYZ.`: a currency with no rate. The tool raises, and the executor turns that into an answer.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `expense-assistant` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/langchain.

## Use a real model

Replace `ScriptedModel()` with your provider's chat model, for example `ChatOpenAI`. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
