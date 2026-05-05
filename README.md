# Agent Flow

This repository contains a simple agent workflow built using `langgraph` and `langchain_groq`.

## Flow of the agent

1. Load environment variables from `.env`.
2. Create a `ChatGroq` LLM client using `GROQ_API_KEY`.
3. Define an `AgentState` typed dictionary to hold the goal, tasks, results, critique, approval status, and iteration count.
4. Define the `planner` function:
   - Receives the current agent state.
   - Builds a planning prompt using the user's goal.
   - Sends the prompt to the LLM.
   - Parses the LLM response into a JSON task list.
   - Returns the updated state with task results.
5. Build a `langgraph` state graph:
   - Register the `planner` node.
   - Add a start edge from `START` to `planner`.
   - Add a finish edge from `planner` to `END`.
6. Compile the graph and invoke it with an initial state.
7. Print the final task results and iteration summary.

## Notes

- The `.env` file should contain `GROQ_API_KEY=<your_key>`.
- `.env` is excluded from version control to keep the key secret.
