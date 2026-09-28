# order-status

TypeScript, a plain function. An order status assistant written as a plain TypeScript function. It looks the order up with a tool of its own, `lookup_order`, reading `orders.json` from its folder, reports the call and its result as events, then streams the answer.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `Where is order 1042?` `1043` works too.
- `9999`: an unknown order, so the tool fails and the agent says so.
- `raise`: the agent throws.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `order-status` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/typescript-function.

## Use a real model

There is no model. Call any model you like from inside the function. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
