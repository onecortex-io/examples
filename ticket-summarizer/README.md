# ticket-summarizer

TypeScript, LangChain.js. A runnable that calls `classify_ticket` and `lookup_customer` (reading `customers.json`), then writes a one line summary.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `Summarize this ticket: The app crashes when I upload a photo on Android. Account ACME-17.`
- An unknown account ID makes the lookup fail, and the chain carries on without it.
- Send `"team": "..."` with the request and the ticket is routed there.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `ticket-summarizer` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/langchain-js.

## Use a real model

Add a chat model to the chain, for example `ChatOpenAI` from `@langchain/openai`. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
