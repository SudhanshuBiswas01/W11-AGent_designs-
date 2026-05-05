import os, json
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph,START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq

load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY not found in .env")

llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=api_key)

class AgentState(TypedDict):
    goal: str
    tasks: List[str]
    results: List[str]
    critique: str 
    approved: bool 
    iterations: int

search = DuckDuckGoSearchRun()

def planner(state: AgentState) -> AgentState:
    system = """You are a planning agent. Break the user's goal into at most 5 concrete tasks. Return only with a valid JSON array of strings. No preamble, no markdown."""

    message = [
        SystemMessage(content=system),
        HumanMessage(content=f"Goal: {state['goal']}")
    ]

    response = llm.invoke(message).content.strip()

    try:
        clean = response.replace("'''json", "").replace("'''", "").strip()
        tasks = json.loads(clean)
    except json.JSONDecodeError:
        tasks = [response]
    
    print(f"Planner response: {tasks}")
    for i , t in enumerate(tasks):
        print(f"Task {i+1}: {t}")
    return {**state, "tasks": tasks}

def executor(state: AgentState) -> AgentState:
    results = []
    critique_ctx = ""
    if state["critique"]:
        critique_ctx = f"\n\n Your previous attempt was rejected. Critique: {state['critique']} \n Improve your results based on this feedback."

    for task in state["tasks"]:
        system = f"""You are an execution agent. Your task is to execute the given task using web search and return a concise summary of the findings. {critique_ctx}"""

        search_ctx = ""
        try:
            search_results = search.run(task[:100])
            search_ctx = f"\n\n Web Search results for context : {search_results[: 800]}"
        except:
            pass

        message = [
            SystemMessage(content=system),
            HumanMessage(content=f"Task: {task} {search_ctx}")
        ]

        result = llm.invoke(message).content
        results.append(result)
        print(f"\n[Execution] Task: {task[:60]} \nResult: {result[:120]}")

    return {**state, "results": results , "iterations": state["iterations"] + 1}


def verifier(state: AgentState) -> AgentState:
    # safety net - approve after 3 iterations regardless
    if state["iterations"] >= 3:
        print("[Verifier] Max iterations reached - force approving.")
        return {**state, "approved": True}

    combined_results = "\n\n".join(
        f"Task {i+1}: {t}\nResult: {r}"
        for i, (t, r) in enumerate(zip(state["tasks"], state["results"]))
    )
    system = """You are a quality verifier. Evaluate the results against the original goal using this rubric:
Completeness: Does it fully address the goal? (0-0.4)
Accuracy: Is the information correct and specific? (0-0.3)
Clarity: Is it well-structured and clear? (0-0.3)
Sum the scores for a total between 0.0 and 1.0.
Respond ONLY as JSON: {"score": 0.85, "approved": true, "critique": "..."}"""
    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"Original goal: {state['goal']}\n\nResults: \n{combined_results}")
    ]
    try:
        raw = llm.invoke(messages).content.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        verdict = json.loads(clean)
        approved = verdict.get("approved", False)
        critique = verdict.get("critique", "")
        score = verdict.get("score", 0)
    except:
        approved, critique, score = False, raw, 0

    
    print(f"\n[Verifier] Score: {score:.2f} | Approved: {approved}")
    return {**state, "approved": approved, "critique": critique}








graph = StateGraph(AgentState)

graph.add_node("planner", planner)
graph.add_node("executor", executor)
graph.add_node("verifier", verifier)

graph.add_edge(START, "planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", "verifier")
graph.add_conditional_edges("verifier", lambda state: END if state["approved"] else "planner")
app = graph.compile()
# - run it —
initial_state: AgentState = {
    "goal": "Research and summarise the top 3 trends in generative AI for 2025",
    "tasks": [],
    "results": [],
    "critique": "",
    "approved": False,
    "iterations": 0
}
final_state = app.invoke(initial_state)

print("\n====== FINAL OUTPUT =====")
for i, (task, result) in enumerate(zip(final_state["tasks"], final_state["results"])):
    print(f"\n[Task {i+1}] {task} \n{result}")
print(f"\nCompleted in {final_state['iterations']} iteration(s).")


