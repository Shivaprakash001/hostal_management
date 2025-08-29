from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
import ast
import operator as op
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from .config import settings
from . import tools as t

# ---------------------------
# Helpers
# ---------------------------

def _safe_eval(expr: str) -> float:
    """
    Safely evaluate simple arithmetic expressions like '8000*4' or '10000*3+500'.
    Supports + - * / // % ** and parentheses and integers/floats.
    """
    allowed_ops = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
        ast.FloorDiv: op.floordiv, ast.Mod: op.mod, ast.Pow: op.pow,
        ast.UAdd: op.pos, ast.USub: op.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Num):  # Py<3.8
            return node.n
        if isinstance(node, ast.Constant):  # Py>=3.8 numbers
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants allowed")
        if isinstance(node, ast.BinOp):
            if type(node.op) not in allowed_ops:
                raise ValueError("Operator not allowed")
            return allowed_ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in allowed_ops:
                raise ValueError("Operator not allowed")
            return allowed_ops[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.Expr):
            return _eval(node.value)
        raise ValueError("Unsupported expression")

    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body)

# ---------------------------
# 1) Bind tools to LangChain (with Pydantic schemas)
# ---------------------------

@tool("find_student_by_name", args_schema=t.FindStudentByNameInput)
async def tool_find_student_by_name(name: str):
    """Find students by name (partial match)."""
    return await t.find_student_by_name(name)

@tool("create_student", args_schema=t.CreateStudentInput)
async def tool_create_student(**kwargs):
    """Create a new student with optional phone/email/room_no."""
    return await t.create_student(**kwargs)

@tool("update_student", args_schema=t.UpdateStudentInput)
async def tool_update_student(student_id: int, data: Dict[str, Any]):
    """Update a student's fields (name, room_no, phone_no, etc.)."""
    return await t.update_student(student_id, data)

@tool("delete_student", args_schema=t.DeleteStudentInput)
async def tool_delete_student(student_id: int, confirm: bool = False):
    """Delete a student by ID. Requires confirmation."""
    return await t.delete_student(student_id, confirm)

@tool("delete_student_by_name", args_schema=t.DeleteStudentByNameInput)
async def tool_delete_student_by_name(student_name: str, confirm: bool = False):
    """Delete a student by name. Handles disambiguation and requires confirmation."""
    return await t.delete_student_by_name(student_name, confirm)

@tool("list_students", args_schema=t.ListStudentsInput)
async def tool_list_students(room_no: str | None = None):
    """List students, optionally filtered by room_no."""
    return await t.list_students(room_no)

@tool("assign_room", args_schema=t.AssignRoomInput)
async def tool_assign_room(student_id: int, room_no: str):
    """Assign a room to a student."""
    return await t.assign_room(student_id, room_no)

@tool("assign_room_by_name", args_schema=t.AssignRoomByNameInput)
async def tool_assign_room_by_name(student_name: str, room_no: str):
    """Assign a room to a student identified by name (first match)."""
    return await t.assign_room_by_name(student_name, room_no)

@tool("create_room", args_schema=t.CreateRoomInput)
async def tool_create_room(**kwargs):
    """Create a room with room_no, capacity, price/status if supported."""
    return await t.create_room(**kwargs)

@tool("delete_room", args_schema=t.DeleteRoomInput)
async def tool_delete_room(room_no: str):
    """Delete a room by room number."""
    return await t.delete_room(room_no)

@tool("list_rooms", args_schema=t.ListRoomsInput)
async def tool_list_rooms(status: str | None = None):
    """List rooms, optionally filtered by status (available/occupied)."""
    return await t.list_rooms(status)

@tool("update_room", args_schema=t.UpdateRoomInput)
async def tool_update_room(room_no: str, data: Dict[str, Any]):
    """Update a room's fields by room_no (capacity, status, price, etc.)."""
    return await t.update_room(room_no, data)

@tool("payments_by_name", args_schema=t.PaymentsByNameInput)
async def tool_payments_by_name(student_name: str):
    """List payments for the first student matching the given name."""
    return await t.payments_by_name(student_name)

