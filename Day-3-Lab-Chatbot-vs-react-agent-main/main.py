import os
import sys
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent.agent import ReActAgent, TOOLS

# ── Persistent state file (survives between runs) ─────────────────────────────
# Stored in the system temp dir so it works on any OS without extra setup.
STATE_FILE = Path(tempfile.gettempdir()) / "react_agent_state.json"


def load_state() -> dict:
    """Load persisted agent state from disk."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(state: dict) -> None:
    """Save agent state to disk."""
    try:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[Warning] Could not save state: {e}")


def get_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL")
    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider
        return OpenAIProvider(model_name=model or "gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    elif provider == "google":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(model_name=model or "gemini-1.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
    elif provider == "claude":
        from src.core.claude_provider import ClaudeProvider
        return ClaudeProvider(model_name=model or "claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY"))
    else:
        print(f"Unknown provider '{provider}'. Set DEFAULT_PROVIDER=openai|google|claude in .env")
        sys.exit(1)


def main():
    llm = get_llm()
    agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=6)

    # ── Restore state from previous session ───────────────────────────────────
    state = load_state()
    if state.get("last_content_output"):
        agent.last_content_output = state["last_content_output"]
        print(f"[State restored] last_content_output from previous session is available.")
        print(f"  → Creator : {agent.last_content_output.get('metadata', {}).get('creator', '?')}")
        print(f"  → Title   : {agent.last_content_output.get('title_suggestions', ['?'])[0][:60]}...")
    if state.get("history"):
        agent.history = state["history"]
        print(f"[State restored] {len(agent.history)} history lines loaded.\n")

    print(f"ReAct Agent ready ({llm.model_name}). Type 'exit' to quit, 'reset' to clear state.")
    print("""
Hints — try asking:
  - Gợi ý địa điểm ăn uống ở Hà Nội
  - Gợi ý địa điểm check-in ở Sài Gòn
  - Gợi ý hidden gem ở Hà Nội
  - Viết kịch bản TikTok về [địa điểm] cho creator [phong cách]
  - Phân tích thời lượng kịch bản vừa tạo
  - Tạo shot list cho kịch bản trên
  - Sinh metadata SEO cho kịch bản video vừa tạo
""")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Bye!")
            break

        # Allow user to wipe state manually
        if user_input.lower() == "reset":
            agent.last_content_output = None
            agent.history = []
            STATE_FILE.unlink(missing_ok=True)
            print("[State cleared]\n")
            continue

        answer = agent.run(user_input, verbose=True)
        print(f"\nAgent: {answer}\n")

        # ── Persist state after every turn ────────────────────────────────────
        save_state({
            "last_content_output": agent.last_content_output,
            "history": agent.history,
        })


if __name__ == "__main__":
    main()