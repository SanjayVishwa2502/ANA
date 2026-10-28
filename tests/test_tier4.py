"""
Unit Tests for Tier 4: Agentic Orchestration & MCP FHIR Tools
"""

import unittest
import json
from tier4_agentic.mcp_fhir_pipeline import lookup_patient_history, check_medication_interaction
from tier4_agentic.agent_state_pipeline import build_agent_graph, NurseAgentState
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

class TestTier4Agentic(unittest.TestCase):
    def test_mcp_lookup_patient_history(self):
        resp_json = lookup_patient_history.invoke({"patient_id": "MRN48291"})
        data = json.loads(resp_json)
        self.assertEqual(data.get("id"), "MRN48291")
        self.assertIn("Jonathan Harker", str(data))

    def test_mcp_check_medication_interaction(self):
        resp = check_medication_interaction.invoke({"medication": "Heparin"})
        self.assertIn("Verified", resp)

    def test_agent_memory_persistence(self):
        memory = MemorySaver()
        agent = build_agent_graph(checkpointer=memory)
        config = {"configurable": {"thread_id": "test_thread_001"}}

        state: NurseAgentState = {
            "messages": [HumanMessage(content="What are the patient's vitals?")],
            "patient_id": "MRN48291",
            "active_dart_note": {},
            "requires_approval": False,
            "shift_session_id": "test_thread_001",
            "context_retrieval_summary": ""
        }
        out1 = agent.invoke(state, config=config)
        self.assertTrue(len(out1["messages"]) >= 2)

if __name__ == "__main__":
    unittest.main()
