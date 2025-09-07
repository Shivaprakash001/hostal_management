# agent/graph2.py

from typing import Any, Dict, List, TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.pydantic_v1 import BaseModel, Field, ValidationError
from langchain.output_parsers import PydanticOutputParser
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from . import tools as t
import os

load_dotenv()

from .embeddings import embeddings   # ✅ load once

# -----------------------------
# Persistent Vectorstore
# -----------------------------
PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

# ✅ Load existing vectorstore if available
if os.path.exists(PERSIST_DIR):
    vectorstore = Chroma(
        collection_name="hostel",
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
    )
else:
    # Ingest docs first time only
    from langchain.schema import Document
    docs = [
        Document(page_content="Hostel fees is 5000 per semester."),
        Document(page_content="Mess timings are 8AM, 1PM, 8PM."),
    ]
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="hostel",
        persist_directory=PERSIST_DIR,
    )
    vectorstore.persist()

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
print(vectorstore._collection.count())  # should show >0


# ── STATE ──────────────────────────────────────────────
class AgentState(TypedDict):
    messages: List[Any]
    plan: Dict[str, Any]
    results: List[str]
    summary: str
    context: str

# ── PLAN MODEL ─────────────────────────────
class Step(BaseModel):
    action: str
    parameters: Dict[str, Any] = {}

class Plan(BaseModel):
    todo: List[Step]
    summary: str

class RagToolInput(BaseModel):
    query: str = Field(..., description="The query to search for hostel info")

