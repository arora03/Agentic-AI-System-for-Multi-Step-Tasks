# Post-Mortem: Agentic AI System

This document reflects on the architectural decisions, challenges, and trade-offs made while building this multi-agent orchestrator from scratch.

## 1. A Scaling Issue Anticipated
**Context Window Bloat in the DAG**
Currently, when a task executes, the Orchestrator injects the results of all its prerequisite tasks into the LLM's prompt context. While this works beautifully for 5-10 tasks, it will not scale. If a "Writer" agent depends on the outputs of 5 different "Analyzer" agents—and each produced a 2,000-token summary—the prompt will quickly exceed the LLM's context limit or cause the model's attention mechanism to degrade. 
*Future Solution:* Implement a vector database (like Pinecone) or a summarization middleware layer. Instead of injecting raw dependency outputs, the system would retrieve only the most semantically relevant chunks of previous task outputs.

## 2. A Design Change in Hindsight
**State Management & Canceling Executions**
In hindsight, while Server-Sent Events (SSE) was perfect for unidirectional streaming of the DAG's progress to the frontend, it lacks bi-directional communication. Once the user clicks "Submit", the FastAPI backend locks into the orchestration loop. If the user notices the Planner made a mistake on Task 1, they cannot easily hit a "Cancel" button to halt the execution midway. 
If I were to rebuild this, I would swap SSE for WebSockets, allowing the Next.js frontend to send a `KILL` signal over the socket to gracefully terminate the `asyncio` task loop on the backend.

## 3. Two Explicit Trade-offs

### Trade-off A: Custom Architecture vs. Black-Box Frameworks
**The Decision:** I strictly adhered to the constraint of avoiding black-box frameworks like LangChain, CrewAI, or AutoGen. I built the `BaseAgent` and `Orchestrator` entirely from scratch using Python's native `asyncio` and `pydantic`.
*   **Pros:** Complete transparency. I know exactly how retries, JSON-mode enforcement, and HTTP calls are handled. There is zero abstraction overhead, resulting in lightning-fast execution times and zero "magic" bugs.
*   **Cons (The Trade-off):** I had to manually implement complex systems like deadlock detection, DAG topological sorting, and concurrent batching (`asyncio.gather`). Relying on a framework like LangGraph would have provided these out-of-the-box, saving development time, but it would have violated the core philosophy of demonstrating true system ownership.

### Trade-off B: SSE (Server-Sent Events) vs. Polling/WebSockets
**The Decision:** I chose SSE to stream the execution state to the Next.js frontend.
*   **Pros:** Native HTTP support, automatic reconnection, and incredibly lightweight compared to establishing a stateful WebSocket connection. It perfectly matched the unidirectional requirement of streaming logs to the user.
*   **Cons (The Trade-off):** As discovered during development, SSE chops massive LLM payloads into arbitrary byte chunks over the network. I had to manually engineer a stream-buffering system on the frontend to safely parse `\r\n\r\n` delimiters and prevent `JSON.parse` from crashing on partial strings. A simpler polling mechanism (where the UI fetches the state every 1 second) would have avoided this complexity, but it would have sacrificed the beautiful, real-time "streaming" UX that makes the application feel alive.
