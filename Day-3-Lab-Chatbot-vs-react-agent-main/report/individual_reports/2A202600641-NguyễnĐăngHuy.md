# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Đăng Huy
- **Student ID**: 2A202600641
- **Date**: 01/06/26

---

> **⚠️ Grader Note — Context on Branch Structure**
>
> This report references two branches: `main` and `huys-version`.
>
> My partner and I did not coordinate our task split properly and ended up implementing overlapping parts of the agent independently. When we merged, the team decided to keep my partner's implementation as `main` because reverting and re-merging would have cost too much time at that stage.
>
> As a result, **`huys-version` is missing some tools that exist on `main`** (e.g. `budget_estimator`, `generate_seo_metadata`) — not because I did not implement them, but because those were added by my partner directly to `main` after the split.
>
> Despite the missing tools, **`huys-version` is architecturally more correct**: it enforces strict one-action-per-response, dispatches tools before checking for `Final Answer`, injects format-violation corrections, and fixes two bugs in `getScene` and `GetDuration` that exist on `main`. The live before/after tests in Section III demonstrate this directly — `main` never calls any tool, while `huys-version` calls the full chain correctly.
>
> My individual contribution is documented against the commits I authored on `main` (`266e1b8`, `daada54`) plus the additional fixes on `huys-version` (`ddfbad5`).

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

### Evaluation Metrics: `main` vs `huys-version` (per `EVALUATION.md`)

| Metric | `main` | `huys-version` | Winner |
|--------|--------|----------------|--------|
| **Token efficiency** | 1 LLM call, large fabricated completion | Multiple calls, short completions per step | `huys-version` — paying for correct answers |
| **Latency** | ~25s (single-tool), ~50s (multi-tool) | Higher wall-clock (sequential calls) | `main` on raw speed, but answers are wrong |
| **Loop count / termination** | Exits at step 0 — premature, not correct | Exits after real tool chain completes | `huys-version` — terminates correctly |
| **Failure mode** | Silent hallucination — looks like success in logs | Explicit FORMAT_VIOLATION — logged, recoverable | `huys-version` — failures are honest and traceable |

**Token efficiency**: `main` appears cheaper but spends tokens fabricating wrong answers. `huys-version` costs more per query but every token contributes to a grounded result.

**Latency**: `main` finishes in fewer seconds because it makes one LLM call and fabricates everything. This is not a useful speed advantage — the EVALUATION.md goal of "responses within 200ms–2s" only applies to *correct* responses.

**Loop count**: `main` always hits `AGENT_END steps: 0`, which looks like perfect termination in the logs. It is actually premature exit — `Final Answer` matched before any `Action` was dispatched. `huys-version` correctly terminates after 1, 2, or 4 steps depending on how many tools the task requires. That is the behavior `EVALUATION.md` is measuring.

**Failure analysis**: `main`'s failure mode is the hardest to catch — the logs show `AGENT_END` with a plausible-looking answer and no error anywhere. In a production system this would silently serve wrong data to users. `huys-version`'s failures surface as explicit `FORMAT_VIOLATION` or `Error:` observations in the log — detectable, debuggable, and fixable. As `INSTRUCTOR_GUIDE.md` states: *"The trace is the truth."* On `main`, the trace lies.

---

## IV. Future Improvements (5 Points)

