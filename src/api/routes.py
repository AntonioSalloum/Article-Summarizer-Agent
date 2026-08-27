import hashlib
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
import urllib.error
import urllib.request
import trafilatura
from main import agent


app = FastAPI()

class inputURL(BaseModel):
    url: HttpUrl


@app.get("/")
def root():
    return {"message": "welcome, head to docs for Swagger UI"}

@app.post("/ingest")
async def ingest(input_url: inputURL):
    url = str(input_url.url)
    
    thread_id = hashlib.md5(url.encode()).hexdigest()

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        return f"Fetch Failed: {e}"

    
    text = raw.decode("utf-8", errors="replace")
    extracted = trafilatura.extract(text) # to only extract the content of the web page and not the entire code of it

    agent.update_state(
        config={"configurable": {"thread_id": thread_id}},
        values={"messages": [{"role": "user", "content": f"Here is the article content:\n\n{extracted}"}]},
    )

    return {
        "message": "succefully ingested url",
        "text": extracted,
        "length of text": len(extracted) if extracted else 0,
        "thread_id": thread_id,
    }
    
class inputQuery(BaseModel):
    query: str
    thread_id: str


@app.post("/chat")
def chat(input_query: inputQuery):
    query = input_query.query

    agent_result = agent.invoke(
        {"messages": [{"role": "user", "content": query}]},
        config={"configurable": {"thread_id": input_query.thread_id}},
    )

    return {
        "message": "success",
        "deep-agent output": agent_result["messages"][-1].content_blocks
    }

    

@app.get("/retrieve-summaries/{thread_id}")
def retrieve_summaries(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    state = agent.get_state(config)

    messages = state.values.get("messages", [])
    
    if not messages:
        return {
            "message": "No history found",
            "thread_id": thread_id,
            "content": None
        }

    last_message = messages[-1]
    content = last_message.content

    return {
        "messages": [msg.content for msg in messages],
        "thread_id": thread_id,
        "content": content
    }