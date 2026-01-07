import asyncio
import operator
import os
from typing import Annotated, Dict, List, Union

import boto3
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

load_dotenv()

web_search = TavilySearch(max_results=2)


@tool
def send_aws_sns(text: str):
    """テキストをAWS SNSに送信するツール"""
    topic_arn = os.getenv("SNS_TOPIC_ARN")
    sns_client = boto3.client("sns")
    sns_client.publish(TopicArn=topic_arn, Message=text)


tools = [web_search, send_aws_sns]

llm_with_tools = init_chat_model(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    model_provider="bedrock_converse",
).bind_tools(tools)


class AgentState(BaseModel):
    messages: Annotated[List[AnyMessage], operator.add]


builder = StateGraph(AgentState)

system_prompt = """
あなたの責務はユーザーからの質問を調査し、結果を要約して、AWS SNS に送ることです。検索は1回のみとしてください。
"""


async def agent(state: AgentState) -> Dict[str, List[AIMessage]]:
    response = await llm_with_tools.ainvoke(
        [SystemMessage(system_prompt)] + state.messages
    )

    return {"messages": [response]}


builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))


def route_node(state: AgentState) -> Union[str]:
    last_message = state.messages[-1]
    if not last_message.tool_calls:
        return END
    return "tools"


builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route_node)
builder.add_edge("tools", "agent")

graph = builder.compile()


async def main():
    question = "LangGraphの基本を優しく解説して"
    response = await graph.ainvoke({"messages": [HumanMessage(question)]})
    return response


response = asyncio.run(main())
print(response)
