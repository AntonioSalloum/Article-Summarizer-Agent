import urllib.error
import urllib.request
from pydantic import BaseModel
from langchain.tools import tool
from langchain_openrouter import ChatOpenRouter
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from deepagents import create_deep_agent
from dotenv import load_dotenv
import os


load_dotenv()

#article summarizer agent

SYSTEM_PROMPT = ''' You are a helpful intelligent article summarizer assistant.
##capabilities
 - 'fetch_article': you fetch the uploaded article and return structured summary of (key points, tone, and entities)
 - Do not guess line counts or position-ground them in tool results from the uploaded article
 - If the answer is not found in the article, say: '\nI do not know based on the given data\n', do not make anything up
'''
    
class fetchArticleInput(BaseModel):
    url:str

@tool
def fetch_article(url:fetchArticleInput):
    """ Fetch the text document from URL. """
    req = urllib.request.Request(
        url,
        headers={"User-Agent":"Mozilla/5.0 (compatible; Article-Summarizer-Agent/1.0)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        return f"Fetch Failed: {e}"
    text = raw.decode("utf-8", errors="replace")
    return text


model = ChatOpenRouter(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    api_key = os.environ.get("MODEL_API_KEY"),
    temperature=0.5,
    timeout=500,
    max_tokens=25000,
    streaming=True,
    request_timeout=120,
    max_retries=10,
)

checkpointer = InMemorySaver()

agent = create_agent(
    model,
    tools=[fetch_article],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
    
)
deep_agent = create_deep_agent(
    model,
    tools=[fetch_article],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)



if __name__ == "__main__":
    content = input("Enter URL: ")

    deep_agent_result = deep_agent.invoke(
        {"messages":[{"role":"user", "content":content}]},
        config={"configurable":{"thread_id":"article-summary-da"}},   
    )
    agent_result = agent.invoke(
        {"messages": [{"role":"user", "content":content}]},
        config={"configurable":{"thread_id":"article-summary-lc"}}, #lc for langchiain and da for deep agent
    )



    print("LC-agent: ", agent_result["messages"][-1].content_blocks, "\n\n")
    print("DA-agent: ", deep_agent_result["messaged"][-1].content_blocks)