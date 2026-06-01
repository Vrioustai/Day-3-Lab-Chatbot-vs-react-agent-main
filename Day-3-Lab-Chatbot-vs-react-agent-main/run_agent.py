import os
import sys
import argparse
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Generator

# Add current dir to path to import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.core.local_provider import LocalProvider
from src.agent.agent import ReActAgent, DEFAULT_TOOLS
from src.telemetry.logger import logger

class MockProvider(LLMProvider):
    """
    Mock LLM Provider that simulates the Thought-Action-Observation loop
    for content creation tasks to test the agent pipeline.
    """
    def __init__(self, model_name: str = "mock-llm"):
        super().__init__(model_name)
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        # Determine the state based on the history in the prompt
        if "Observation:" not in prompt:
            # Step 1: Initial call. Generate getActivity action
            content = (
                "Thought: Để gợi ý địa điểm ẩm thực tại Hà Nội, tôi cần gọi tool getActivity với city=\"ha_noi\" và categories=\"am_thuc\".\n"
                "Action: getActivity(city=\"ha_noi\", categories=\"am_thuc\")"
            )
        elif "getActivity" in prompt and "getContent" not in prompt:
            # Step 2: Have activity data, generate getContent action
            content = (
                "Thought: Tôi đã có danh sách địa điểm ẩm thực tại Hà Nội. Địa điểm thú vị nhất là 'Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng)'. "
                "Bây giờ tôi sẽ gọi tool getContent để tự động viết kịch bản TikTok cho creator Minh có tone hài hước và các câu cửa miệng đặc trưng.\n"
                "Action: getContent(\n"
                "  activity_item={'name': 'Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng)', 'fact': 'Quán phở mở vào khung giờ linh hồn, khách phải xếp hàng rồng rắn giữa đêm lạnh chỉ để ăn một bát phở bò sốt vang.', 'insight_gap': 'Đối thủ thường làm review trải nghiệm khen ngon. Khoảng trống: Làm video thử thách \\'Thức xuyên đêm ăn phở gánh và cái kết buồn ngủ sấp mặt\\' hoặc châm biếm \\'Có đáng để hành xác vì một bát phở?\\''},\n"
                "  creator_persona={'name': 'Minh', 'tone_of_voice': 'Hài hước', 'catchphrases': ['Thực tế là...', 'Hết cứu!', 'Ủa alo?']}\n"
                ")"
            )
        elif "getContent" in prompt and "GetDuration" not in prompt:
            # Step 3: Have script, generate GetDuration action
            content = (
                "Thought: Kịch bản TikTok đã được tạo thành công. Bây giờ tôi cần phân tích thời lượng và tốc độ nói cho kịch bản này bằng cách gọi tool GetDuration.\n"
                "Action: GetDuration(content_output={\n"
                "  'status': 'success',\n"
                "  'metadata': {'creator': 'Minh', 'tone_applied': 'Hài hước', 'format': 'POV Clip ngắn', 'audio': 'Nhạc nền xu hướng TikTok'},\n"
                "  'title_suggestions': ['Đừng đi Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng) nếu chưa biết sự thật này!', 'Cú lừa mang tên Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng)?...'],\n"
                "  'script_scenes': [\n"
                "    {'time': '00:00 - 00:05', 'visual': 'Cảnh mở màn...', 'audio_voiceover': 'Trên mạng review Phở Gánh Hàng Chiếu... Nhưng Thực tế là..., có những sự thật...'},\n"
                "    {'time': '00:05 - 00:25', 'visual': 'Cắt cảnh thực tế...', 'audio_voiceover': 'Đấy nhìn xem! Khách xếp hàng rồng rắn... Hết cứu!!'},\n"
                "    {'time': '00:25 - 00:45', 'visual': 'Quay Minh ngồi trải nghiệm...', 'audio_voiceover': 'Thay vì làm clip khen ngon... mình mách bạn...'},\n"
                "    {'time': '00:45 - 00:60', 'visual': 'Minh cười trừ...', 'audio_voiceover': 'Tóm lại là Ủa alo?, anh em có dám thử... Nhớ follow Minh nhé!'}\n"
                "  ]\n"
                "})"
            )       
        elif "GetDuration" in prompt and "getScene" not in prompt:
            # Step 4: Have duration analysis, generate getScene action
            content = (
                "Thought: Tôi đã có thông số phân tích thời lượng kịch bản. Tiếp theo, tôi cần vẽ phân cảnh quay chi tiết (Shot List) bằng cách gọi tool getScene.\n"
                "Action: getScene(content_output={\n"
                "  'status': 'success',\n"
                "  'metadata': {'creator': 'Minh', 'tone_applied': 'Hài hước', 'format': 'POV Clip ngắn', 'audio': 'Nhạc nền xu hướng TikTok'},\n"
                "  'title_suggestions': ['Đừng đi Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng) nếu chưa biết sự thật này!', 'Cú lừa mang tên Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng)?...'],\n"
                "  'script_scenes': [\n"
                "    {'time': '00:00 - 00:05', 'visual': 'Cảnh mở màn...', 'audio_voiceover': 'Trên mạng review Phở Gánh Hàng Chiếu... Nhưng Thực tế là..., có những sự thật...'},\n"
                "    {'time': '00:05 - 00:25', 'visual': 'Cắt cảnh thực tế...', 'audio_voiceover': 'Đấy nhìn xem! Khách xếp hàng rồng rắn... Hết cứu!!'},\n"
                "    {'time': '00:25 - 00:45', 'visual': 'Quay Minh ngồi trải nghiệm...', 'audio_voiceover': 'Thay vì làm clip khen ngon... mình mách bạn...'},\n"
                "    {'time': '00:45 - 00:60', 'visual': 'Minh cười trừ...', 'audio_voiceover': 'Tóm lại là Ủa alo?, anh em có dám thử... Nhớ follow Minh nhé!'}\n"
                "  ]\n"
                "})"
            )
        else:
            # Step 5: Finished all tool runs. Present final answer
            content = (
                "Thought: Tôi đã thu thập đầy đủ thông tin địa điểm Hà Nội, kịch bản, thời lượng và phân cảnh. Tôi sẽ tổng hợp câu trả lời cuối cùng.\n"
                "Final Answer: Tôi đã hoàn thành việc gợi ý địa điểm và xây dựng kịch bản video ngắn cho creator Minh:\n"
                "- Địa điểm: Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng) - một trải nghiệm ẩm thực độc đáo tại Hà Nội.\n"
                "- Kịch bản TikTok: Đã được viết theo phong cách hài hước với các câu cửa miệng 'Thực tế là...', 'Hết cứu!', 'Ủa alo?'.\n"
                "- Thời lượng: Phân tích cho thấy tổng thời lượng là 60 giây, tốc độ nói trung bình ở mức vừa phải (khoảng 120 từ/phút), phù hợp với TikTok Shorts.\n"
                "- Phân cảnh quay (Shot List): Bản phân cảnh gồm 4 shot chi tiết, gợi ý các góc quay như POV, Medium Shot và Close-up, kèm hướng dẫn đạo cụ (Tripod, mic không dây).\n\n"
                "Kịch bản và phân cảnh đã sẵn sàng để quay bấm máy!"
            )
            
        return {
            "content": content,
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(prompt.split()) + len(content.split())
            },
            "latency_ms": 100,
            "provider": "mock"
        }
        
    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        res = self.generate(prompt, system_prompt)
        yield res["content"]

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Run the ReAct Agent or Chatbot Baseline.")
    parser.add_argument(
        "--provider", 
        choices=["mock", "openai", "google", "local"], 
        default="mock",
        help="LLM provider to use (default: mock)"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default=None,
        help="Model name (uses default for provider if not specified)"
    )
    parser.add_argument(
        "--query", 
        type=str, 
        default="Hãy gợi ý địa điểm ẩm thực tại Hà Nội, tự động viết kịch bản TikTok cho creator Minh có tone hài hước, phân tích thời lượng và vẽ phân cảnh chi tiết.",
        help="User query for the agent"
    )
    parser.add_argument(
        "--mode",
        choices=["agent", "chatbot"],
        default="agent",
        help="Run as a ReAct Agent or a standard Chatbot"
    )
    
    args = parser.parse_args()
    
    # Initialize Provider
    provider_name = args.provider
    model_name = args.model
    
    print(f"=== Starting System ===")
    print(f"Mode: {args.mode.upper()}")
    print(f"Provider: {provider_name.upper()}")
    
    if provider_name == "mock":
        provider = MockProvider()
        model_name = model_name or "mock-gpt-4o"
    elif provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            print("❌ Error: OPENAI_API_KEY not found in environment. Please set it in .env file.")
            sys.exit(1)
        model_name = model_name or os.getenv("DEFAULT_MODEL", "gpt-4o")
        provider = OpenAIProvider(model_name=model_name, api_key=api_key)
    elif provider_name == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            print("❌ Error: GEMINI_API_KEY not found in environment. Please set it in .env file.")
            sys.exit(1)
            model_name = model_name or "gemini-2.5-flash"
        provider = GeminiProvider(model_name=model_name, api_key=api_key)
    elif provider_name == "local":
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        if not os.path.exists(model_path):
            print(f"❌ Error: Local model not found at {model_path}.")
            sys.exit(1)
        provider = LocalProvider(model_path=model_path)
    
    print(f"Model: {provider.model_name}")
    print(f"Query: {args.query}\n")
    
    if args.mode == "agent":
        # Create and run ReAct Agent
        agent = ReActAgent(llm=provider, tools=DEFAULT_TOOLS, max_steps=6)
        final_answer = agent.run(args.query)
        print("\n=== Agent Final Answer ===")
        print(final_answer)
    else:
        # Standard Chatbot logic (one-shot prompt)
        print("Running chatbot baseline (one-shot completion without tools)...")
        # System prompt instructs the model to solve the problem
        system_prompt = "You are a helpful assistant. You must answer the user query as best as you can."
        response = provider.generate(args.query, system_prompt=system_prompt)
        print("\n=== Chatbot Response ===")
        print(response.get("content", ""))
        
        # Log to telemetry
        logger.log_event("CHATBOT_START", {"input": args.query, "model": provider.model_name})
        from src.telemetry.metrics import tracker
        tracker.track_request(
            provider=provider_name,
            model=provider.model_name,
            usage=response.get("usage", {}),
            latency_ms=response.get("latency_ms", 0)
        )
        logger.log_event("CHATBOT_END", {"response": response.get("content", "")})

if __name__ == "__main__":
    main()
