import asyncio

import feedparser
import streamlit as st
from dotenv import load_dotenv
from strands import Agent, tool

load_dotenv()


@tool
def get_aws_updates(service_name: str) -> list:
    feed = feedparser.parse("https://aws.amazon.com/about-aws/whats-new/recent/feed/")
    result = []

    for entry in feed.entries:
        if service_name.lower() in entry.title.lower():
            result.append(
                {
                    "published": entry.get("published", "N/A"),
                    "summary": entry.get("summary", ""),
                }
            )

            if len(result) >= 3:
                break

    return result


agent = Agent(
    model="us.anthropic.claude-sonnet-4-20250514-v1:0", tools=[get_aws_updates]
)

st.title("AWS最新アップデート要約アプリ")
service_name = st.text_input("アップデートを知りたいAWSサービス名を入力してください:")


async def process_stream(service_name: str, container):
    text_holder = container.empty()
    response = ""
    prompt = f"AWSの{service_name}の最新アップデートを日付付きで要約して。"

    async for chunk in agent.stream_async(prompt):
        if isinstance(chunk, dict):
            event = chunk.get("event", {})

            if "contentBlockStart" in event:
                tool_use = (
                    event["contentBlockStart"].get("start", {}).get("toolUse", {})
                )
                tool_name = tool_use.get("name")

                if response:
                    text_holder.markdown(response)
                    response = ""

                container.info(f"{tool_name} ツールを実行中...")
                text_holder = container.empty()

            if text := chunk.get("data"):
                response += text
                text_holder.markdown(response)


if st.button("確認"):
    if service_name.strip() == "":
        st.warning("サービス名を入力してください。")
    else:
        with st.spinner("アップデートを確認中..."):
            container = st.container()
            asyncio.run(process_stream(service_name, container))