# ── MODELS ─────────────────────────────────────────────
llm = ChatGroq(model="Gemma2-9b-it", temperature=0, api_key=os.getenv("GROQ_API_KEY"))
planner_llm = ChatGroq(model="Gemma2-9b-it", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# vectorstore = Chroma(
#     embedding_function=embeddings,
#     collection_name="langgraph",
#     persist_directory="./chroma_db"
# )
# retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# ── PROMPTS ────────────────────────────────────────────
PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a planner for a hostel management assistant. 
You have access to the following tools:
- find_student_by_name: Find a student by name
- create_student: Create a new student
- update_student: Update student details
- delete_student: Delete a student
- delete_student_by_name: Delete student by name
- list_students: List all students
- assign_room: Assign room to student
- assign_room_by_name: Assign room by student name
- create_room: Create a new room
- delete_room: Delete a room
- list_rooms: List all rooms
- update_room: Update room details
- payments_by_name: Get payments by student name
- assign_any_empty_room_by_name: Assign any empty room to student
- create_payment_by_name: Create payment by student name
- set_payments_status_by_name: Update payment status
- rag_tool: Retrieve hostel info (rules, timings, fees)

Always decide which tool(s) to use to answer the query.
If the query is about hostel info, mess timings, hostel fee → use rag_tool.
For student queries, use find_student_by_name or other student tools.
"""),
    ("human", "User request: {input}\n\nReturn a JSON with 'todo' (list of steps with 'action' + 'parameters') and 'summary'.")
])



ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("system", "Conversation summary so far:\n{summary}"),
    MessagesPlaceholder(variable_name="messages"),
    ("system", "Context:\n{context}\nAnswer ONLY from context when possible."),
])

# ── TOOLS ─────────────────────────────────────────────
@tool("find_student_by_name", args_schema=t.FindStudentByNameInput)
async def tool_find_student_by_name(name: str):
    """Find a student in the hostel database by their name."""
    return await t.find_student_by_name(name)

@tool("create_student", args_schema=t.CreateStudentInput)
async def tool_create_student(**kwargs):
    """Create a new student record in the hostel database."""
    return await t.create_student(**kwargs)

@tool("update_student", args_schema=t.UpdateStudentInput)
async def tool_update_student(student_id: int, data: Dict[str, Any]):
    """Update details of a student by student ID."""
    return await t.update_student(student_id, data)

@tool("delete_student", args_schema=t.DeleteStudentInput)
async def tool_delete_student(student_id: int, confirm: bool = False):
    """Delete a student record by ID (requires confirmation)."""
    return await t.delete_student(student_id, confirm)

@tool("delete_student_by_name", args_schema=t.DeleteStudentByNameInput)
async def tool_delete_student_by_name(student_name: str, confirm: bool = False):
    """Delete a student by name (requires confirmation)."""
    return await t.delete_student_by_name(student_name, confirm)

@tool("list_students", args_schema=t.ListStudentsInput)
async def tool_list_students(room_no: str | None = None):
    """List all students, optionally filter by room number."""
    return await t.list_students(room_no)

@tool("assign_room", args_schema=t.AssignRoomInput)
async def tool_assign_room(student_id: int, room_no: str):
    """Assign a room to a student by their ID."""
    return await t.assign_room(student_id, room_no)

@tool("assign_room_by_name", args_schema=t.AssignRoomByNameInput)
async def tool_assign_room_by_name(student_name: str, room_no: str):
    """Assign a room to a student by their name."""
    return await t.assign_room_by_name(student_name, room_no)

@tool("create_room", args_schema=t.CreateRoomInput)
async def tool_create_room(**kwargs):
    """Create a new room in the hostel database."""
    return await t.create_room(**kwargs)

@tool("delete_room", args_schema=t.DeleteRoomInput)
async def tool_delete_room(room_no: str):
    """Delete a room from the hostel database by room number."""
    return await t.delete_room(room_no)

@tool("list_rooms", args_schema=t.ListRoomsInput)
async def tool_list_rooms(status: str | None = None):
    """List all hostel rooms, optionally filter by status (empty/occupied)."""
    return await t.list_rooms(status)

@tool("update_room", args_schema=t.UpdateRoomInput)
async def tool_update_room(room_no: str, data: Dict[str, Any]):
    """Update details of a room by room number."""
    return await t.update_room(room_no, data)

@tool("payments_by_name", args_schema=t.PaymentsByNameInput)
async def tool_payments_by_name(student_name: str):
    """Fetch all payments made by a student (using their name)."""
    return await t.payments_by_name(student_name)

@tool("assign_any_empty_room_by_name", args_schema=t.AssignAnyEmptyRoomByNameInput)
async def tool_assign_any_empty_room_by_name(student_name: str):
    """Assign any available empty room to a student by their name."""
    return await t.assign_any_empty_room_by_name(student_name)

@tool("create_payment_by_name", args_schema=t.CreatePaymentByNameInput)
async def tool_create_payment_by_name(student_name: str, amount: float, status: str | None = None):
    """Create a payment record for a student by their name."""
    return await t.create_payment_by_name(student_name, amount, status)

@tool("set_payments_status_by_name", args_schema=t.SetPaymentsStatusByNameInput)
async def tool_set_payments_status_by_name(student_name: str, status: str, payment_id: int | None = None):
    """Update the payment status of a student by name (optionally by payment ID)."""
    return await t.set_payments_status_by_name(student_name, status, payment_id)

@tool("rag_tool", args_schema=RagToolInput)
async def rag_tool(query: str):
    """Retrieve hostel info (rules, mess timings, fees, etc.) using RAG."""
    try:
        docs = retriever.invoke(query)   # use .invoke, not get_relevant_documents
        if not docs:
            return "No hostel info found."
        return "\n".join([d.page_content for d in docs])
    except Exception as e:
        return f"[RAG error: {e}]"


# Collect tools
TOOLS = [
    tool_find_student_by_name,
    tool_create_student,
    tool_update_student,
    tool_delete_student,
    tool_delete_student_by_name,
    tool_list_students,
    tool_assign_room,
    tool_assign_room_by_name,
    tool_create_room,
    tool_delete_room,
    tool_list_rooms,
    tool_update_room,
    tool_payments_by_name,
    tool_assign_any_empty_room_by_name,
    tool_create_payment_by_name,
    tool_set_payments_status_by_name,
    rag_tool,
]


# Registry: name -> tool
ALL_TOOLS = {tool_.name: tool_ for tool_ in TOOLS}

# ── NODES ─────────────────────────────────────────────
def planner_node(state: AgentState):
    """Generates a plan based on the user's request."""
    user_input = state["messages"][-1].content
    messages = PLANNER_PROMPT.format_messages(input=user_input)
    resp = planner_llm.invoke(messages)

    try:
        parser = PydanticOutputParser(pydantic_object=Plan)
        plan = parser.parse(resp.content).dict()
    except ValidationError as e:
        print(f"Validation Error parsing plan: {e}")
        plan = {"todo": [resp.content], "summary": "Fallback plan"}

    return {"plan": plan, "results": []}

async def executor_node(state: AgentState):
    """Executes the steps defined in the plan."""
    plan = state.get("plan", {})
    todo = plan.get("todo", [])
    results = []

    for step in todo:
        if isinstance(step, dict):
            action = step.get("action", "")
            params = step.get("parameters", {})
        elif hasattr(step, "action"):
            action = step.action
            params = step.parameters
        else:
            action = str(step)
            params = {}

        tool_fn = ALL_TOOLS.get(action)

        if callable(tool_fn):
            try:
                if hasattr(tool_fn, "arun"):
                    result = await tool_fn.arun(params)
                elif hasattr(tool_fn, "func"):
                    result = await tool_fn.func(**params)
                else:
                    result = await tool_fn(**params) if params else await tool_fn(state["messages"][-1].content)
            except Exception as e:
                result = f"[Error executing {action}: {e}]"
        else:
            result = f"Unknown action: {action}"

        results.append(str(result))

    return {"results": results}

def answer_node(state: AgentState) -> AgentState:
    """Generates the final answer to the user."""
    inputs = {
        "summary": state.get("summary", ""),
        "messages": state["messages"][-4:],
        "context": "\n".join(state.get("results", [])),
    }
    response = llm.invoke(ANSWER_PROMPT.format_messages(**inputs))
    state["messages"].append(
        response if isinstance(response, AIMessage) else AIMessage(content=str(response))
    )
    state["summary"] = state.get("plan", {}).get("summary", state.get("summary", ""))
    return state

# ── GRAPH ─────────────────────────────────────────────
graph = StateGraph(AgentState)
graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("answer", answer_node)

# Add docstrings to nodes
planner_node.__doc__ = "Generates a plan based on the user's request."
executor_node.__doc__ = "Executes the steps defined in the plan."
answer_node.__doc__ = "Generates the final answer to the user."

graph.set_entry_point("planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", "answer")
graph.add_edge("answer", END)

app = graph.compile()

# ── RUNNER ────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio

    async def main():
        print("🤖 Hostel Assistant (with tools + chat history). Type 'quit' to exit.")
        state: AgentState = {"messages": [], "plan": {}, "results": [], "summary": "", "context": ""}
        while True:
            q = input("You: ")
            if q.lower() in {"quit", "exit"}:
                break
            state["messages"].append(HumanMessage(content=q))
            state = await app.ainvoke(state)
            print("Bot:", state["messages"][-1].content)

    asyncio.run(main())
