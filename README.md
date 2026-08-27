# Article Summarizer Agent

## Description

This project is a conversational article summarization API built with FastAPI and a LangChain/LangGraph agent. Given a URL, the agent fetches the page, extracts the article's readable content (stripping nav bars, ads, scripts, and other page chrome), stores it in short-term memory, and lets the user ask follow-up questions about it (summaries, tone analysis, entity extraction, etc.) using conversational memory instead of a single-shot summarize-and-done response.


## Requirements

- Python 3.12
- fastapi
- uvicorn
- pydantic
- python-dotenv
- trafilatura
- lxml_html_clean
- langchain
- langchain-core
- langchain-openrouter
- langgraph

Install all requirements with:

```
pip install -r requirements.txt
```

## Topics Learned

- Building a FastAPI service with typed request/response models (Pydantic `BaseModel`, `HttpUrl`)
- Fetching and parsing raw HTML with `urllib.request`, including setting request headers to avoid basic bot blocking
- Extracting clean article text from raw HTML using `trafilatura`, instead of feeding raw page source into an LLM
- Building an LLM agent with LangChain/LangGraph and connecting it to a chat model through OpenRouter
- Using a LangGraph checkpointer for short-term conversational memory, keyed by `thread_id`
- Writing to agent memory without triggering a model call (`agent.update_state`), versus invoking the model on existing memory (`agent.invoke`)
- Reading stored conversation state without re-running the agent (`agent.get_state`)
- Debugging live agent behavior through FastAPI's auto-generated Swagger UI (`/docs`)
- Handling free-tier LLM provider instability (timeouts, deprecated model IDs, upstream overload errors) and adding retry/timeout configuration at the model level

## Challenges

- **Deprecated free model ID**: The original model (`nvidia/nemotron-nano-9b-v2:free`) had been pulled from OpenRouter, causing silent hangs and read timeouts rather than a clear error. Diagnosed by testing the raw OpenRouter HTTP endpoint directly, outside of LangChain, to isolate the failure from the agent code.
- **Agent overhead vs. free-tier limits**: An initial `deepagents`-based agent added significant system prompt and tool-schema overhead per request, which combined with a slow free-tier model to consistently exceed the request timeout. Switched to a standard LangChain agent to reduce payload size and request latency.
- **Upstream provider overload**: Even with a valid, available model, requests occasionally failed with a 502 "service temporarily overloaded" error from the underlying provider (NVIDIA via OpenRouter). Addressed by adding `max_retries` at the model level rather than treating it as a code bug.
- **Windows Application Control policy**: The dev machine's Application Control policy blocked a compiled dependency DLL (`orjson`, a FastAPI dependency) and, at one point, `pip.exe` itself. Worked around by running package management through `python -m pip` and reinstalling affected packages inside the correct Python 3.12 virtual environment.
- **Separating ingestion from summarization**: Initial design ran the agent immediately on ingest, producing a summary before the user asked for one. Reworked `/ingest` to only fetch, extract, and write the article into the thread's memory via `agent.update_state`, deferring all model calls to `/chat`.

## How to Run

1. Clone or download this repository.
2. Create and activate a Python 3.12 virtual environment:

```
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install the required libraries (see Requirements above).
4. Set the required API key in a `.env` file in the project root:

```
MODEL_API_KEY=your_openrouter_api_key
```

5. Run the API with uvicorn:

```
python -m uvicorn src.api.routes:app --reload
```

6. Open the interactive Swagger UI to test the endpoints:

```
http://127.0.0.1:8000/docs
```

7. Typical flow:
   - `POST /ingest` with `{"url": "..."}` to fetch and store an article, returns a `thread_id`.
   - `POST /chat` with `{"thread_id": "...", "query": "..."}` to ask questions about the ingested article.
   - `GET /summaries/{thread_id}` to retrieve stored conversation state without re-running the agent.

## Running with Docker

1. Build the Docker image:
   ```
   docker build -t article-summarizer-agent .
   ```

2. Run the container with your environment file:
   ```
   docker run -it -p 8000:8000 --env-file .docker.env article-summarizer-agent
   ```

3. Open the interactive Swagger UI to test the endpoints:
   ```
   http://localhost:8000/docs
   ```