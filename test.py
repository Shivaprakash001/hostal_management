from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os
load_dotenv()

# ── LLM ──────────────────────────────────────────────
llm = ChatGroq(model="Gemma2-9b-it", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

# ── Embeddings + Vector Store ───────────────────────
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="./db", embedding_function=embeddings)
retriever = vectorstore.as_retriever()

# ── TOOL: wrap retriever ────────────────────────────
@tool
def retrieve_tool(query: str) -> str:
    """Retrieve relevant documents from the knowledge base to answer factual queries."""
    docs = retriever.invoke(query)   # .invoke = new API
    return "\n".join([doc.page_content for doc in docs])

# LLM can decide when to call tools
llm_with_tools = llm.bind_tools([retrieve_tool])

# ── Prompt ──────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful hostel management assistant. "
               "You can chat casually OR use tools when needed."),
    ("system", "Facts so far:\n{facts}"),
    ("system", "Conversation summary:\n{summary}"),
    MessagesPlaceholder(variable_name="messages"),
])

# ── State ───────────────────────────────────────────
class State(dict):
    messages: list
    summary: str
    facts: dict

# ── Answer Node ─────────────────────────────────────
def answer(state: State):
    inputs = {
        "messages": state["messages"][-4:],  # keep recent history
        "summary": state.get("summary", ""),
        "facts": state.get("facts", {}),
    }

    # Step 1: LLM proposes an answer (or tool call)
    response = llm_with_tools.invoke(prompt.format_messages(**inputs))

    # Step 2: If tool call, execute it
    if isinstance(response, AIMessage) and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "retrieve_tool":
                tool_result = retrieve_tool.invoke(tool_call["args"]["query"])
                # Add tool result back to state
                state["messages"].append(
                    ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
                )
                # Step 3: Re-ask LLM with tool result
                followup = llm_with_tools.invoke(state["messages"])
                state["messages"].append(followup)
                return state

    # Step 4: Normal case → just a reply
    if hasattr(response, "content") and response.content:
        state["messages"].append(response)
    else:
        state["messages"].append(AIMessage(content="(No response generated)"))

    return state


# ── Runner ──────────────────────────────────────────
if __name__ == "__main__":
    state = State(messages=[], summary="", facts={})
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        state["messages"].append(HumanMessage(content=user_input))
        state = answer(state)
        print("Bot:", state["messages"][-1].content)
