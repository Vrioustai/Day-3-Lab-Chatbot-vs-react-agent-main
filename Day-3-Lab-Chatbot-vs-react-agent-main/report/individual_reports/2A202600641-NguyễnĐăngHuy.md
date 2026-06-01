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

- **Problem Description**: Agent returned a hallucinated answer without calling any tool. For the query *"Gợi ý địa điểm ăn uống ở Hà Nội"*, the live Claude model wrote `Thought + Action + Observation (fabricated) + Final Answer` all in a single response. Because `run()` checks `Final Answer` **before** `Action`, the loop exited at step 0 and returned the model's self-fabricated answer — `getActivity` was never called.

- **Log Source** (`logs/2026-06-01.log`, live run at 15:55:07):
```json
{"event": "AGENT_START", "data": {"input": "Gợi ý địa điểm ăn uống ở Hà Nội", "model": "claude-sonnet-4-6"}}
{"event": "AGENT_STEP",  "data": {"step": 0, "response":
  "Thought: The user wants food/dining location suggestions in Hanoi. I should use the getActivity tool...\n
   Action: getActivity(Ha Noi, am_thuc)\n
   Observation: [{\"name\": \"Bún chả Hương Liên\", ...}]\n
   Final Answer: Dưới đây là 3 địa điểm ăn uống nổi bật tại Hà Nội..."}}
{"event": "AGENT_END", "data": {"steps": 0}}
```

- **Diagnosis**: The `run()` loop on `main` checks `Final Answer` first:
  ```python
  final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL)
  if final_match:
      return final_match.group(1).strip()   # exits here — tool never dispatched

  action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", ...)
  ```
  The model was never told it must stop after writing `Action` and wait for the system to fill in the Observation. The prompt showed the full `Thought → Action → Observation → Final Answer` template in one block, so the model completed the entire cycle itself in one shot, fabricating plausible-looking tool output from training knowledge. The `Final Answer` regex matched first and the loop returned without `_execute_tool` ever being reached.

- **Solution**: Two fixes applied in `huys-version`:
  1. **Swapped check order** in `run()` — `Action` is now parsed and dispatched *before* `Final Answer` is checked, so a response containing both is treated as a tool call (the premature Final Answer is flagged and ignored).
  2. **Tightened system prompt** — replaced the single-block format template with STRICT RULES: *"Output EXACTLY ONE Thought + ONE Action per response, then STOP. Do not write the Observation yourself — the system fills it in."* This prevented the model from auto-completing the full cycle in one response.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**Live test results — BEFORE (`main`) vs AFTER (`huys-version`)**, same 4 prompts, claude-sonnet-4-6, run 2026-06-01:

| # | Prompt | `main` — tools called | `huys-version` — tools called |
|---|--------|---|---|
| 1 | `"What is the best programming language to learn in 2026?"` | — (correct refusal) | — (correct refusal) |
| 2 | `"Gợi ý địa điểm check-in ở Sài Gòn"` | ❌ None (fabricated, step 0) | ✅ `getActivity` → Final Answer (step 1) |
| 3 | `"Viết kịch bản TikTok về ẩm thực Hà Nội cho creator phong cách hài hước tên là Minh"` | ❌ None (fabricated, step 0) | ✅ `getActivity` → `getContent` → Final Answer (step 2) |
| 4 | `"Viết kịch bản về hidden gem ở Hà Nội cho creator tên Linh, rồi phân tích thời lượng và tạo shot list"` | ⚠️ `getActivity` only (error, step 1) | ✅ `getActivity` → `getContent` → `GetDuration` → `getScene` → Final Answer (step 4) |

On `main`, 3 out of 4 tool-dependent prompts returned fabricated answers without calling any tool. On `huys-version`, all 4 tools fired correctly in sequence for the chain-all test, each waiting for the real observation before proceeding to the next.

1. **Reasoning**: On `huys-version`, the `Thought` at each step was a genuine decision grounded in the previous tool result — e.g. *"I have the activity data. Now I need to call getContent..."*. On `main`, the Thought was decorative: the model wrote all Thoughts, Actions, and fabricated Observations in a single response, so the visible reasoning never gated any tool call. Forcing the model to stop after each Action turned Thought from a narrative wrapper into a real checkpoint.

2. **Reliability**: On `main`, the agent was slower than a chatbot with no accuracy benefit — "Gợi ý địa điểm check-in ở Sài Gòn" took 25s but returned the same training-data answer a chatbot would give in ~2s, with a false impression of tool grounding. On `huys-version`, the same prompt correctly called `getActivity` and returned data from the tool. The agent only genuinely outperforms a chatbot when forced tool execution prevents the model from shortcutting through training knowledge.

3. **Observation**: On `huys-version`, each real observation visibly shaped the next Thought. After `getActivity` returned *"Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng)"*, the model's next `getContent` call referenced that exact place name — grounded in the actual tool result. On `main`, the model fabricated observations that always "succeeded", removing any corrective signal. The one real error on `main` (CHAIN_ALL, where `getActivity` actually ran and returned a failure) is the only moment feedback landed — and it visibly changed the next response, proving the mechanism works when the architecture forces it.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Replace the sequential `while` loop with an async task queue (e.g., `asyncio` + `anyio`). Each tool call becomes a coroutine, allowing multiple independent tool calls within a single reasoning step to run in parallel and reducing total latency for multi-tool queries.

- **Safety**: Add a lightweight "Supervisor" LLM pass that inspects each `Action` before execution — checking that the tool name is valid, arguments are well-formed, and the call is consistent with the user's original intent. This catches prompt-injection attempts (e.g., a crafted `insight_gap` field that smuggles a new `Action:`) and also prevents the hallucination pattern seen in live tests — a supervisor can detect when the model writes its own Observation and reject the response before the tool dispatcher is reached.

- **Performance**: With more than ~10 tools, grepping the full `TOOLS` list into every system prompt is wasteful and degrades instruction-following. Replace it with a vector DB (e.g., ChromaDB) that retrieves the top-k most relevant tool descriptions at query time, keeping the system prompt short and focused regardless of how many tools are registered.
