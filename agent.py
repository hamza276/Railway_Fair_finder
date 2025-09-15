import os
from typing import Optional
from config import logger
from tools import create_railway_search_tool, create_web_search_tool, create_web_loader_tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# -----------------------------------------------------------------------------------
# Create LangChain agent
# -----------------------------------------------------------------------------------

def create_railway_agent(api_key: Optional[str]) -> AgentExecutor:
    resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_api_key:
        raise RuntimeError(
            "Missing API key. Set OPENROUTER_API_KEY (or OPENAI_API_KEY) before running."
        )

    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    logger.info(f"Using OpenRouter base URL: {base_url}")

    # Proper Chat model that uses the OpenAI "tools" API (not deprecated "functions")
    llm = ChatOpenAI(
        api_key=resolved_api_key,
        model="deepseek/deepseek-chat-v3.1:free",
        base_url=base_url,
        temperature=0.7,
    )

    tools = [
        create_railway_search_tool(),
        create_web_search_tool(),
        create_web_loader_tool()
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant for Pakistan Railway fare searches.

Your capabilities:
- Search railway fares between Pakistani cities using web search and content loading
- Find cheapest options and multiple class alternatives
- Load content from official Pakistan Railway websites

Available tools:
1. railway_search: Comprehensive search for fares between cities
2. web_search_railway: Search for railway information from official sources
3. load_railway_page: Load content from specific railway website URLs

When users ask about railway travel:
1. Use railway_search tool for comprehensive fare searches
2. If more details needed, use web_search_railway for additional information
3. For specific pages, use load_railway_page tool
4. If departure or arrival location is missing, ask the user to provide them
5. Present results in a clear, structured format
6. Always show the cheapest option first

Be conversational and helpful. If information is missing, politely ask for it."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    # Use the tools agent (sends "tools", not "functions")
    agent = create_openai_tools_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )

    return agent_executor