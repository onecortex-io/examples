# Onecortex examples

Agents you can deploy to Onecortex as they are, one per folder, one per supported framework. Fork this
repository, pick a folder in the Onecortex dashboard, and call the agent over HTTPS a few minutes later.

None of them needs a model API key. Each uses a scripted model and the data in its folder, so every answer
is exact, and each README says where a real model plugs in.

| Folder | Language | Framework | Docs |
|---|---|---|---|
| [`echo`](echo) | Python | a plain function | https://docs.onecortex.io/frameworks/python-function |
| [`support-triage`](support-triage) | Python | LangGraph | https://docs.onecortex.io/frameworks/langgraph |
| [`travel-concierge`](travel-concierge) | Python | the OpenAI Agents SDK | https://docs.onecortex.io/frameworks/openai-agents |
| [`weather-planner`](weather-planner) | Python | Strands Agents | https://docs.onecortex.io/frameworks/strands |
| [`docs-qa`](docs-qa) | Python | LlamaIndex | https://docs.onecortex.io/frameworks/llamaindex |
| [`expense-assistant`](expense-assistant) | Python | LangChain | https://docs.onecortex.io/frameworks/langchain |
| [`research-crew`](research-crew) | Python | CrewAI | https://docs.onecortex.io/frameworks/crewai |
| [`recipe-assistant`](recipe-assistant) | TypeScript | Mastra | https://docs.onecortex.io/frameworks/mastra |
| [`meeting-scheduler`](meeting-scheduler) | TypeScript | the Vercel AI SDK | https://docs.onecortex.io/frameworks/vercel-ai |
| [`ticket-summarizer`](ticket-summarizer) | TypeScript | LangChain.js | https://docs.onecortex.io/frameworks/langchain-js |
| [`order-status`](order-status) | TypeScript | a plain function | https://docs.onecortex.io/frameworks/typescript-function |

Start with the quickstart, which deploys `echo`: https://docs.onecortex.io/quickstart.

Every folder holds an `agent.yml`, the one file Onecortex needs: https://docs.onecortex.io/agent-yml.

MIT licensed. Start your own agent from any of them.
