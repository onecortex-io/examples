# refund-approval

Python, LangGraph. A refund desk that asks a person before it refunds anything. The model looks the order up with `lookup_order`, then the `approve` node calls `interrupt()` with the question and a JSON Schema for the answer. The run ends with an `interrupt` event, and the next call on the same session carries the answer as a `resume`. An in-memory checkpointer keeps the pause for as long as the session lives.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `Please refund order 1042` ends with an `interrupt` asking to approve 40.00 EUR. Answer it with the same `sessionId` and a `resume`: `{"approve": true, "note": "..."}` refunds, `{"approve": false}` declines, and a `cancelled` resume cancels.
- In the dashboard's **Chat** tab the same pause shows as a form under the reply.
- Order `9999` does not exist, so its lookup fails and nothing pauses.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `refund-approval` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

How pausing and resuming work: https://docs.onecortex.io/build/human-in-the-loop. This framework's page: https://docs.onecortex.io/frameworks/langgraph.

## Use a real model

Replace `ScriptedModel` with your provider's chat model, for example `ChatOpenAI`, bound to the tools with `bind_tools`. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration. For a pause that must outlive the session, compile the graph with a durable checkpointer, such as Postgres.
