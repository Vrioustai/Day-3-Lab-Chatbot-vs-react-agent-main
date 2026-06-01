import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

# 🗄️ DATABASE
ACTIVITIES_DB = {
    "ha_noi": {
        "am_thuc": [
            {
                "name": "Phở Gánh Hàng Chiếu (Ăn lúc 3h sáng)",
                "fact": "Quán phở mở vào khung giờ linh hồn, khách phải xếp hàng rồng rắn giữa đêm lạnh chỉ để ăn một bát phở bò sốt vang.",
                "insight_gap": "Đối thủ thường làm review trải nghiệm khen ngon. Khoảng trống: Làm video thử thách 'Thức xuyên đêm ăn phở gánh và cái kết buồn ngủ sấp mặt' hoặc châm biếm 'Có đáng để hành xác vì một bát phở?'"
            },
            {
                "name": "Cà phê Đường Tàu (Phố Phùng Hưng/Điện Biên Phủ)",
                "fact": "Mặc dù bị cấm và rào chắn vì an toàn, các quán cafe ở đây vẫn hoạt động 'chui' bằng cách có người dắt tay khách qua chốt.",
                "insight_gap": "Chưa ai làm clip POV đóng vai 'Điệp viên vượt biên' đi uống cafe tàu hỏa dưới góc nhìn hài hước. Né kiểu quay cinematic đẹp đẽ thông thường."
            }
        ],
        "check_in": [
            {
                "name": "Toà soạn Báo Hà Nội Mới",
                "fact": "Góc tường vàng kinh điển mà ai đến Hà Nội cũng chụp, nhưng luôn trong tình trạng xếp hàng và dính người khác vào khung hình.",
                "insight_gap": "Làm kịch bản hướng dẫn 'Văn hoá xếp hàng chụp ảnh bờ Hồ' hoặc mẹo chỉnh ảnh xoá người bằng AI cực lầy lội."
            },
            {
                "name": "Chợ hoa đêm Quảng An (2h sáng)",
                "fact": "Nơi bán buôn hoa lớn nhất Hà Nội lúc rạng đông, ánh sáng đèn led mờ ảo lên hình rất nghệ thuật nhưng mùi tanh của nước và đá rã rất khó chịu.",
                "insight_gap": "Làm nội dung kiểu tương phản (Kỳ vọng vs Thực tế): Trên mạng là nàng thơ ôm hoa thơ mộng, thực tế là lạnh thấu xương và suýt bị xe chở hoa tông."
            }
        ],
        "hidden_gem": [
            {
                "name": "Hẻm ngõ siêu nhỏ Phố Cổ (Ngõ 10 Hàng Trống)",
                "fact": "Những con ngõ chỉ vừa đúng một người đi nghiêng, tối tăm và sâu hun hút, dẫn vào không gian sống của 3-4 thế hệ người Hà Nội cổ.",
                "insight_gap": "Hợp với Creator thích style học thuật/trải nghiệm: Khám phá 'Bất động sản nghìn đô nhưng đi phải nín thở' tại Hà Nội."
            }
        ]
    },
    "sai_gon": {
        "am_thuc": [
            {
                "name": "Cơm tấm bãi rác (Quận 4)",
                "fact": "Tên gọi do nằm gần bến trung chuyển rác cũ, giá một đĩa cơm sườn lên tới 100k - 150k (đắt hơn nhà hàng sang trọng) nhưng vẫn đông nghẹt.",
                "insight_gap": "Góc tiếp cận: Đánh giá xem 'Cơm tấm nhà giàu núp bóng bãi rác' có thực sự xứng đáng với giá tiền hay chỉ là chiêu trò marketing."
            },
            {
                "name": "Cà phê bệt Nhà Thờ Đức Bà",
                "fact": "Không bàn, không ghế, chỉ có tờ báo giấy trải xuống đất và ly cafe sữa đá 20k nhưng là linh hồn của giới trẻ Sài Gòn.",
                "insight_gap": "Làm video so sánh văn hoá: 'Trà chanh vỉa hè Hà Nội' vs 'Cà phê bệt Sài Gòn' dưới góc nhìn hài hước, phân tích hành vi ngồi bệt."
            }
        ],
        "check_in": [
            {
                "name": "Chung cư 42 Nguyễn Huệ",
                "fact": "Khu chung cư cũ biến đổi thành tổ hợp cafe, mỗi căn hộ một style. Đi thang máy phải trả tiền (khoảng 5k-10k/lượt).",
                "insight_gap": "Kịch bản châm biếm: 'Cẩm nang sinh tồn khi đi cafe chung cư 42': Làm sao để không mất tiền thang máy mà vẫn check-in được hết các tầng."
            },
            {
                "name": "Bến Bạch Đằng lúc hoàng hôn",
                "fact": "Nơi ngắm hoàng hôn ngắm Landmark 81 cực đẹp nhưng siêu đông cặp đôi và các bạn làm TikToker ra quay giật giật.",
                "insight_gap": "Góc POV hài hước: 'Một mét vuông 10 ông TikToker' - Đi tìm sự bình yên giả trân tại bến Bạch Đằng."
            }
        ],
        "hidden_gem": [
            {
                "name": "Hẻm Nhật Bản (Little Japan Town - Lê Thánh Tôn)",
                "fact": "Con hẻm yên tĩnh ban ngày với các cửa gỗ kéo style Nhật, nhưng ban đêm biến thành khu phố đèn đỏ náo nhiệt với các quán bar chìm.",
                "insight_gap": "Làm content theo format 'Khám phá hai mặt đối lập của một con hẻm' (Style chữa lành ban ngày vs Style quẩy ban đêm)."
            }
        ]
    }
}


