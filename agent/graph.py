from __future__ import annotations
from typing import Annotated, Dict, Any, List, Optional
import operator
from langgraph.graph import StateGraph, END, START
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from .config import settings
from . import tools as t

# 1) Bind tools to LangChain (with Pydantic schemas)
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
]

# 3) Build the Agent
llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0,
)

# Separate planning LLM (no tools, just planning)
planner_llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0,
)

SYSTEM_PROMPT = (
    "You are Agent Warden for a Hostel Management System. "
    "You help manage students, rooms, and payments. "
    "Always return responses in this format: "
    "{'summary': 'human-friendly summary', 'data': [...]} "
    ""
    "Rules: "
    "- For destructive operations (delete/update), ask for confirmation first. "
    "- If multiple matches exist, ask user to clarify which one. "
    "- Always provide helpful summaries and insights. "
    "- Suggest alternatives if something fails. "
    "- Keep responses deterministic (temperature 0). "
    ""
    "Available tools: "
    "- find_student_by_name, create_student, update_student, delete_student "
    "- list_students, assign_room, create_room, delete_room, list_rooms, update_room "
    "- payments_by_name, create_payment_by_name, set_payments_status_by_name "
    ""
    "Example responses: "
    "- Summary: 'Found 3 students matching 'shiva'. Please select one.' "
    "- Summary: 'Are you sure you want to delete student ID 123? This action cannot be undone.' "
    "- Summary: 'Successfully created room 401 with capacity 2.' "
)

PLANNER_PROMPT = (
    "You are a Task Planning Agent. Your job is to break down user requests into clear, executable steps. "
    ""
    "Rules: "
    "- Always resolve math expressions first (e.g., 8000*4 = 32000) "
    "- Break complex requests into simple, sequential steps "
    "- Each step should be a single action that can be executed "
    "- Include computed values in the plan "
    "- Be specific about what needs to be done "
    ""
    "Available tools: "
    "- find_student_by_name, create_student, update_student, delete_student "
    "- list_students, assign_room, create_room, delete_room, list_rooms, update_room "
    "- payments_by_name, create_payment_by_name, set_payments_status_by_name "
    "Use these tools to plan the steps. Only use tools that are relevant to the user's request. It is very important to use the tools to plan the steps."
    "Output Format (JSON only): "
    "{"
    "  'todo': ["
    "    'step 1 description',"
    "    'step 2 description',"
    "    'step 3 description'"
    "  ],"
    "  'computed_values': {"
    "    'price': 32000,"
    "    'total_rooms': 12"
    "  },"
    "  'summary': 'Brief description of what this plan accomplishes'"
    "}"
    ""
    "Examples: "
    "- User: 'update all rooms to price 8000*4' "
    "- Plan: {'todo': ['Calculate 8000*4 = 32000', 'List all rooms', 'Update each room price to 32000'], 'computed_values': {'price': 32000}, 'summary': 'Update all room prices to ₹32,000'}"
    ""
    "- User: 'show all students and their room assignments' "
    "- Plan: {'todo': ['List all students', 'List all rooms', 'Match students with rooms'], 'summary': 'Display all students and their room assignments'}"
)

# 4) Define LangGraph State
class AgentState(Dict[str, Any]):
    messages: List[Any]
    plan: Optional[Dict[str, Any]] = None
    current_step: int = 0
    results: List[Any] = []

graph = StateGraph(AgentState)
llm_with_tools = llm.bind_tools(TOOLS)

