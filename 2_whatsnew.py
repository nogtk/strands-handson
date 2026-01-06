import feedparser
from strands import Agent, tool
from dotenv import load_dotenv

load_dotenv()

@tool
def get_aws_updates(service_name: str) -> list:
    feed = feedparser.parse("https://aws.amazon.com/about-aws/whats-new/recent/feed/")
    result = []

    for entry in feed.entries:
        if service_name.lower() in entry.title.lower():
            result.append({
                "published": entry.get("published", "N/A"),
                "summary": entry.get("summary", "")
            })

            if len(result) >= 3:
                break
    
    return result

agent = Agent(
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[get_aws_updates]
)

service_name = input("アップデートを知りたいAWSサービス名を入力してください:").strip()
prompt = f"AWSの{service_name}の最新アップデートを日付付きで要約して。"
response = agent(prompt)