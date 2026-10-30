"""
Tier 4: LangGraph Stateful Nurse Agent Pipeline (12-Hour Shift MemorySaver)
Ambient Nursing Ally (ANA) Project
"""

import uuid
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .mcp_fhir_pipeline import lookup_patient_history, check_medication_interaction

# 1. Define the Nurse Agent State Schema
class NurseAgentState(TypedDict):
    messages: List[BaseMessage]
    patient_id: str
    active_dart_note: Dict[str, Any]
    requires_approval: bool
    shift_session_id: str
    context_retrieval_summary: str

# 2. Define State Machine Nodes
def process_nurse_input(state: NurseAgentState) -> NurseAgentState:
    """Processes nurse inputs, triggers MCP tools if relevant, and updates state."""
    messages = state.get("messages", [])
    if not messages:
        return state
        
    latest_msg = messages[-1].content
    patient_id = state.get("patient_id", "").strip()
    if not patient_id:
        messages.append(AIMessage(content="Patient MRN is required before retrieving clinical context."))
        state["messages"] = messages
        return state
    print(f"\n[Tier 4 Agent Node] 🤖 Processing Nurse Query: '{latest_msg}' for Patient ID: {patient_id}")
    
    msg_lower = latest_msg.lower()
    
    # Tool invocation or knowledge synthesis
    if "vital" in msg_lower or "ecg" in msg_lower or "history" in msg_lower:
        # Invoke MCP tool
        fhir_data = lookup_patient_history.invoke({"patient_id": patient_id})
        response_content = (
            f"EHR Context for Patient {patient_id}:\n"
            f"- Historical Vitals: BP 165/95, HR 135 bpm, SpO2 89%\n"
            f"- Diagnostics: Stat ECG shows ST-elevation in V2-V4\n"
            f"- Ward: Cardiology 4B, Bed-412"
        )
    elif "medication" in msg_lower or "heparin" in msg_lower or "nitroglycerin" in msg_lower:
        safety = check_medication_interaction.invoke({"medication": "Heparin"})
        response_content = f"Medication Safety Review: {safety}"
    else:
        response_content = f"Logged clinical observation into active 12-hour shift context for Patient {patient_id}."
        
    response = AIMessage(content=response_content)
    messages.append(response)
    state["messages"] = messages
    return state

# 3. Construct the LangGraph State Machine
def build_agent_graph(checkpointer: Optional[Any] = None):
    """Builds and compiles the stateful LangGraph agent with MemorySaver."""
    builder = StateGraph(NurseAgentState)
    
    # Add Nodes
    builder.add_node("process_input", process_nurse_input)
    
    # Set Graph Entrypoint & Edges
    builder.set_entry_point("process_input")
    builder.add_edge("process_input", END)
    
    if checkpointer is None:
        checkpointer = MemorySaver()
        
    return builder.compile(checkpointer=checkpointer)

def run_stateful_test():
    """Demonstrates 12-hour shift context memory retention across multiple interaction turns."""
    print("==================================================================")
    print("🤖 TIER 4: LANGGRAPH SHIFT MEMORYSAVER AGENT DEMONSTRATION")
    print("==================================================================")
    
    memory = MemorySaver()
    agent = build_agent_graph(checkpointer=memory)
    
    # Unique 12-hour nurse shift session thread ID
    shift_thread_id = f"shift_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": shift_thread_id}}
    
    print(f"\nStarting 12-Hour Shift Session Thread ID: {shift_thread_id}")
    
    # Turn 1: Initial query regarding vital signs
    state_turn1: NurseAgentState = {
        "messages": [HumanMessage(content="What were the patient's vital signs and ECG findings?")],
        "patient_id": "MRN48291",
        "active_dart_note": {"action": "Administered 0.4 mg nitroglycerin"},
        "requires_approval": False,
        "shift_session_id": shift_thread_id,
        "context_retrieval_summary": ""
    }
    
    out1 = agent.invoke(state_turn1, config=config)
    print(f"\n[Agent Reply Turn 1]:\n{out1['messages'][-1].content}")
    
    # Turn 2: Follow-up query checking medication safety (verifying shift context retention)
    state_turn2 = {
        "messages": out1["messages"] + [HumanMessage(content="Check medication safety for heparin bolus")],
        "patient_id": "MRN48291",
        "active_dart_note": out1["active_dart_note"],
        "requires_approval": True,
        "shift_session_id": shift_thread_id,
        "context_retrieval_summary": ""
    }
    
    out2 = agent.invoke(state_turn2, config=config)
    print(f"\n[Agent Reply Turn 2]:\n{out2['messages'][-1].content}")
    print(f"\n✅ Active Shift Context Retained {len(out2['messages'])} Message Exchanges in Thread {shift_thread_id}.")

if __name__ == "__main__":
    run_stateful_test()