@tool("assign_any_empty_room_by_name", args_schema=t.AssignAnyEmptyRoomByNameInput)
async def tool_assign_any_empty_room_by_name(student_name: str):
    """Assign the first empty room found to the named student."""
    return await t.assign_any_empty_room_by_name(student_name)

@tool("create_payment_by_name", args_schema=t.CreatePaymentByNameInput)
async def tool_create_payment_by_name(student_name: str, amount: float, status: str | None = None):
    """Create a payment for a student by name with given amount and optional status."""
    return await t.create_payment_by_name(student_name, amount, status)

@tool("set_payments_status_by_name", args_schema=t.SetPaymentsStatusByNameInput)
async def tool_set_payments_status_by_name(student_name: str, status: str, payment_id: int | None = None):
    """Set status for all payments (or a specific payment_id) for a student by name."""
    return await t.set_payments_status_by_name(student_name, status, payment_id)

# --- NEW: Safe arithmetic as a tool ---
@tool("evaluate_expression")
async def tool_evaluate_expression(expression: str):
    """Safely evaluate arithmetic expressions like '8000*4'."""
    try:
        return {"summary": f"Calculated {expression}", "data": [{"expression": expression, "value": _safe_eval(expression)}]}
    except Exception as e:
        return {"summary": f"Failed to calculate {expression}", "data": [], "error": str(e)}

# 2) Collect all tools
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
    tool_evaluate_expression,
]

# 3) Build the LLMs
llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0,
)
planner_llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0,
)

SYSTEM_PROMPT = (
    "You are Agent Warden for a Hostel Management System.\n"
    "Act as an execution-planner + tool-using agent.\n"
    "Always:\n"
    "  1) Parse the user query.\n"
    "  2) If complex/bulk or includes math, plan steps first.\n"
    "  3) Execute tools step-by-step until done.\n"
    "  4) Return JSON only: {'summary': '<human>', 'data': [...]}.\n"
    "Rules:\n"
    "- Disambiguate if multiple matches exist; ask which one.\n"
    "- For destructive ops (delete/update), ask for confirmation before executing.\n"
    "- Provide counts and insights (totals, first 10, etc.).\n"
    "- Suggest alternatives if something fails (e.g., room full -> suggest next available).\n"
    "- Deterministic outputs.\n"
)

PLANNER_PROMPT = (
    "You are a Task Planning Agent. Break the user's request into executable steps.\n"
    "Resolve math expressions up front (e.g., 8000*4=32000). Be explicit and sequential.\n"
    "Output strictly JSON with keys: todo (list of steps), computed_values (dict), summary (string).\n"
    "Example for 'update all rooms to price 8000*4':\n"
    "{\n"
    "  \"todo\": [\"Calculate 8000*4\", \"List all rooms\", \"Update each room price to 32000\"],\n"
    "  \"computed_values\": {\"price\": 32000},\n"
    "  \"summary\": \"Update all room prices to ₹32,000\"\n"
    "}\n"
)

# 4) Define LangGraph State
class AgentState(Dict[str, Any]):
    messages: List[Any]
    plan: Optional[Dict[str, Any]]
    current_step: int
    results: List[Any]

graph = StateGraph(AgentState)
llm_with_tools = llm.bind_tools(TOOLS)

# ---------------------------
# Nodes
# ---------------------------

def planner_node(state: AgentState, config: RunnableConfig):
    """Create a plan for complex/bulk requests."""
    messages = state["messages"]
    planning_messages = [SystemMessage(content=PLANNER_PROMPT), *messages]
    response = planner_llm.invoke(planning_messages, config=config)

    content = response.content or ""
    # Extract JSON chunk if LLM wraps
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        plan_json = json.loads(content[start:end])
        if not isinstance(plan_json, dict) or "todo" not in plan_json:
            raise ValueError("Invalid planner JSON")
    except Exception:
        # fallback minimal plan
        plan_json = {"todo": [content], "computed_values": {}, "summary": "Simple execution"}

    # Keep previous messages + planner response for traceability
    return {
        "plan": plan_json,
        "current_step": 0,
        "results": [],
        "messages": messages + [response],
    }