def clean_input(text: str) -> str:
    """Chuẩn hóa tiếng Việt không dấu và viết liền để dễ map key"""
    text = text.lower().strip()
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'[đ]', 'd', text)
    text = text.replace("ho chi minh", "sai gon").replace("hcm", "sai gon")
    text = text.replace(" ", "_")
    return text


TOOLS = [
    {
        "name": "getActivity",
        "description": "Gợi ý địa điểm du lịch kèm fact và insight_gap cho content creator.",
        "parameters": {
            "city": "Tên thành phố. Chỉ hỗ trợ: 'Ha Noi' hoặc 'Sai Gon'.",
            "categories": "Danh mục hoạt động. Chỉ hỗ trợ: 'am_thuc', 'check_in', 'hidden_gem'.",
        },
        "example": "Action: getActivity(Ha Noi, am_thuc)",
    },
    {
        "name": "getContent",
        "description": "Tự động viết kịch bản video ngắn (TikTok/Reels) theo persona của creator và địa điểm đã chọn.",
        "parameters": {
            "activity_item": "Một phần tử dict từ kết quả getActivity (chứa name, fact, insight_gap).",
            "creator_persona": "Dict mô tả creator: name, tone_of_voice, catchphrases.",
            "trending_info": "(Tuỳ chọn) Dict chứa audio và format đang viral.",
        },
        "example": 'Action: getContent({"name": "...", "fact": "...", "insight_gap": "..."}, {"name": "Creator X", "tone_of_voice": "Hài hước", "catchphrases": ["Ủa alo?"]})',
    },
    {
        "name": "GetDuration",
        "description": "Phân tích thời lượng kịch bản, tốc độ nói và đưa ra khuyến nghị tối ưu nhịp độ video.",
        "parameters": {
            "content_output": "Dict kết quả trả về từ getContent.",
        },
        "example": "Action: GetDuration(<content_output dict>)",
    },
    {
        "name": "getScene",
        "description": "Chuyển kịch bản thành bản phân cảnh quay chi tiết (shot list) gồm góc máy, chuyển động và đạo cụ.",
        "parameters": {
            "content_output": "Dict kết quả trả về từ getContent.",
        },
        "example": "Action: getScene(<content_output dict>)",
    },
    {
        "name": "generate_seo_metadata",
        "description": "Sinh metadata SEO cho video ngắn dựa trên output của getContent.",
        "parameters": {
            "content_output": "Dict kết quả trả về từ getContent.",
            "platform": "Chuỗi nền tảng: 'tiktok', 'youtube_shorts', hoặc 'reels'.",
        },
        "example": "Action: generate_seo_metadata(<content_output dict>, tiktok)",
    },    {
        "name": "budget_estimator",
        "description": "Ước tính chi phí sản xuất thực tế tại hiện trường cho Creator.",
        "parameters": {
            "city": "Tên thành phố nơi sản xuất. Ví dụ: 'Ha Noi' hoặc 'Sai Gon'.",
            "duration_days": "Số ngày sản xuất.",
            "crew_size": "Số lượng nhân sự tham gia (mặc định 1)."
        },
        "example": "Action: budget_estimator(Ha Noi, 3, 2)"
    },]


