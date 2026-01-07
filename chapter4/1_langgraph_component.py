import operator
from typing import Annotated, Any, Dict, Literal

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel


class State(BaseModel):
    messages: Annotated[list[str], operator.add]
    id: int


builder = StateGraph(State)


def search_web(state: State) -> Dict[str, Any]:
    # Dummy implementation of web search
    return {"id": 123, "messages": ["WebSearch"]}


def summarize(state: State) -> Dict[str, Any]:
    return {"id": 123, "messages": ["Summarizer"]}


def save_record(state: State) -> Dict[str, Any]:
    return {"id": 123, "messages": ["SaveRecord"]}


def routing_function(state: State) -> Literal["Summarizer", "Recorder"]:
    if state.id == 123:
        return "Summarizer"
    else:
        return "Recorder"


builder.add_node("WebSearch", search_web)
builder.add_node("Summarizer", summarize)
builder.add_node("Recorder", save_record)

builder.add_edge(START, "WebSearch")
builder.add_conditional_edges("WebSearch", routing_function)
builder.add_edge("Summarizer", END)
builder.add_edge("Recorder", END)

graph = builder.compile()

response = graph.invoke({"id": 123, "messages": ["start"]})
print(response)