def call_model(state: AgentState, config: RunnableConfig):
    """Simple agent path (no planning), but can use tools; loops via agent<->tool."""
    messages = state["messages"]
    response = llm_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT), *messages], config=config)
    return {"messages": [response]}

async def executor_node(state: AgentState, config: RunnableConfig):
    """Execute planned steps one by one; keep looping until all steps are done."""
    plan = state.get("plan") or {}
    todo: List[str] = list(plan.get("todo", []))
    computed_values: Dict[str, Any] = dict(plan.get("computed_values", {}))
    step_idx = state.get("current_step", 0)
    results = list(state.get("results", []))

    if not todo:
        return {"messages": [AIMessage(content=json.dumps({"summary": "No steps to execute", "data": [], "plan": plan}))]}

    if step_idx >= len(todo):
        # Finished
        total_steps = len(todo)
        completed = len([r for r in results if r.get("status") == "completed"])
        failed = len([r for r in results if r.get("status") == "failed"])
        summary = f"✅ Plan completed. {completed}/{total_steps} steps done."
        if failed:
            summary += f" {failed} step(s) failed."
        final = {
            "summary": summary,
            "data": results,
            "plan": plan,
            "execution_stats": {
                "total_steps": total_steps,
                "completed": completed,
                "failed": failed,
                "computed_values": computed_values,
            },
        }
        return {"messages": [AIMessage(content=json.dumps(final))]}

    step = str(todo[step_idx])
    step_l = step.lower()
    step_result = {"step": step_idx + 1, "description": step, "status": "pending"}

    try:
        # 1) Math / Calculate
        if "calculate" in step_l or any(o in step for o in ["*", "+", "-", "/", "//", "%"]):
            val_payload = await tool_evaluate_expression.ainvoke({"expression": step.replace("calculate", "").strip()}, config=config)
            # normalize tool_evaluate_expression output
            if isinstance(val_payload, dict) and "data" in val_payload and val_payload["data"]:
                val = val_payload["data"][0].get("value")
            else:
                val = None
            if val is not None:
                # Heuristic: if the plan referenced "price", store it
                if "price" in step_l or "room price" in step_l:
                    computed_values["price"] = val
                computed_values["last_calc"] = val
                step_result.update({"status": "completed", "result": val})
            else:
                step_result.update({"status": "failed", "error": "Could not compute value"})

        # 2) List Rooms
        elif "list all rooms" in step_l or "list rooms" in step_l or "fetch all rooms" in step_l or "get all rooms" in step_l:
            rooms = await tool_list_rooms.ainvoke({}, config=config)
            count = len(rooms) if isinstance(rooms, list) else 0
            step_result.update({"status": "completed", "result": rooms, "count": count})

        # 3) List Students
        elif "list all students" in step_l or "list students" in step_l or "fetch all students" in step_l:
            students = await tool_list_students.ainvoke({}, config=config)
            count = len(students) if isinstance(students, list) else 0
            step_result.update({"status": "completed", "result": students, "count": count})

        # 4) Bulk Update Room Price
        elif "update each room price" in step_l or ("update" in step_l and "room" in step_l and "price" in step_l):
            price = computed_values.get("price") or computed_values.get("last_calc")
            if price is None:
                step_result.update({"status": "failed", "error": "No price value to apply"})
            else:
                rooms = await tool_list_rooms.ainvoke({}, config=config)
                updates = []
                errors = []
                if isinstance(rooms, list):
                    for r in rooms:
                        try:
                            updated = await tool_update_room.ainvoke({"room_no": r["room_no"], "data": {"price": price}}, config=config)
                            updates.append(updated)
                        except Exception as e:
                            errors.append({"room_no": r.get("room_no"), "error": str(e)})
                step_result.update({"status": "completed", "result": updates, "count": len(updates)})
                if errors:
                    step_result["errors"] = errors

        # 5) Generic step marker (no-op)
        else:
            step_result.update({"status": "completed", "note": "Step acknowledged (no specific action)"})

    except Exception as e:
        step_result.update({"status": "failed", "error": str(e)})

    results.append(step_result)

    # Advance to next step (loop again)
    return {
        "messages": state["messages"],
        "plan": {**plan, "computed_values": computed_values},
        "current_step": step_idx + 1,
        "results": results,
    }