class ReActAgent:
    """
    ReAct-style Agent with conversation history and cross-turn state persistence.
    Fixes:
      1. self.history is now read and written — enables follow-up queries like "kịch bản vừa tạo".
      2. self.last_content_output stores the last getContent result so downstream tools
         (GetDuration, getScene, generate_seo_metadata) can reference it without re-running.
      3. _execute_tool auto-saves getContent output into self.last_content_output.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        # FIX 1: history now accumulates turns so follow-up queries have context
        self.history: List[str] = []
        # FIX 2: persist last getContent output across run() calls
        self.last_content_output: Optional[dict] = None

    def get_system_prompt(self) -> str:
        tool_blocks = []
        for t in self.tools:
            params = "\n".join([f"    - {k}: {v}" for k, v in t.get("parameters", {}).items()])
            tool_blocks.append(
                f"  Tool: {t['name']}\n"
                f"  Description: {t['description']}\n"
                f"  Parameters:\n{params}\n"
                f"  Example: {t.get('example', '')}"
            )
        tool_section = "\n\n".join(tool_blocks)

        return f"""You are a travel content assistant. You ONLY answer questions using the tools listed below.

RULES:
1. You MUST use a tool to look up information. Never answer from memory or make up data.
2. If the user's question cannot be answered by any available tool, respond with:
   Final Answer: I don't know. This question is outside the scope of my available tools.
3. Always follow the exact format below. Do not skip steps.
4. When the user refers to "kịch bản vừa tạo", "kết quả trên", or "video trên", use the
   content_output data already provided in the conversation context — do NOT call getContent again.

AVAILABLE TOOLS:
{tool_section}