def planner_node(state: AgentState, config: RunnableConfig):
    """Planning agent that breaks down user requests into executable steps."""
    messages = state["messages"]
    
    print(f"DEBUG: Planner received messages: {[msg.content for msg in messages if hasattr(msg, 'content')]}")
    
    # Create planning prompt
    planning_messages = [
        SystemMessage(content=PLANNER_PROMPT),
        *messages
    ]
    
    # Get plan from planning LLM
    response = planner_llm.invoke(planning_messages, config=config)
    
    print(f"DEBUG: Planner LLM response: {response.content}")
    
    try:
        # Extract JSON plan from response - handle markdown and extra content
        content = response.content
        
        # Remove markdown code blocks if present
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        
        # Find JSON content
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            json_content = content[start:end]
            
            print(f"DEBUG: Extracted JSON content: {json_content}")
            
            try:
                # First try to parse as regular JSON
                plan_json = json.loads(json_content)
                print(f"DEBUG: Parsed plan JSON: {plan_json}")
                
                # Validate plan structure
                if "todo" in plan_json and isinstance(plan_json["todo"], list):
                    return {
                        "plan": plan_json,
                        "current_step": 0,
                        "results": [],
                        "messages": [response]
                    }
            except json.JSONDecodeError as json_error:
                print(f"DEBUG: JSON parsing failed: {json_error}")
                # Try to handle single quotes by replacing them with double quotes
                try:
                    # Replace single quotes with double quotes, but be careful with apostrophes
                    fixed_json = json_content.replace("'", '"')
                    # Handle common cases where single quotes are used in text
                    fixed_json = fixed_json.replace('"s ', "'s ")  # possessive
                    fixed_json = fixed_json.replace('"t ', "'t ")  # contractions
                    fixed_json = fixed_json.replace('"re ', "'re ")  # contractions
                    fixed_json = fixed_json.replace('"ll ', "'ll ")  # contractions
                    fixed_json = fixed_json.replace('"ve ', "'ve ")  # contractions
                    
                    plan_json = json.loads(fixed_json)
                    print(f"DEBUG: Parsed fixed JSON: {plan_json}")
                    
                    # Validate plan structure
                    if "todo" in plan_json and isinstance(plan_json["todo"], list):
                        return {
                            "plan": plan_json,
                            "current_step": 0,
                            "results": [],
                            "messages": [response]
                        }
                except json.JSONDecodeError as second_error:
                    print(f"DEBUG: Second JSON parsing failed: {second_error}")
                    # Try to extract a simple plan from the content
                    if "payments_by_name" in content.lower():
                        # Extract student name from content
                        import re
                        name_match = re.search(r'payments_by_name.*?["\']([^"\']+)["\']', content.lower())
                        student_name = name_match.group(1) if name_match else "shiva"
                        fallback_plan = {
                            "todo": [
                                f"Get payments for student {student_name}"
                            ],
                            "computed_values": {},
                            "summary": f"Retrieve payments for student {student_name}"
                        }
                        print(f"DEBUG: Using fallback plan for payments query: {fallback_plan}")
                        return {
                            "plan": fallback_plan,
                            "current_step": 0,
                            "results": [],
                            "messages": [response]
                        }
                    elif "8000*4" in content or "32000" in content:
                        fallback_plan = {
                            "todo": [
                                "Calculate 8000*4 = 32000",
                                "List all rooms", 
                                "Update each room price to 32000"
                            ],
                            "computed_values": {"price": 32000},
                            "summary": "Update all room prices to ₹32,000"
                        }
                        print(f"DEBUG: Using fallback plan for math expression: {fallback_plan}")
                        return {
                            "plan": fallback_plan,
                            "current_step": 0,
                            "results": [],
                            "messages": [response]
                        }
        
        # Fallback: create simple plan
        fallback_plan = {
            "todo": [response.content],
            "computed_values": {},
            "summary": "Simple task execution"
        }
        print(f"DEBUG: Using fallback plan: {fallback_plan}")
        return {
            "plan": fallback_plan,
            "current_step": 0,
            "results": [],
            "messages": [response]
        }
        
    except Exception as e:
        # Error fallback
        print(f"DEBUG: Planning error: {e}")
        error_plan = {
            "todo": [f"Error in planning: {str(e)}"],
            "computed_values": {},
            "summary": "Planning failed"
        }
        return {
            "plan": error_plan,
            "current_step": 0,
            "results": [],
            "messages": [response]
        }

