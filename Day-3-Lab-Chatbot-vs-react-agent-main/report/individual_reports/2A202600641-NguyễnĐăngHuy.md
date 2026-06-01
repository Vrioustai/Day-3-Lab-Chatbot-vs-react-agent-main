# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Đăng Huy
- **Student ID**: 2A202600641
- **Date**: 01/06/26

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**: `ReActAgent.run()`, `ReActAgent._execute_tool()`, `TOOLS` constant, `ClaudeProvider`, `main.py` CLI, verbose step display, unit tests (`test_agent_run.py`), live integration tests (`test_agent_live.py`)

- **Code Highlights**:

`run()` — the core ReAct loop (commit `266e1b8`):

```python
def run(self, user_input: str) -> str:
    logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

    current_prompt = user_input
    steps = 0

    while steps < self.max_steps:
        result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
        response_text = result["content"]

        logger.log_event("AGENT_STEP", {"step": steps, "response": response_text})

        final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL)
        if final_match:
            logger.log_event("AGENT_END", {"steps": steps})
            return final_match.group(1).strip()

        action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", response_text, re.DOTALL)
        if action_match:
            tool_name = action_match.group(1).strip()
            tool_args = action_match.group(2).strip()
            observation = self._execute_tool(tool_name, tool_args)
            current_prompt += f"\n{response_text}\nObservation: {observation}"
        else:
            current_prompt += f"\n{response_text}"

        steps += 1

    logger.log_event("AGENT_END", {"steps": steps})
    return "Max steps reached without a Final Answer."
```

`_execute_tool()` — dispatches parsed actions to tool handlers (commit `266e1b8`):

```python
def _execute_tool(self, tool_name: str, args: str) -> str:
    import json

    known_tools = {t['name'] for t in self.tools}
    if tool_name not in known_tools:
        return f"Tool '{tool_name}' not found."

    try:
        if tool_name == "getActivity":
            parts = [a.strip().strip("\"'") for a in args.split(",", 1)]
            result = ReActAgent.getActivity(*parts)

        elif tool_name == "getContent":
            parsed = json.loads(f"[{args}]")
            result = ReActAgent.getContent(*parsed)

        elif tool_name == "GetDuration":
            parsed = json.loads(args)
            result = ReActAgent.GetDuration(parsed)

        elif tool_name == "getScene":
            parsed = json.loads(args)
            result = ReActAgent.getScene(parsed)

        else:
            return f"Tool '{tool_name}' is registered but has no handler."

    except Exception as e:
        return f"Error executing '{tool_name}': {e}"

    return json.dumps(result, ensure_ascii=False)
```

`ClaudeProvider` — Anthropic SDK provider added alongside OpenAI/Gemini (commit `266e1b8`):

```python
class ClaudeProvider(LLMProvider):
    def __init__(self, model_name: str = "claude-sonnet-4-6", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        kwargs = dict(
            model=self.model_name,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        latency_ms = int((time.time() - start_time) * 1000)
        content = response.content[0].text
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
        return {"content": content, "usage": usage, "latency_ms": latency_ms, "provider": "anthropic"}
```

- **Documentation**: `run()` drives the Thought → Action → Observation cycle. Each iteration calls `self.llm.generate()` with the growing prompt, parses `Action: tool_name(args)` via regex, routes it to `_execute_tool()`, and appends the JSON observation before the next step. `Final Answer:` terminates the loop. The `TOOLS` constant feeds the system prompt's tool section, so the LLM always has up-to-date parameter specs and usage examples.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Agent entered an infinite "Thought-only" loop — at every step the LLM responded with only a `Thought:` line and no `Action:`, consuming all `max_steps` without producing a result.

- **Log Source** (`logs/2026-06-01.log`, lines 8–12):
```json
{"event": "AGENT_START", "data": {"input": "Loop forever", "model": "mock"}}
{"event": "AGENT_STEP",  "data": {"step": 0, "response": "Thought: Still thinking..."}}
{"event": "AGENT_STEP",  "data": {"step": 1, "response": "Thought: Still thinking..."}}
{"event": "AGENT_STEP",  "data": {"step": 2, "response": "Thought: Still thinking..."}}
{"event": "AGENT_END",   "data": {"steps": 3}}
```

- **Diagnosis**: The system prompt's `FORMAT` section only showed the happy-path template (`Thought → Action → Observation → Final Answer`). When the LLM could not match the input to any available tool it stalled — it knew it should not answer from memory, but it also received no instruction for what to do in a format-violation state. The `else` branch in `run()` silently appended the broken response to the prompt, giving the model nothing to correct against, so the pattern repeated until `max_steps`.

- **Solution**: Tightened the system prompt to an explicit "STRICT RULES" block (rule 5: *"If the question cannot be answered by any tool: Final Answer: I don't know."*). Added a `FORMAT_VIOLATION` correction message that is injected into the prompt whenever neither `Action:` nor `Final Answer:` is detected, telling the model exactly what tools have been called so far and what it must produce next.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: The `Thought` block forced the agent to commit to a plan in natural language before acting. In a plain chatbot, the model jumps directly from question to answer — if it is wrong, there is no visible reasoning to audit. With the `Thought` step visible in the prompt history, each subsequent step builds on an explicit record of what was decided and why, making errors traceable to a specific reasoning mistake rather than an opaque output.

2. **Reliability**: The agent performed *worse* than a direct chatbot for out-of-scope questions. A chatbot answers "What is the capital of France?" instantly from training knowledge. The ReAct agent, constrained to only use registered tools, either stalled (as seen in the log) or had to return "I don't know" — correct behavior by design, but a frustrating regression for users asking general questions outside the travel-content domain.

3. **Observation**: Observations acted as hard constraints that pruned the LLM's next response. Without an observation the model could speculate; after receiving a JSON observation from `getActivity`, the next `Thought` was grounded in the actual returned place names and facts. This reduced hallucination significantly in multi-step flows (e.g., `getActivity → getContent → GetDuration`) because each tool result narrowed what the model could plausibly say next.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Replace the sequential `while` loop with an async task queue (e.g., `asyncio` + `anyio`). Each tool call becomes a coroutine, allowing multiple independent tool calls within a single reasoning step to run in parallel and reducing total latency for multi-tool queries.

- **Safety**: Add a lightweight "Supervisor" LLM pass that inspects each `Action` before execution — checking that the tool name is valid, arguments are well-formed, and the call is consistent with the user's original intent. This catches prompt-injection attempts (e.g., a crafted `insight_gap` field that smuggles a new `Action:` into the observation) before they reach `_execute_tool`.

- **Performance**: With more than ~10 tools, grepping the full `TOOLS` list into every system prompt is wasteful and degrades instruction-following. Replace it with a vector DB (e.g., ChromaDB) that retrieves the top-k most relevant tool descriptions at query time, keeping the system prompt short and focused regardless of how many tools are registered.
