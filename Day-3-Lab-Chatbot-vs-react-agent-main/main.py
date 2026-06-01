import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from src.agent.agent import ReActAgent, TOOLS

# Send logs to file only — keep the console clean for cycle display
logging.getLogger("AI-Lab-Agent").handlers = [
    h for h in logging.getLogger("AI-Lab-Agent").handlers
    if not isinstance(h, logging.StreamHandler) or isinstance(h, logging.FileHandler)
]


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

    print(f"ReAct Agent ready ({llm.model_name}). Type 'exit' to quit.")
    print("""
Hints — try asking:
  - Gợi ý địa điểm ăn uống ở Hà Nội
  - Gợi ý địa điểm check-in ở Sài Gòn
  - Gợi ý hidden gem ở Hà Nội
  - Viết kịch bản TikTok về [địa điểm] cho creator [phong cách]
  - Phân tích thời lượng kịch bản vừa tạo
  - Tạo shot list cho kịch bản trên
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

        answer = agent.run(user_input, verbose=True)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
