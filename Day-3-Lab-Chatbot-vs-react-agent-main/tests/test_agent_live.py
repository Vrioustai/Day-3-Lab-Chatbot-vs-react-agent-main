import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent, TOOLS

def get_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model    = os.getenv("DEFAULT_MODEL")
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
        raise ValueError(f"Unknown provider: {provider}. Set DEFAULT_PROVIDER=openai|google|claude in .env")


def test_live_activity_query():
    """Agent should call getActivity and return real data."""
    agent = ReActAgent(llm=get_llm(), tools=TOOLS, max_steps=6)
    result = agent.run("Gợi ý cho tôi địa điểm ăn uống ở Hà Nội.")
    assert result, "Empty response"
    assert "I don't know" not in result, f"Agent gave up instead of using tools: {result}"
    print(f"PASS test_live_activity_query\nAnswer: {result}\n")


def test_live_out_of_scope():
    """Agent should say I don't know for questions outside tool scope."""
    agent = ReActAgent(llm=get_llm(), tools=TOOLS, max_steps=6)
    result = agent.run("Thời tiết hôm nay ở Đà Nẵng thế nào?")
    assert "don't know" in result.lower() or "không biết" in result.lower(), \
        f"Agent should have said I don't know, got: {result}"
    print(f"PASS test_live_out_of_scope\nAnswer: {result}\n")


def test_live_full_pipeline():
    """Agent should chain getActivity → getContent in one run."""
    agent = ReActAgent(llm=get_llm(), tools=TOOLS, max_steps=8)
    result = agent.run(
        "Tôi muốn làm video TikTok về địa điểm check-in ở Sài Gòn. "
        "Hãy chọn một địa điểm và viết kịch bản cho tôi."
    )
    assert result, "Empty response"
    print(f"PASS test_live_full_pipeline\nAnswer: {result}\n")


if __name__ == "__main__":
    print("Running live tests (requires API key in .env)...\n")
    test_live_activity_query()
    test_live_out_of_scope()
    test_live_full_pipeline()
    print("All live tests passed.")
