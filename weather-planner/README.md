# weather-planner

Python, Strands Agents. A day planner that calls `get_forecast` (reading `forecasts.json`) before suggesting a plan.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `Should I plan a beach day in Lisbon tomorrow?`: sunny.
- `What should I do in Edinburgh tomorrow?`: rainy. Any other city, such as Reykjavik, makes the tool fail.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `weather-planner` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/strands.

## Use a real model

Replace `StubModel()` with a real Strands model provider. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
