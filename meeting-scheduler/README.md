# meeting-scheduler

TypeScript, the Vercel AI SDK. A `ToolLoopAgent` that calls `checkCalendar`, then `holdSlot`, then confirms: two tool calls in one run.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `Find me an hour on Thursday`
- `Can we meet on Monday?`: fully booked. `Book something on Saturday`: the calendar tool fails on a weekend.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `meeting-scheduler` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/vercel-ai.

## Use a real model

Replace the mock model with a real one, for example `openai('gpt-5')` from `@ai-sdk/openai`. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
