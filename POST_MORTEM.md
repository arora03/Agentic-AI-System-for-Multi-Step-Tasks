# Post-Mortem

## Scaling Issue Encountered / Anticipated
**Issue:** Handling large context windows and state transfer.
Currently, the Orchestrator passes the raw JSON dumps of completed tasks as context to downstream tasks. If the `Retriever` fetches 50,000 tokens of raw data, passing all of this to multiple subsequent agents (e.g., `Analyzer` and `Writer`) will quickly exceed the context window limits of standard LLM APIs, leading to request rejections or degraded reasoning performance.
**Mitigation:** In the future, the state management should rely on a vector database or a summarization pipeline, where downstream agents only receive semantic embeddings or dense summaries of upstream data rather than the raw payload.

## Design Change in Hindsight
**Change:** Agent-to-Agent Communication instead of strict DAG orchestration.
While the centralized Orchestrator with manual batching guarantees order, it is inflexible. If the `Analyzer` realizes the `Retriever` missed something, it cannot easily ask the `Retriever` to fetch more data. In hindsight, implementing a "message bus" architecture where agents can autonomously request sub-tasks from each other (a true multi-agent swarm) would have been more robust than a top-down Planner-Orchestrator pattern.

## Explicit Trade-Offs

1. **Trade-off: Custom Orchestration vs. Framework (e.g., LangChain)**
   - **Reasoning:** I chose to build the `Orchestrator` and `Agent` classes from scratch using raw API calls and `asyncio.gather`. 
   - **Trade-off:** This cost development time and lacks built-in tools (like automatic web searching or memory management) that LangChain provides. However, it was strictly necessary to demonstrate foundational understanding and avoid the "black box" abstraction trap, resulting in a system that is 100% transparent and easier to debug when edge cases occur.

2. **Trade-off: HTTP Server-Sent Events (SSE) vs. WebSockets**
   - **Reasoning:** I used SSE for the FastAPI-to-Next.js streaming connection.
   - **Trade-off:** WebSockets allow bi-directional communication, which is useful for pausing or injecting human feedback mid-execution. SSE is unidirectional (Server to Client). I traded the bi-directional capability for SSE because SSE is significantly easier to implement robustly over HTTP/1.1, handles connection drops automatically (built-in retry), and perfectly fits the requirement of "streaming partial outputs" to the user without adding unnecessary protocol overhead.