# Tool execution node (simple path)
async def tool_node(state: AgentState, config: RunnableConfig):
    last = state["messages"][-1]
    tool_msgs = []
    for call in getattr(last, "tool_calls", []) or []:
        name = call["name"]
        args = call["args"] or {}
        bound = next(tl for tl in TOOLS if tl.name == name)
        result = await bound.ainvoke(args, config=config)

        # Normalize to {summary, data}
        def _envelope(ans):
            if isinstance(ans, dict) and "summary" in ans and "data" in ans:
                return {"summary": str(ans.get("summary", "")), "data": ans.get("data") or []}
            if isinstance(ans, list):
                preview = ans[:10]
                return {"summary": f"Found {len(ans)} record(s). Showing {len(preview)}.", "data": preview}
            if isinstance(ans, dict):
                return {"summary": "1 record.", "data": [ans]}
            return {"summary": str(ans), "data": []}

        envelope = _envelope(result)
        tool_msgs.append(ToolMessage(content=json.dumps(envelope), tool_call_id=call["id"]))
    return {"messages": tool_msgs}

# ---------------------------
# Graph wiring
# ---------------------------

graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("agent", call_model)
graph.add_node("tool", tool_node)

# Start → planner
graph.add_edge(START, "planner")

# Decide path after planning: complex → executor, simple → agent
def main_router(state: AgentState):
    msgs = state.get("messages", [])
    if not msgs:
        return "executor"
    # Check *latest* human message for complexity
    human_msgs = [m for m in msgs if isinstance(m, HumanMessage)]
    text = (human_msgs[-1].content.lower() if human_msgs else "").strip()

    complex_keywords = [
        "all rooms", "all students", "bulk", "multiple",
        "update all", "delete all", "every", "each",
        "*", "+", "-", "/", "//", "%", "calculate", "math"
    ]
    if any(k in text for k in complex_keywords):
        return "executor"
    return "agent"

graph.add_conditional_edges("planner", main_router, {"executor": "executor", "agent": "agent"})

# Executor loops until done
def executor_router(state: AgentState):
    plan = state.get("plan") or {}
    total = len(plan.get("todo", []))
    idx = state.get("current_step", 0)
    if idx < total:
        return "executor"
    return END

graph.add_conditional_edges("executor", executor_router, {"executor": "executor", END: END})

# Simple path: agent ⇄ tool loop until no more tool calls
def simple_router(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool"
    return END

graph.add_conditional_edges("agent", simple_router, {"tool": "tool", END: END})
graph.add_edge("tool", "agent")  # allow multiple tool iterations

# Compile
app = graph.compile()

# 5) Entry with per-session memory
_CHAT_HISTORY: Dict[str, List[Any]] = {}

def _get_history(session_id: str) -> List[Any]:
    if session_id not in _CHAT_HISTORY:
        _CHAT_HISTORY[session_id] = [SystemMessage(content=SYSTEM_PROMPT)]
    return _CHAT_HISTORY[session_id]

async def agentwardan_chat(user_input: str, session_id: str = "default"):
    history = _get_history(session_id)
    history.append(HumanMessage(content=user_input))
    state = {"messages": history, "plan": None, "current_step": 0, "results": []}
    result = await app.ainvoke(state)
    reply = result["messages"][-1]
    history.append(reply)
    # trim to last 20 exchanges (+ system)
    if len(history) > 41:
        _CHAT_HISTORY[session_id] = [history[0]] + history[-40:]
    return reply.content
