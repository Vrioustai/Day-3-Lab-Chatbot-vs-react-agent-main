import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.llm_provider import LLMProvider
from src.agent.agent import ReActAgent, TOOLS

# --- Mock LLM that returns scripted responses in order ---
class MockLLM(LLMProvider):
    def __init__(self, responses):
        super().__init__(model_name="mock")
        self._responses = iter(responses)

    def generate(self, prompt, system_prompt=None):
        return {"content": next(self._responses), "usage": {}, "latency_ms": 0}

    def stream(self, prompt, system_prompt=None):
        yield next(self._responses)

# --- Test 1: Agent returns Final Answer directly ---
def test_final_answer_on_first_step():
    llm = MockLLM(["Thought: I know the answer.\nFinal Answer: Paris is the capital of France."])
    agent = ReActAgent(llm=llm, tools=TOOLS)
    result = agent.run("What is the capital of France?")
    assert result == "Paris is the capital of France.", f"Got: {result}"
    print("PASS test_final_answer_on_first_step")

# --- Test 2: Agent calls a tool then returns Final Answer ---
def test_tool_call_then_final_answer():
    llm = MockLLM([
        "Thought: I need to look up activities.\nAction: getActivity(Ha Noi, am_thuc)",
        "Thought: I have the data.\nFinal Answer: Here are food spots in Ha Noi.",
    ])
    agent = ReActAgent(llm=llm, tools=TOOLS)
    result = agent.run("What food spots are in Ha Noi?")
    assert result == "Here are food spots in Ha Noi.", f"Got: {result}"
    print("PASS test_tool_call_then_final_answer")

# --- Test 3: Agent hits max_steps without Final Answer ---
def test_max_steps_guard():
    llm = MockLLM(["Thought: Still thinking..."] * 10)
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=3)
    result = agent.run("Loop forever")
    assert "Max steps" in result, f"Got: {result}"
    print("PASS test_max_steps_guard")


ALL_TOOLS_AGENT = ReActAgent(llm=MockLLM([]), tools=TOOLS)

# --- Test 4: _execute_tool — getActivity with valid city and category ---
def test_execute_tool_getActivity_valid():
    import json
    result = ALL_TOOLS_AGENT._execute_tool("getActivity", "Ha Noi, am_thuc")
    data = json.loads(result)
    assert data["status"] == "success", f"Got: {result}"
    assert data["city"] == "Ha Noi"
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    print("PASS test_execute_tool_getActivity_valid")

# --- Test 5: _execute_tool — getActivity with unknown city returns error ---
def test_execute_tool_getActivity_unknown_city():
    import json
    result = ALL_TOOLS_AGENT._execute_tool("getActivity", "Da Nang, am_thuc")
    data = json.loads(result)
    assert "error" in data, f"Got: {result}"
    print("PASS test_execute_tool_getActivity_unknown_city")

# --- Test 6: _execute_tool — getActivity with invalid category returns error ---
def test_execute_tool_getActivity_invalid_category():
    import json
    result = ALL_TOOLS_AGENT._execute_tool("getActivity", "Sai Gon, shopping")
    data = json.loads(result)
    assert "error" in data, f"Got: {result}"
    print("PASS test_execute_tool_getActivity_invalid_category")

# --- Test 7: _execute_tool — unknown tool name ---
def test_execute_tool_unknown():
    result = ALL_TOOLS_AGENT._execute_tool("nonExistentTool", "")
    assert "not found" in result, f"Got: {result}"
    print("PASS test_execute_tool_unknown")

# --- Test 8: Full loop — getActivity result flows into prompt as Observation ---
def test_observation_appended_to_prompt():
    import json
    captured_prompts = []

    class CapturingLLM(MockLLM):
        def generate(self, prompt, system_prompt=None):
            captured_prompts.append(prompt)
            return super().generate(prompt, system_prompt)

    llm = CapturingLLM([
        "Thought: I need activities.\nAction: getActivity(Sai Gon, check_in)",
        "Thought: Got data.\nFinal Answer: Done.",
    ])
    agent = ReActAgent(llm=llm, tools=TOOLS)
    agent.run("Suggest check-in spots in Sai Gon")

    # Second LLM call must include the Observation from getActivity
    second_prompt = captured_prompts[1]
    assert "Observation:" in second_prompt, "Observation not appended to prompt"
    obs_data = json.loads(second_prompt.split("Observation:")[-1].strip())
    assert obs_data["status"] == "success"
    print("PASS test_observation_appended_to_prompt")


if __name__ == "__main__":
    test_final_answer_on_first_step()
    test_tool_call_then_final_answer()
    test_max_steps_guard()
    test_execute_tool_getActivity_valid()
    test_execute_tool_getActivity_unknown_city()
    test_execute_tool_getActivity_invalid_category()
    test_execute_tool_unknown()
    test_observation_appended_to_prompt()
    print("\nAll tests passed.")