- **Build a UI to visualize the reasoning chain**: The current agent outputs steps as terminal text, which is hard to follow for someone new to the ReAct concept. Building a proper web UI (e.g., with Streamlit) would render the full Thought → Action → Observation chain as an interactive step-by-step timeline — each cycle displayed as a colored card, with collapsible observations and a sidebar showing which tools have been called. This makes the agent's internal logic *visible and learnable*, not just functional. It is especially useful for teaching: a student can watch the agent "think out loud" in a browser rather than reading raw JSON logs.

  *Example — Streamlit app with `run_steps()` generator:*
  ```python
  # app.py
  import streamlit as st
  from src.agent.agent import ReActAgent, TOOLS
  from src.core.claude_provider import ClaudeProvider

  st.title("ReAct Agent – Live Reasoning Viewer")
  user_input = st.text_input("Ask the agent:")

  if st.button("Run") and user_input:
      agent = ReActAgent(llm=ClaudeProvider(), tools=TOOLS, max_steps=8)
      for step in agent.run_steps(user_input):   # run_steps() yields one dict per cycle
          with st.expander(f"Step {step['index']} — {step['tool'] or 'Final Answer'}", expanded=True):
              st.info(f"💭 **Thought:** {step['thought']}")
              if step['tool']:
                  st.warning(f"⚡ **Action:** `{step['tool']}({step['args']})`")
                  st.success(f"👁 **Observation:** {step['observation']}")
              else:
                  st.success(f"✅ **Final Answer:** {step['answer']}")
  ```
  *Run with:* `streamlit run app.py`

- **Step-back on tool error**: Currently, if a tool returns an error the agent just appends it to the prompt and hopes the model self-corrects. A smarter approach is an automatic retry policy — on `Error:` observation, re-inject a structured correction with a retry counter capped at 2.

  *Example:*
  ```python
  if observation.startswith("Error:") and retries < 2:
      current_prompt += (
          f"\n[SYSTEM] {tool_name} failed: {observation}. "
          f"Fix your arguments and call it again. Attempt {retries+1}/2."
      )
      retries += 1
      continue   # skip steps += 1, retry same tool
  retries = 0
  ```

- **Short-term conversation memory**: Each call to `agent.run()` starts fresh — there is no memory of previous turns. Adding a sliding-window history would let users ask follow-up questions like *"now write the shot list for that script"* without re-running all tools from scratch.

  *Example:*
  ```python
  MAX_HISTORY = 6   # keep last 3 turns (user + agent each)

  def run(self, user_input: str) -> str:
      self.history.append(f"User: {user_input}")
      context = "\n".join(self.history[-MAX_HISTORY:]) + "\n" + user_input
      answer = self._run_loop(context)
      self.history.append(f"Agent: {answer}")
      return answer
  ```

- **Schema validation before dispatch**: Before `_execute_tool()` calls the real function, validate the parsed arguments against a lightweight schema defined in the `TOOLS` constant. This catches malformed calls at the boundary before they hit a confusing Python exception.

  *Example:*
  ```python
  # In TOOLS definition:
  {"name": "getActivity", "required": ["city", "categories"], ...}

  # In _execute_tool():
  required = {t["name"]: t.get("required", []) for t in self.tools}
  parts = [a.strip() for a in args.split(",")]
  missing = required[tool_name][len(parts):]   # fields not covered by positional args
  if missing:
      return f"Error: {tool_name} missing required args: {missing}. Got: {args!r}"
  ```

- **Support local models (Ollama) for offline practice**: Replacing the cloud provider with a locally-running model (e.g., `llama3`, `mistral` via Ollama) removes API costs and rate limits entirely — making it practical to run hundreds of test iterations while learning. Smaller models also expose ReAct's failure modes more clearly (they hallucinate Observations more aggressively), which is valuable for understanding *why* the prompt engineering and format enforcement matters.

  *Example — drop-in `OllamaProvider`:*
  ```python
  import requests

  class OllamaProvider(LLMProvider):
      def __init__(self, model_name: str = "llama3"):
          super().__init__(model_name, api_key=None)

      def generate(self, prompt: str, system_prompt: str = None) -> dict:
          payload = {
              "model": self.model_name,
              "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
              "stream": False,
          }
          r = requests.post("http://localhost:11434/api/generate", json=payload)
          return {"content": r.json()["response"], "provider": "ollama"}
  ```
  *Usage:* `! ollama pull llama3` then set `DEFAULT_PROVIDER=ollama` in `.env`.
