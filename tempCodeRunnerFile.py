        
    class fetchArticleInput(BaseModel):
        url:str

    @tool
    def fetch_article(url:fetchArticleInput):
        """ Fetch the text document from URL. """
        req = urllib.request.Request(
            url,
            header={"User-Agent":"Mozilla/5.0 (compatible; Article-Summarizer-Agent/1.0)"}
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
        except urllib.error.URLError as e:
            return f"Fetch Failed: {e}"
        text = raw.decode("utf-8", errors="replace")
        return text


    model = init_chat_model(
        "openrouter:nvidia/nemotron-3.5-lightning:free",
        api_key = model_api_key,
        temperature=0.5,
        timeout=320,
        max_tokens=25000,
        streaming=True,
        request_timeout=60,
    )

    checkpointer = InMemorySaver()

    agent = create_agent(
        model,
        tools=[fetch_article],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    content = input("Enter URL: ")

    agent_result = agent.invoke(
        {"messages": [{"role":"user", "content":content}]},
        config={"configurable":{"thread_id":"article-summary-lc"}}, #lc for langchiain and da for deep agent
    )

    deep_agent = create_deep_agent(
        model,
        tools=[fetch_article],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


    deep_agent_result = deep_agent.invoke(
        {"messages":[{"role":"user", "content":content}]},
        config={"configurable":{"thread_id":"article-summary-da"}},   
    )

    print("LC-agent: ", agent_result["messages"][-1].content_blocks, "\n\n")
    print("DA-agent: ", deep_agent_result["messaged"][-1].content_blocks)