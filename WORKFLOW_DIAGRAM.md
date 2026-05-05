# Agent Workflow Diagram

## Multi-Agent Research & Validation System

```mermaid
---
config:
  layout: elk
---
flowchart TD
    subgraph P[Planner Agent]
        class P planner
        A1["User Goal Input"] --> A2["Use Groq LLM to generate 1–5 tasks"]
        A2 --> A3["Clean and parse JSON into task list"]
        A3 --> A4["Store tasks in AgentState.tasks"]
    end

    subgraph E[Executor Agent]
        class E executor
        B1["Receive tasks + critique (if any)"] --> B2["Search web (DuckDuckGo) for each task"]
        B2 --> B3["Summarize results using LLM"]
        B3 --> B4["Incorporate critique if verification failed"]
        B4 --> B5["Update AgentState.results and iterations"]
    end

    subgraph V[Verifier Agent]
        class V verifier
        C1["Receive tasks, results, and goal"] --> C2["Evaluate quality (Completeness 40%, Accuracy 30%, Clarity 30%)"]
        C2 --> C3["Generate JSON verdict (score + approval)"]
        C3 --> C4["If not approved and iterations < 3 → send critique to Executor"]
        C4 --> C5["If approved or max iterations reached → mark approved=true"]
    end

    %% Flow connections %%
    A4 --> B1
    B5 --> C1
    C4 --> B1
    C5 --> D["Approved Output"]

    %% Shared State %%
    subgraph S[AgentState]
        class S state
        S1["goal"]
        S2["tasks"]
        S3["results"]
        S4["critique"]
        S5["approved"]
        S6["iterations"]
    end

    P -.-> S
    E -.-> S
    V -.-> S

    %% Styling %%
    classDef planner stroke:#818cf8,fill:#eef2ff;
    classDef executor stroke:#2dd4bf,fill:#f0fdfa;
    classDef verifier stroke:#a78bfa,fill:#f5f3ff;
    classDef state stroke:#4ade80,fill:#f0fdf4;
```

## Workflow Overview

- **Planner:** Decomposes the user goal into 1–5 concrete tasks
- **Executor:** Performs web searches and LLM-based summarization for each task
- **Verifier:** Quality-checks results and provides critique for refinement
- **Loop:** If not approved and iterations < 3, feedback cycles back to Executor
- **Exit:** Approved output or max iterations (3) reached

**Shared State:** All agents read/write to `AgentState` containing goal, tasks, results, critique, approval status, and iteration count.
