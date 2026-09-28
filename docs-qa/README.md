# docs-qa

Python, LlamaIndex. A documentation assistant for a fictional home router. A `FunctionAgent` calls `search_docs` over the pages in `docs/` and answers with the page it used.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `How do I reset the router?` or `How do I update the firmware?`
- `Which pizza toppings are best?`: not in the pages, so the search fails.
- Send `"detail": "full"` with the request and the tool quotes the whole passage, read from the workflow context.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `docs-qa` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/llamaindex.

## Use a real model

Replace the scripted model with a real LlamaIndex LLM, for example `OpenAI(model="gpt-5")`. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