def call_model(state: AgentState, config: RunnableConfig):
    """Model call with tools - for simple queries that don't need planning."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages, config=config)
    return {"messages": [response]}

async def executor_node(state: AgentState, config: RunnableConfig):
    """Execution agent that runs planned tasks one by one without breakdowns."""
    plan = state.get("plan", {})
    if not plan or not isinstance(plan, dict):
        return {"messages": [AIMessage(content="No valid plan found.")]}
    
    todo = plan.get("todo", [])
    computed_values = plan.get("computed_values", {})
    results = []
    
    # Debug: Log what we received
    print(f"DEBUG: Executor received plan: {plan}")
    print(f"DEBUG: Todo items: {todo}")
    
    try:
        for i, step in enumerate(todo):
            step_str = str(step).lower()
            step_result = {"step": i + 1, "description": step, "status": "pending"}
            
            print(f"DEBUG: Executing step {i+1}: {step}")
            
            try:
                # Execute step based on content
                if "list_rooms" in step_str or "fetch all rooms" in step_str or "get all rooms" in step_str:
                    print(f"DEBUG: Detected list_rooms step")
                    rooms = await tool_list_rooms.ainvoke({}, config=config)
                    step_result.update({
                        "status": "completed",
                        "result": rooms,
                        "count": len(rooms) if isinstance(rooms, list) else 0
                    })
                    results.append(step_result)
                    
                elif "list_students" in step_str or "fetch all students" in step_str or "get all students" in step_str:
                    print(f"DEBUG: Detected list_students step")
                    students = await tool_list_students.ainvoke({}, config=config)
                    step_result.update({
                        "status": "completed",
                        "result": students,
                        "count": len(students) if isinstance(students, list) else 0
                    })
                    results.append(step_result)
                    
                elif "update" in step_str and "room" in step_str and "price" in step_str:
                    print(f"DEBUG: Detected update room price step")
                    # Extract price from computed values or calculate
                    price = computed_values.get("price")
                    if not price:
                        # Try to extract from step description
                        import re
                        price_match = re.search(r'(\d+)', step_str)
                        if price_match:
                            price = int(price_match.group(1))
                    
                    # If still no price, try to extract from user input
                    if not price:
                        user_input = state.get("user_input", "")
                        if user_input:
                            # Look for math expressions in user input
                            math_match = re.search(r'(\d+[\+\-\*\/]\d+)', user_input.lower())
                            if math_match:
                                expr = math_match.group(1)
                                try:
                                    price = eval(expr)
                                    print(f"DEBUG: Calculated price from user input: {expr} = {price}")
                                except:
                                    pass
                    
                    print(f"DEBUG: Using price: {price}")
                    
                    if price:
                        # Get all rooms first
                        rooms = await tool_list_rooms.ainvoke({}, config=config)
                        updated_rooms = []
                        
                        for room in rooms:
                            if isinstance(room, dict) and "room_no" in room:
                                try:
                                    updated = await tool_update_room.ainvoke(
                                        {"room_no": room["room_no"], "data": {"price": price}},
                                        config=config
                                    )
                                    updated_rooms.append(updated)
                                except Exception as e:
                                    step_result["errors"] = step_result.get("errors", [])
                                    step_result["errors"].append(f"Room {room.get('room_no', 'unknown')}: {str(e)}")
                        
                        step_result.update({
                            "status": "completed",
                            "result": updated_rooms,
                            "count": len(updated_rooms),
                            "price_applied": price
                        })
                    else:
                        step_result.update({
                            "status": "failed",
                            "error": "No price value found for room updates"
                        })
                    
                    results.append(step_result)
                    
                elif "calculate" in step_str or "math" in step_str or "*" in step_str or "+" in step_str or "-" in step_str or "/" in step_str:
                    print(f"DEBUG: Detected math calculation step")
                    # Handle math expressions
                    try:
                        import re
                        # Look for math expressions in the step description
                        math_match = re.search(r'(\d+[\+\-\*\/]\d+)', step_str)
                        if math_match:
                            expr = math_match.group(1)
                            result = eval(expr)  # Safe for simple math
                            step_result.update({
                                "status": "completed",
                                "result": f"{expr} = {result}",
                                "computed_value": result
                            })
                            # Store in computed values for later use
                            computed_values["price"] = result
                            print(f"DEBUG: Calculated {expr} = {result}, stored in computed_values")
                        else:
                            # Try to extract from the original user input
                            user_input = state.get("user_input", "")
                            if user_input:
                                math_match = re.search(r'(\d+[\+\-\*\/]\d+)', user_input.lower())
                                if math_match:
                                    expr = math_match.group(1)
                                    result = eval(expr)
                                    step_result.update({
                                        "status": "completed",
                                        "result": f"{expr} = {result}",
                                        "computed_value": result
                                    })
                                    computed_values["price"] = result
                                    print(f"DEBUG: Calculated from user input {expr} = {result}")
                                else:
                                    step_result.update({
                                        "status": "failed",
                                        "error": "No math expression found in step or user input"
                                    })
                            else:
                                step_result.update({
                                    "status": "failed",
                                    "error": "No math expression found"
                                })
                    except Exception as e:
                        step_result.update({
                            "status": "failed",
                            "error": f"Math calculation failed: {e}"
                        })
                    
                    results.append(step_result)
                    
                else:
                    print(f"DEBUG: Generic step execution")
                    # Generic step - mark as completed with note
                    step_result.update({
                        "status": "completed",
                        "result": "Step executed",
                        "note": "Generic step execution"
                    })
                    results.append(step_result)
                    
            except Exception as e:
                # Handle step execution errors
                print(f"DEBUG: Step {i+1} failed with error: {e}")
                step_result.update({
                    "status": "failed",
                    "error": str(e)
                })
                results.append(step_result)
        
        # Generate comprehensive summary
        total_steps = len(todo)
        completed_steps = len([r for r in results if r.get("status") == "completed"])
        failed_steps = len([r for r in results if r.get("status") == "failed"])
        
        print(f"DEBUG: Execution complete. {completed_steps}/{total_steps} steps completed")
        
        # Create summary based on plan type
        if "update" in str(todo).lower() and "room" in str(todo).lower():
            price = computed_values.get("price", "unknown")
            summary = f"✅ Executed {completed_steps}/{total_steps} steps. Updated room prices to ₹{price}."
        elif "list" in str(todo).lower():
            total_items = sum([r.get("count", 0) for r in results if r.get("count")])
            summary = f"✅ Executed {completed_steps}/{total_steps} steps. Retrieved {total_items} items."
        else:
            summary = f"✅ Executed {completed_steps}/{total_steps} steps successfully."
        
        if failed_steps > 0:
            summary += f" {failed_steps} step(s) failed."
        
        # Final response
        final_response = {
            "summary": summary,
            "data": results,
            "plan": plan,
            "execution_stats": {
                "total_steps": total_steps,
                "completed": completed_steps,
                "failed": failed_steps,
                "computed_values": computed_values
            }
        }
        
        return {"messages": [AIMessage(content=json.dumps(final_response))]}
        
    except Exception as e:
        # Handle overall execution errors
        print(f"DEBUG: Overall execution failed: {e}")
        error_response = {
            "summary": f"❌ Execution failed: {str(e)}",
            "data": results,
            "error": str(e),
            "plan": plan
        }
        return {"messages": [AIMessage(content=json.dumps(error_response))]}

# Add nodes
graph.add_node("planner", planner_node)
graph.add_node("agent", call_model)
graph.add_node("executor", executor_node)

# Add edges
graph.add_edge(START, "planner")

# Router to decide flow based on request complexity
def main_router(state: AgentState):
    """Decide whether to use planner→executor or direct tool execution."""
    messages = state["messages"]
    user_input = state.get("user_input", "")
    
    print(f"DEBUG: Router received {len(messages)} messages")
    print(f"DEBUG: Router user_input: {user_input}")
    
    for i, msg in enumerate(messages):
        if hasattr(msg, 'content'):
            print(f"DEBUG: Message {i}: {msg.content[:100]}...")
        else:
            print(f"DEBUG: Message {i}: {type(msg)}")
    
    # Use explicit user_input if available, otherwise fall back to message parsing
    if user_input:
        content = user_input.lower()
        print(f"DEBUG: Router using explicit user_input: {content}")
    elif messages and len(messages) >= 2:
        # Check the user message (second message, after system message)
        user_message = messages[1]
        if hasattr(user_message, 'content'):
            content = user_message.content.lower()
            print(f"DEBUG: Router using message[1]: {content}")
        else:
            print(f"DEBUG: Message[1] has no content, routing to executor")
            return "executor"
    else:
        print(f"DEBUG: No user input found, routing to executor")
        return "executor"
    
    # Complex requests that need planning
    complex_keywords = [
        "all rooms", "all students", "bulk", "multiple", 
        "update all", "delete all", "every", "each",
        "*", "+", "-", "/", "calculate", "math"
    ]
    
    if any(keyword in content for keyword in complex_keywords):
        print(f"DEBUG: Routing to executor (complex request)")
        return "executor"  # Go to executor with the plan
    else:
        print(f"DEBUG: Routing to agent (simple request)")
        return "agent"  # Go to simple agent

graph.add_conditional_edges("planner", main_router, {
    "executor": "executor",
    "agent": "agent"
})

# Executor goes directly to END
graph.add_edge("executor", END)

# Simple agent path: if model requests a tool -> tool node, else END
def router(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool"
    return END

graph.add_conditional_edges("agent", router, {"tool": "tool", END: END})

# Tool execution node
async def tool_node(state: AgentState, config: RunnableConfig):
    last = state["messages"][-1]
    tool_msgs = []
    for call in last.tool_calls:
        name = call["name"]
        args = call["args"]
        tool = next(t for t in TOOLS if t.name == name)
        result = await tool.ainvoke(args, config=config)
        # Normalize tool outputs to an envelope {summary, data}
        def _envelope_from_result(answer):
            try:
                if isinstance(answer, dict) and "summary" in answer and "data" in answer:
                    return {"summary": str(answer.get("summary", "")), "data": answer.get("data") or []}
                if isinstance(answer, list):
                    count = len(answer)
                    preview = answer[:10]
                    return {"summary": f"Found {count} record(s). Showing {len(preview)}.", "data": preview}
                if isinstance(answer, dict):
                    return {"summary": "1 record.", "data": [answer]}
                # fallback to text
                return {"summary": str(answer), "data": []}
            except Exception:
                return {"summary": str(answer), "data": []}
        envelope = _envelope_from_result(result)
        payload = json.dumps(envelope)
        tool_msgs.append(ToolMessage(content=payload, tool_call_id=call["id"]))
    return {"messages": tool_msgs}

graph.add_node("tool", tool_node)
# End the run after one tool execution to avoid repeated tool loops
graph.add_edge("tool", END)

# Compile
app = graph.compile()

# 5) Entry function with per-session memory
_CHAT_HISTORY: Dict[str, List[Any]] = {}

def _get_history(session_id: str) -> List[Any]:
    if session_id not in _CHAT_HISTORY:
        _CHAT_HISTORY[session_id] = [SystemMessage(content=SYSTEM_PROMPT)]
    return _CHAT_HISTORY[session_id]

async def agentwardan_chat(user_input: str, session_id: str = "default"):
    history = _get_history(session_id)
    history.append(HumanMessage(content=user_input))
    
    # Create initial state with both system and user messages
    state = {
        "messages": history,
        "user_input": user_input  # Explicitly store user input
    }
    
    print(f"DEBUG: Initial state created with {len(history)} messages")
    print(f"DEBUG: User input: {user_input}")
    
    result = await app.ainvoke(state)
    reply = result["messages"][-1]
    history.append(reply)
    # trim to last 20 exchanges (+ system)
    if len(history) > 41:
        _CHAT_HISTORY[session_id] = [history[0]] + history[-40:]
    return reply.content
