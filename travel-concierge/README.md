# travel-concierge

Python, the OpenAI Agents SDK. `Triage` hands flight requests to `Booking`, which calls `search_flights` (reading `flights.json`) and recommends the cheapest direct flight.

It calls no real model and needs no API key: a scripted model and the data in this folder make every answer exact, while the events it streams are the ones the framework really produces.

## Try it

- `Find me a flight from London to Lisbon on 12 October`. London to Madrid works too, and London to Oslo has no flights.
- Send `"currency": "EUR"` or `"USD"` with the request and the tool converts the prices, read from the run context.

## Deploy it

1. Fork this repository.
2. Sign in at https://app.onecortex.io and click **Create agent**.
3. Connect GitHub, pick your fork, and choose `travel-concierge` as the agent folder.
4. Click **Create agent**, and call it once the build succeeds.

The full walk through is the quickstart: https://docs.onecortex.io/quickstart. This framework's page: https://docs.onecortex.io/frameworks/openai-agents.

## Use a real model

Replace `TriageModel()` and `BookingModel()` with a real model name, for example `model="gpt-5"`. Add the model's API key as a secret on the agent's **Config** tab, never in the repository: https://docs.onecortex.io/build/configuration.
