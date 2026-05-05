import os, json
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq

load_dotenv()
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=os.environ.get("GROQ_API_KEY")
)

class AgentState(TypedDict):
    goal: str
    tasks: List[str]
    results: List[str]
    critique: str 
    approved: bool 
    iterations: int

search = DuckDuckGoSearchRun()

def planner(state: AgentState) -> AgentState:
    system = """You are a planning agent. Break the usre's goal into at most 5 concrete tasks. Return only with a valid JSON array of strting. No preamable, no markdown."""

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