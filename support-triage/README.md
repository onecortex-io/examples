# support-triage

Python, LangGraph. A support graph. `classify` decides what the message is about, `agent` calls `lookup_order` through a `ToolNode` for order questions, and `respond` answers everything else. A checkpointer keeps the conversation per session.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `My order number is 1042.`, then `When will it arrive?` with the same `sessionId`: the second answer remembers the order.
- Order `9999` does not exist, so its lookup fails and the agent says so.
- Send `"model": "..."` with the request and the answer names it: a caller's field reaching the graph.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `support-triage` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/langgraph.

## Use a real model

Replace `ScriptedModel` with your provider's chat model, for example `ChatOpenAI`, bound to the tools with `bind_tools`. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
