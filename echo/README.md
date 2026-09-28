# echo

Python, a plain function. The smallest real agent: a Python function with no framework and no dependencies. It reports one tool call of its own, `word_count`, then answers `You said: <prompt>`. It prints an `answering:` line on every call, so you can see your own output in its logs.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `hello`: answers `You said: hello` after one `word_count` call.
- `raise`: the agent raises, so you can see how a failure reaches the caller and the logs.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `echo` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/python-function.

## Use a real model

There is no model. Replace the body of `agent` with your own code, calling any model you like. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