FORMAT (follow exactly):
Thought: <your reasoning about what to do next>
Action: tool_name(arguments)
Observation: <result returned by the tool — filled in automatically>
... (repeat Thought/Action/Observation as needed)
Final Answer: <your final response to the user>"""

    def _build_prompt(self, user_input: str) -> str:
        """
        Build the full prompt by prepending conversation history and, if relevant,
        injecting the last content_output so follow-up tools can reference it directly.
        """
        import json

        parts = []

        # Inject persisted content_output when user refers to a previous result
        followup_triggers = [
            "vừa tạo", "kịch bản trên", "kết quả trên", "kết quả đó",
            "trên đó", "video trên", "kịch bản vừa", "output trên"
        ]
        user_lower = user_input.lower()
        if self.last_content_output and any(kw in user_lower for kw in followup_triggers):
            injected = json.dumps(self.last_content_output, ensure_ascii=False)
            parts.append(f"[Kịch bản đã tạo ở lượt trước — dùng trực tiếp làm content_output]:\n{injected}\n")

        # Append previous conversation turns
        if self.history:
            parts.append("\n".join(self.history))

        parts.append(f"User: {user_input}")
        return "\n".join(parts)

    def run(self, user_input: str, verbose: bool = False) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        current_prompt = self._build_prompt(user_input)
        steps = 0

        while steps < self.max_steps:
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            response_text = result["content"]

            logger.log_event("AGENT_STEP", {"step": steps, "response": response_text})

            # Final Answer found → save history and return
            final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL)
            if final_match:
                # FIX 1: persist this turn into history
                self.history.append(f"User: {user_input}")
                self.history.append(f"Assistant: {response_text}")
                logger.log_event("AGENT_END", {"steps": steps})
                return final_match.group(1).strip()

            # Parse Action: tool_name(arguments)
            action_match = re.search(r"Action:\s*(\w+)\((.*)\)", response_text, re.DOTALL)
            if action_match:
                tool_name = action_match.group(1).strip()
                tool_args = action_match.group(2).strip()
                observation = self._execute_tool(tool_name, tool_args)

                if verbose:
                    thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\Z)", response_text, re.DOTALL)
                    thought = thought_match.group(1).strip() if thought_match else ""
                    obs_preview = observation[:200] + ("..." if len(observation) > 200 else "")
                    print(f"\n{'─' * 50}")
                    print(f" Step {steps + 1}")
                    print(f"{'─' * 50}")
                    print(f" Thought   : {thought}")
                    print(f" Action    : {tool_name}({tool_args[:100]}{'...' if len(tool_args) > 100 else ''})")
                    print(f" Observation: {obs_preview}")
                    print(f"{'─' * 50}")

                current_prompt += f"\n{response_text}\nObservation: {observation}"
            else:
                if verbose:
                    thought_match = re.search(r"Thought:\s*(.*)", response_text, re.DOTALL)
                    thought = thought_match.group(1).strip() if thought_match else response_text.strip()
                    print(f"\n{'─' * 50}")
                    print(f" Step {steps + 1}")
                    print(f"{'─' * 50}")
                    print(f" Thought   : {thought[:200]}{'...' if len(thought) > 200 else ''}")
                    print(f"{'─' * 50}")
                current_prompt += f"\n{response_text}"

            steps += 1

        logger.log_event("AGENT_END", {"steps": steps})
        return "Max steps reached without a Final Answer."

    # ─────────────────────────────────────────────
    # Tool implementations (static / class methods)
    # ─────────────────────────────────────────────

    @staticmethod
    def getActivity(city: str, categories: str) -> dict:
        city_key = clean_input(city)
        cate_key = clean_input(categories)

        if city_key not in ACTIVITIES_DB:
            return {"error": f"Hiện tại tool chỉ hỗ trợ dữ liệu cho 'ha_noi' hoặc 'sai_gon'. Bạn nhập: '{city}'"}

        if cate_key not in ACTIVITIES_DB[city_key]:
            valid_cates = ", ".join(ACTIVITIES_DB[city_key].keys())
            return {"error": f"Không tìm thấy danh mục '{categories}'. Hãy chọn một trong các danh mục: {valid_cates}"}

        return {
            "status": "success",
            "city": city,
            "category": categories,
            "data": ACTIVITIES_DB[city_key][cate_key]
        }

    @staticmethod
    def budget_estimator(city: str, duration_days: int, crew_size: int = 1) -> dict:
        """
        Tool ước tính chi phí sản xuất thực tế tại hiện trường cho Creator.
        """
        city_key = clean_input(city)
        base_costs = {
            "ha_noi": {"hotel": 400000, "food": 250000, "move": 100000},
            "sai_gon": {"hotel": 500000, "food": 300000, "move": 120000}
        }

        cost = base_costs.get(city_key, {"hotel": 300000, "food": 200000, "move": 80000})
        total = (cost["hotel"] + cost["food"] + cost["move"]) * duration_days * crew_size

        return {
            "status": "success",
            "estimated_total": f"{total:,} VND",
            "breakdown": {
                "di_chuyen_noi_thanh": f"{(cost['move'] * duration_days):,} VND",
                "an_uong_trai_nghiem": f"{(cost['food'] * duration_days * crew_size):,} VND"
            },
            "monetization_tip": "Khuyến nghị chèn 1 slot tiếp thị liên kết (Affiliate) đồ dùng du lịch hoặc liên hệ homestay xin tài trợ chỗ ở để giảm 40% chi phí này."
        }

    @staticmethod
    def getContent(activity_item: dict, creator_persona: dict, trending_info: dict = None) -> dict:
        location = activity_item.get("name", "Địa điểm bí ẩn")
        fact = activity_item.get("fact", "Một sự thật thú vị chưa được tiết lộ.")
        insight_gap = activity_item.get("insight_gap", "Góc tiếp cận độc lạ chưa ai làm.")

        creator_name = creator_persona.get("name", "Creator X")
        tone = creator_persona.get("tone_of_voice", "Hài hước, châm biếm")
        catchphrases = creator_persona.get("catchphrases", ["Hết cứu", "Ủa alo?", "Thực tế là..."])

        p1 = catchphrases[0] if len(catchphrases) > 0 else "Thực tế là..."
        p2 = catchphrases[1] if len(catchphrases) > 1 else "Hết cứu!"
        p3 = catchphrases[2] if len(catchphrases) > 2 else "Ủa alo?"

        audio = trending_info.get("audio", "Nhạc nền lôi cuốn đang viral") if trending_info else "Nhạc nền xu hướng TikTok"
        v_format = trending_info.get("format", "POV Shorts") if trending_info else "POV Clip ngắn"

        title_suggestions = [
            f"Đừng đi {location} nếu chưa biết sự thật này!",
            f"Cú lừa mang tên {location}? {p1}...",
            f"Trải nghiệm {location} theo phong cách... hành xác! ({p2})"
        ]

        script_scenes = [
            {
                "time": "00:00 - 00:05",
                "visual": f"Cảnh mở màn giật gân: {creator_name} đứng trước mặt camera, biểu cảm hoang mang/châm biếm tại {location}. Text trên màn hình hiện lớn: 'Cú lừa {location}?'",
                "audio_voiceover": f"[{audio} bật lên dồn dập] Trên mạng review {location} lung linh lắm đúng không? Nhưng {p1}, có những sự thật mà không ai nói cho bạn biết!"
            },
            {
                "time": "00:05 - 00:25",
                "visual": f"Cắt cảnh (B-roll) quay cận cảnh thực tế khốc liệt: {fact}. {creator_name} quay lén hoặc có hành động tương tác hài hước.",
                "audio_voiceover": f"Đấy, nhìn xem! {fact}. Người ta đi du lịch là để chữa lành, còn đi kiểu này là để 'chữa lợn lành thành lợn què'. {p2}!"
            },
            {
                "time": "00:25 - 00:45",
                "visual": f"Quay {creator_name} ngồi trải nghiệm thực tế, mặt 'bất lực' nhưng đưa ra giải pháp/góc nhìn độc lạ.",
                "audio_voiceover": f"Thay vì làm clip khen đẹp như các idol khác, mình mách bạn cách xử lý này: {insight_gap}. Đi du lịch là phải có cái đầu lạnh!"
            },
            {
                "time": "00:45 - 00:60",
                "visual": f"{creator_name} cười trừ, giơ tay chào hoặc làm động tác đặc trưng của kênh. Text kêu gọi hành động hiện lên.",
                "audio_voiceover": f"Tóm lại là {p3}, anh em có dám thử trải nghiệm kiểu hành xác này không? Comment bên dưới cho tôi biết nhé! Nhớ follow {creator_name} đấy."
            }
        ]

        return {
            "status": "success",
            "metadata": {
                "creator": creator_name,
                "tone_applied": tone,
                "format": v_format,
                "audio": audio
            },
            "title_suggestions": title_suggestions,
            "script_scenes": script_scenes
        }

    @staticmethod
    def GetDuration(content_output: dict) -> dict:
        if content_output.get("status") != "success":
            return {"error": "Dữ liệu đầu vào từ getContent không hợp lệ hoặc thiếu kịch bản."}

        scenes = content_output.get("script_scenes", [])
        creator_name = content_output.get("metadata", {}).get("creator", "Creator")

        total_words = 0
        total_seconds = 0

        for scene in scenes:
            voiceover = scene.get("audio_voiceover", "")
            clean_voiceover = re.sub(r'\[.*?\]', '', voiceover).strip()
            word_count = len(clean_voiceover.split())
            total_words += word_count

            time_range = scene.get("time", "00:00 - 00:00")
            try:
                end_time_str = time_range.split("-")[1].strip()
                seconds = int(end_time_str.split(":")[1])
                if seconds > total_seconds:
                    total_seconds = seconds
            except (IndexError, ValueError):
                total_seconds = 60

        wpm = (total_words / total_seconds) * 60 if total_seconds > 0 else 0

        if wpm > 150:
            speaking_pace = "Bắn rap / Dồn dập (Cực kỳ hợp với TikTok Shorts / Reels)"
        elif wpm < 110:
            speaking_pace = "Chậm rãi / Thong thả (Hợp với style chữa lành, ASMR)"
        else:
            speaking_pace = "Vừa phải / Chuẩn điện ảnh"

        hook_sec = 5
        cta_sec = 15
        body_sec = total_seconds - (hook_sec + cta_sec)

        duration_breakdown = {
            "hook_segment": f"{hook_sec}s (Chiếm {round((hook_sec/total_seconds)*100, 1)}% tổng thời lượng) - Giữ chân 3s đầu",
            "body_segment": f"{body_sec}s (Chiếm {round((body_sec/total_seconds)*100, 1)}% tổng thời lượng) - Truyền tải nội dung",
            "cta_segment": f"{cta_sec}s (Chiếm {round((cta_sec/total_seconds)*100, 1)}% tổng thời lượng) - Kêu gọi tương tác"
        }

        optimization_recommendations = [
            f"Tốc độ nói trung bình đạt {round(wpm)} từ/phút ({speaking_pace}). {creator_name} cần giữ nhịp điệu này để không bị tụt tương tác.",
            f"Phần 'The Body' kéo dài {body_sec}s, khuyến nghị chèn thêm ít nhất 4-5 source quay B-roll (cận cảnh món ăn/địa điểm) để tránh tạo cảm giác nhàm chán.",
            "Đoạn kết kêu gọi hành động (CTA) dài 15s có rủi ro bị người dùng lướt qua sớm. Hãy lồng thêm câu hỏi gây tranh cãi ở giây thứ 50 để kích thích comment."
        ]

        return {
            "status": "success",
            "video_duration_analysis": {
                "total_duration": f"{total_seconds} giây",
                "total_words_to_speak": total_words,
                "calculated_wpm": round(wpm, 1),
                "pace_rating": speaking_pace
            },
            "structure_breakdown": duration_breakdown,
            "retention_insights": optimization_recommendations
        }

    @staticmethod
    def getScene(content_output: dict) -> dict:
        # Validate input
        if not isinstance(content_output, dict) or content_output.get("status") != "success":
            return {"error": "Dữ liệu đầu vào từ getContent không hợp lệ."}

        script_scenes = content_output.get("script_scenes", [])
        creator_name = content_output.get("metadata", {}).get("creator", "Creator")

        shot_list = []

        # Templates for shot sizes and camera movements
        shot_types = [
            "Extreme Close-up (Đặc tả biểu cảm mặt)",
            "Medium Shot (Trung cảnh ngang ngực)",
            "POV (Góc nhìn thứ nhất)",
            "Wide Shot (Toàn cảnh bối cảnh)"
        ]
        camera_movements = [
            "Static (Giữ máy cố định)",
            "Push-in (Dịch máy vào gần chậm)",
            "Pan Left/Right (Quét máy sang ngang)",
            "Handheld (Cầm tay rung lắc tự nhiên)"
        ]

        for idx, scene in enumerate(script_scenes):
            time_frame = scene.get("time", "00:00 - 00:05")
            visual_desc = scene.get("visual", "")
            voiceover = re.sub(r'\[.*?\]', '', scene.get("audio_voiceover", "")).strip()

            shot_type = shot_types[idx % len(shot_types)]
            movement = camera_movements[idx % len(camera_movements)]

            if idx == 0:
                director_note = (
                    "Hook: Giữ chân người xem trong 3s đầu. Sử dụng biểu cảm cường điệu, text lớn và jump-cut để tăng retention."
                )
                props = ["Điện thoại quay", "Mic không dây"]
            elif idx == len(script_scenes) - 1:
                director_note = "Kết: Creator nhìn vào camera, CTA rõ ràng, kêu gọi follow/comment."
                props = ["Đạo cụ nhận diện kênh"]
            else:
                director_note = "B-roll: xen kẽ close-up và wide, chuyển cảnh mỗi 2-3s để giữ nhịp." 
                props = ["Tripod/Gimbal", "Phụ kiện trang trí"]

            shot_item = {
                "scene_number": idx + 1,
                "time_range": time_frame,
                "script_context": visual_desc,
                "example_voiceover": voiceover,
                "cinematography": {
                    "shot_size": shot_type,
                    "camera_movement": movement,
                    "framing_guide": f"Bố cục 1/3, đặt camera ngang tầm mắt, tránh cắt sát đầu của {creator_name}."
                },
                "production_details": {
                    "equipment_needed": props,
                    "director_note": director_note
                }
            }
            shot_list.append(shot_item)

        summary = {
            "total_shots_to_film": len(shot_list),
            "estimated_shooting_time": f"{max(20, len(shot_list)*5)} - {max(30, len(shot_list)*8)} phút",
            "aspect_ratio_target": "9:16 (Dọc - TikTok/Shorts/Reels)"
        }

        return {"status": "success", "storyboard_summary": summary, "detailed_shot_list": shot_list}

    @staticmethod
    def generate_seo_metadata(content_output: dict, platform: str = "tiktok") -> dict:
        # Validate input
        if not isinstance(content_output, dict) or content_output.get("status") != "success":
            return {"error": "Dữ liệu đầu vào từ getContent không hợp lệ hoặc thiếu kịch bản."}

        valid_platforms = ["tiktok", "youtube_shorts", "reels"]
        platform = (platform or "tiktok").lower().strip()
        if platform not in valid_platforms:
            return {"error": f"Platform không hợp lệ: '{platform}'. Hãy chọn một trong: {', '.join(valid_platforms)}"}

        metadata = content_output.get("metadata", {})
        title_suggestions = content_output.get("title_suggestions", [])
        script_scenes = content_output.get("script_scenes", [])

        creator_name = metadata.get("creator", "Creator")
        tone = metadata.get("tone_applied", "hài hước")
        video_format = metadata.get("format", "POV Shorts")

        all_voiceover = " ".join(
            re.sub(r'\[.*?\]', '', scene.get("audio_voiceover", "")).strip()
            for scene in script_scenes
        )

        # Title selection and truncation
        seo_title = title_suggestions[0] if title_suggestions else f"Khám phá bí mật cùng {creator_name}!"
        title_char_limits = {"tiktok": 100, "youtube_shorts": 100, "reels": 125}
        limit = title_char_limits[platform]
        if len(seo_title) > limit:
            seo_title = seo_title[: limit - 3].rstrip() + "..."

        # Description: use first scene voiceover as hook
        first_voice = ""
        if script_scenes:
            first_voice = re.sub(r'\[.*?\]', '', script_scenes[0].get("audio_voiceover", "")).strip()
        hook_preview = (first_voice[:120] + "...") if len(first_voice) > 120 else first_voice

        desc_templates = {
            "tiktok": f"{hook_preview}\n\n👉 Theo dõi {creator_name} để không bỏ lỡ những góc nhìn độc lạ!\n💬 Comment trải nghiệm của bạn bên dưới nhé!",
            "youtube_shorts": f"{hook_preview}\n\n🔔 Subscribe {creator_name} để xem thêm video hài hước & chân thực!\n📌 Video thuộc series: {video_format}\n👍 Like nếu bạn thấy hữu ích!",
            "reels": f"{hook_preview}\n\nSave lại để xem khi cần! 🔖\nTag bạn bè vào đây 👇\nFollow {creator_name} để cập nhật thêm!",
        }
        description = desc_templates[platform]

        # Hashtags
        base_hashtags = ["#dulich", "#reviewdulich", "#khampha", "#vietnam", "#travel"]
        tone_hashtag_map = {
            "hài hước": ["#haivl", "#chiembi"],
            "châm biếm": ["#chiembi", "#noisuthat"],
            "chân thực": ["#reallife", "#noisuthat"],
        }
        tone_key = next((k for k in tone_hashtag_map if k in tone.lower()), None)
        tone_hashtags = tone_hashtag_map.get(tone_key, ["#creator"])

        platform_hashtag_map = {
            "tiktok": ["#tiktokdulich", "#fyp", "#xuhuong"],
            "youtube_shorts": ["#shorts", "#youtubeshorts"],
            "reels": ["#reels", "#reelsviral"],
        }
        platform_hashtags = platform_hashtag_map.get(platform, [])

        all_hashtags = list(dict.fromkeys(base_hashtags + tone_hashtags + platform_hashtags))
        hashtag_limits = {"tiktok": 10, "youtube_shorts": 8, "reels": 15}
        final_hashtags = all_hashtags[: hashtag_limits[platform]]

        # Keywords extraction
        stopwords = {"là", "và", "của", "có", "một", "để", "với", "cho", "bạn", "này", "mình", "cái", "rồi", "thì", "nhé", "đi", "ra", "lên", "vào", "đây"}
        raw_words = re.findall(r"\b[\wđ]{4,}\b", all_voiceover.lower())
        word_freq: Dict[str, int] = {}
        for w in raw_words:
            if w in stopwords:
                continue
            word_freq[w] = word_freq.get(w, 0) + 1
        top_keywords = sorted(word_freq, key=lambda x: word_freq[x], reverse=True)[:8]

        posting_tips_map = {
            "tiktok": ["Đăng vào khung giờ vàng: 11h-13h hoặc 19h-21h (VN).", "Dùng audio trending trong 48h đầu để tăng đề xuất.", "Reply comment sớm để kích hoạt thuật toán."],
            "youtube_shorts": ["Thêm mô tả ngắn + hashtag chính trong 100 ký tự đầu.", "Dùng thumbnail biểu cảm và caption kêu gọi hành động."],
            "reels": ["Chia sẻ lên Story ngay sau khi đăng.", "Kết thúc caption bằng câu hỏi để kích thích bình luận."]
        }

        return {
            "status": "success",
            "platform": platform,
            "seo_title": seo_title,
            "description": description,
            "hashtags": final_hashtags,
            "hashtag_string": " ".join(final_hashtags),
            "top_keywords": top_keywords,
            "posting_tips": posting_tips_map.get(platform, [])
        }

    # ─────────────────────────────────────────────
    # Tool dispatcher
    # ─────────────────────────────────────────────

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
                # FIX 3: auto-save for follow-up tool calls
                if isinstance(result, dict) and result.get("status") == "success":
                    self.last_content_output = result

            elif tool_name == "budget_estimator":
                parts = [a.strip().strip("\"'") for a in args.split(",")]
                if len(parts) == 2:
                    city, duration_days = parts
                    crew_size = 1
                elif len(parts) == 3:
                    city, duration_days, crew_size = parts
                else:
                    return "Error executing 'budget_estimator': expected arguments city, duration_days, [crew_size]."

                try:
                    result = ReActAgent.budget_estimator(city, int(duration_days), int(crew_size))
                except ValueError:
                    return "Error executing 'budget_estimator': duration_days and crew_size must be integers."

            elif tool_name == "GetDuration":
                parsed = json.loads(args)
                result = ReActAgent.GetDuration(parsed)

            elif tool_name == "getScene":
                parsed = json.loads(args)
                result = ReActAgent.getScene(parsed)

            elif tool_name == "generate_seo_metadata":
                parsed = json.loads(args)
                if isinstance(parsed, list) and len(parsed) == 2:
                    result = ReActAgent.generate_seo_metadata(parsed[0], parsed[1])
                elif isinstance(parsed, list) and len(parsed) == 1:
                    result = ReActAgent.generate_seo_metadata(parsed[0])
                else:
                    return "Error executing 'generate_seo_metadata': expected JSON array with [content_output, platform] or [content_output]."

            else:
                return f"Tool '{tool_name}' is registered but has no handler."

        except Exception as e:
            return f"Error executing '{tool_name}': {e}"

        return json.dumps(result, ensure_ascii=False)