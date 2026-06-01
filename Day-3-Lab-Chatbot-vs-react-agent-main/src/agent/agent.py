import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

# 🗄️ DATABASE: Được thiết kế chi tiết với Fact và Insight để Agent dễ "bắt chữ" lên kịch bản
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
]

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
        self._content_cache: Optional[dict] = None

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

STRICT RULES — violations will cause the system to reject your response:
1. NEVER answer from memory or training data. Every fact, script, duration, and shot list MUST come from a tool call.
2. Output EXACTLY ONE Thought + ONE Action per response, then STOP. Do not write the Observation yourself — the system fills it in.
3. Only write "Final Answer:" after you have received Observations from ALL required tools.
4. If a task requires multiple tools, call them ONE AT A TIME across separate responses.
5. If the question cannot be answered by any tool: Final Answer: I don't know. This is outside my available tools.

AVAILABLE TOOLS:
{tool_section}

FORMAT (one block per response — no exceptions):
Thought: <why you are calling this specific tool now>
Action: tool_name(arguments)

— STOP here. Wait for Observation before writing anything else. —"""

    @staticmethod
    def _summarize_observation(tool_name: str, observation: str) -> str:
        import json
        try:
            data = json.loads(observation)
        except Exception:
            return observation[:120]
        if "error" in data:
            return f"Error: {data['error']}"
        if tool_name == "getActivity":
            items = data.get("data", [])
            names = ", ".join(d["name"] for d in items)
            return f"Found {len(items)} places in {data.get('city', '?')}: {names}."
        if tool_name == "getContent":
            meta = data.get("metadata", {})
            scenes = data.get("script_scenes", [])
            return f"Script created for {meta.get('creator', '?')} — {len(scenes)} scenes, format: {meta.get('format', '?')}."
        if tool_name == "GetDuration":
            v = data.get("video_duration_analysis", {})
            return f"Duration: {v.get('total_duration', '?')}, {v.get('calculated_wpm', '?')} WPM — {v.get('pace_rating', '?')}."
        if tool_name == "getScene":
            s = data.get("storyboard_summary", {})
            return f"Shot list: {s.get('total_shots_to_film', '?')} shots, ~{s.get('estimated_shooting_time', '?')}."
        return observation[:120]

    @staticmethod
    def _parse_action(response_text: str):
        """Extract (tool_name, args) by counting parenthesis depth — handles nested parens in args."""
        m = re.search(r"Action:\s*(\w+)\(", response_text)
        if not m:
            return None
        tool_name = m.group(1)
        start = m.end()
        depth, i = 1, start
        while i < len(response_text) and depth > 0:
            if response_text[i] == '(':
                depth += 1
            elif response_text[i] == ')':
                depth -= 1
            i += 1
        if depth != 0:
            return None
        return tool_name, response_text[start:i - 1].strip()

    def run(self, user_input: str, verbose: bool = False) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        self._content_cache = None
        current_prompt = user_input
        called_tools: list[str] = []
        steps = 0

        while steps < self.max_steps:
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            response_text = result["content"]
            logger.log_event("AGENT_STEP", {"step": steps, "response": response_text})

            thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|\Z)", response_text, re.DOTALL)
            thought = thought_match.group(1).strip() if thought_match else ""
            parsed_action = self._parse_action(response_text)
            final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL)

            label = f"[{steps + 1}]"
            if verbose and thought:
                print(f"{label} 💭 {re.split(r'(?<=[.!?])\\s', thought)[0]}")

            if parsed_action:
                tool_name, tool_args = parsed_action
                if verbose:
                    flag = " ⚠ premature Final Answer ignored" if final_match else ""
                    print(f"{label} ⚡ {tool_name}({tool_args[:80]}{'...' if len(tool_args) > 80 else ''}){flag}")

                observation = self._execute_tool(tool_name, tool_args)
                called_tools.append(tool_name)
                logger.log_event("TOOL_CALL", {
                    "step": steps + 1, "thought": thought, "tool": tool_name,
                    "args": tool_args[:300], "observation": self._summarize_observation(tool_name, observation),
                })
                if verbose:
                    print(f"{label} 👁  {self._summarize_observation(tool_name, observation)}\n")
                current_prompt += f"\n{response_text}\nObservation: {observation}"

            elif final_match:
                if verbose:
                    print(f"{label} ✅ Final Answer")
                logger.log_event("AGENT_END", {"steps": steps})
                return final_match.group(1).strip()

            else:
                done = ", ".join(called_tools) if called_tools else "none"
                correction = (
                    f"\n[SYSTEM] Format violation. Tools called so far: [{done}]. "
                    f"Write exactly ONE Thought + ONE Action for the next required tool, then STOP. "
                    f"Do NOT write Observation or Final Answer."
                )
                logger.log_event("FORMAT_VIOLATION", {"step": steps + 1, "called": called_tools})
                if verbose:
                    print(f"{label} ⚠  Format violation — tools so far: [{done}]\n")
                current_prompt += correction

            steps += 1

        logger.log_event("AGENT_END", {"steps": steps})
        return "Max steps reached without a Final Answer."

    @staticmethod
    def getActivity(city: str, categories: str) -> dict:
        """
        Tool gợi ý địa điểm, kèm sự thật (fact) và khoảng trống nội dung (insight_gap)
        
        Parameters:
        - city (str): 'Ha Noi' hoặc 'Sai Gon'
        - categories (str): 'am_thuc', 'check_in', 'hidden_gem'
        """
        city_key = clean_input(city)
        cate_key = clean_input(categories)
        
        # Kiểm tra thành phố
        if city_key not in ACTIVITIES_DB:
            return {"error": f"Hiện tại tool chỉ hỗ trợ dữ liệu cho 'ha_no' hoặc 'sai_gon'. Bạn nhập: '{city}'"}
            
        # Kiểm tra category
        if cate_key not in ACTIVITIES_DB[city_key]:
            valid_cates = ", ".join(ACTIVITIES_DB[city_key].keys())
            return {"error": f"Không tìm thấy danh mục '{categories}'. Hãy chọn một trong các danh mục: {valid_cates}"}
            
        return {
            "status": "success",
            "city": city,
            "category": categories,
            "data": ACTIVITIES_DB[city_key][cate_key]
        }

    def getContent(activity_item: dict, creator_persona: dict, trending_info: dict = None) -> dict:
        """
        Tool tự động viết kịch bản bằng cách giả lập (mock) dữ liệu dựa trên đầu vào.
        Không gọi LLM, tự động sinh text chuẩn theo Persona và Insight Gap.
        """
        # 1. Bóc tách dữ liệu đầu vào
        location = activity_item.get("name", "Địa điểm bí ẩn")
        fact = activity_item.get("fact", "Một sự thật thú vị chưa được tiết lộ.")
        insight_gap = activity_item.get("insight_gap", "Góc tiếp cận độc lạ chưa ai làm.")
        
        creator_name = creator_persona.get("name", "Creator X")
        tone = creator_persona.get("tone_of_voice", "Hài hước, châm biếm")
        catchphrases = creator_persona.get("catchphrases", ["Hết cứu", "Ủa alo?", "Thực tế là..."])
        
        # Lấy các câu cửa miệng để chèn vào kịch bản cho thật
        p1 = catchphrases[0] if len(catchphrases) > 0 else "Thực tế là..."
        p2 = catchphrases[1] if len(catchphrases) > 1 else "Hết cứu!"
        p3 = catchphrases[2] if len(catchphrases) > 2 else "Ủa alo?"

        # 2. Giả lập định dạng Audio và Video nếu không có truyền vào
        audio = trending_info.get("audio", "Nhạc nền lôi cuốn đang viral") if trending_info else "Nhạc nền xu hướng TikTok"
        v_format = trending_info.get("format", "POV Shorts") if trending_info else "POV Clip ngắn"

        # 3. Tự động tạo Tiêu đề giả lập (Hook Titles) theo style giật gân
        title_suggestions = [
            f"Đừng đi {location} nếu chưa biết sự thật này!",
            f"Cú lừa mang tên {location}? {p1}...",
            f"Trải nghiệm {location} theo phong cách... hành xác! ({p2})"
        ]

        # 4. Tự động "may đo" kịch bản phân cảnh mô phỏng
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

        # 5. Trả về kết quả cấu trúc dict sạch sẽ
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
    def _extract_scenes(content_output: dict) -> list:
        """Try common key patterns to find the scenes list from a getContent output."""
        for key in ("script_scenes", "scenes"):
            val = content_output.get(key)
            if isinstance(val, list) and val:
                return val
        # one level deeper: {"script": {"scenes": [...]}}
        nested = content_output.get("script", {})
        if isinstance(nested, dict):
            for key in ("script_scenes", "scenes"):
                val = nested.get(key)
                if isinstance(val, list) and val:
                    return val
        return []

    def GetDuration(content_output: dict) -> dict:
        """
        Tool phân tích thời lượng kịch bản, tính toán tốc độ nói và tối ưu nhịp độ video.

        Input: Output (Dictionary) của hàm getContent.
        Output: Bản phân tích thông số thời lượng và lời khuyên giữ chân khán giả (Mock Data).
        """
        if content_output.get("status") != "success":
            return {"error": "Dữ liệu đầu vào từ getContent không hợp lệ hoặc thiếu kịch bản."}

        scenes = ReActAgent._extract_scenes(content_output)
        if not scenes:
            return {"error": "Không tìm thấy script_scenes. Hãy truyền trực tiếp output của getContent."}
        creator_name = content_output.get("metadata", {}).get("creator", "Creator")
        
        total_words = 0
        total_seconds = 0

        # 2. Xử lý thuật toán mô phỏng dựa trên text của kịch bản
        for scene in scenes:
            voiceover = scene.get("audio_voiceover", "")
            # Loại bỏ các ký tự nằm trong ngoặc vuông [Nhạc nền/SFX] để đếm từ thoại chuẩn
            clean_voiceover = re.sub(r'\[.*?\]', '', voiceover).strip()
            word_count = len(clean_voiceover.split())
            total_words += word_count

            # Bóc tách giây từ chuỗi "00:45 - 00:60" -> Lấy số 60 làm tổng giây
            time_range = scene.get("time", "00:00 - 00:00")
            try:
                end_time_str = time_range.split("-")[1].strip()
                seconds = int(end_time_str.split(":")[1])
                if seconds > total_seconds:
                    total_seconds = seconds
            except (IndexError, ValueError):
                total_seconds = 60 # Fallback mặc định nếu format lỗi

        # 3. Tính toán Tốc độ nói mô phỏng (WPM - Words Per Minute)
        # Công thức: (Tổng số từ / Tổng số giây) * 60 giây
        wpm = (total_words / total_seconds) * 60 if total_seconds > 0 else 0
        
        if wpm > 150:
            speaking_pace = "Bắn rap / Dồn dập (Cực kỳ hợp với TikTok Shorts / Reels)"
        elif wpm < 110:
            speaking_pace = "Chậm rãi / Thong thả (Hợp với style chữa lành, ASMR)"
        else:
            speaking_pace = "Vừa phải / Chuẩn điện ảnh"

        # 4. Phân bổ cấu trúc thời lượng hình học (Retention Structure)
        hook_sec = 5
        cta_sec = 15
        body_sec = max(0, total_seconds - (hook_sec + cta_sec))

        def pct(part): return round(part / total_seconds * 100, 1) if total_seconds > 0 else 0
        duration_breakdown = {
            "hook_segment": f"{hook_sec}s (Chiếm {pct(hook_sec)}% tổng thời lượng) - Giữ chân 3s đầu",
            "body_segment": f"{body_sec}s (Chiếm {pct(body_sec)}% tổng thời lượng) - Truyền tải nội dung",
            "cta_segment": f"{cta_sec}s (Chiếm {pct(cta_sec)}% tổng thời lượng) - Kêu gọi tương tác"
        }

        # 5. Tự động sinh Khuyến nghị tối ưu (Optimization Tips)
        optimization_recommendations = [
            f"Tốc độ nói trung bình đạt {round(wpm)} từ/phút ({speaking_pace}). {creator_name} cần giữ nhịp điệu này để không bị tụt tương tác.",
            f"Phần 'The Body' kéo dài {body_sec}s, khuyến nghị chèn thêm ít nhất 4-5 source quay B-roll (cận cảnh món ăn/địa điểm) để tránh tạo cảm giác nhàm chán.",
            "Đoạn kết kêu gọi hành động (CTA) dài 15s có rủi ro bị người dùng lướt qua sớm. Hãy lồng thêm câu hỏi gây tranh cãi ở giây thứ 50 để kích thích comment."
        ]

        # 6. Trả về kết quả phân tích sạch sẽ
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


    def getScene(content_output: dict) -> dict:
        """
        Tool chuyển đổi kịch bản chữ thành Bản phân cảnh quay chi tiết (Shot List).
        Tự động phân tích bối cảnh để gợi ý Góc máy (Shot Type), Chuyển động (Movement) và Đạo cụ.
        
        Input: Output (Dictionary) của hàm getContent.
        Output: Danh sách các cảnh quay chi tiết phục vụ việc bấm máy quay (Mock Data).
        """
        if content_output.get("status") != "success":
            return {"error": "Dữ liệu đầu vào từ getContent không hợp lệ."}

        script_scenes = ReActAgent._extract_scenes(content_output)
        if not script_scenes:
            return {"error": "Không tìm thấy script_scenes. Hãy truyền trực tiếp output của getContent."}
        creator_name = content_output.get("metadata", {}).get("creator", "Creator")
    
        shot_list = []
    
        # Danh sách các góc máy và chuyển động để map mô phỏng theo thứ tự logic của video ngắn
        shot_types = ["Extreme Close-up (Đặc tả biểu cảm mặt)", "Medium Shot (Trung cảnh ngang ngực)", "POV (Góc nhìn thứ nhất)", "Wide Shot (Toàn cảnh bối cảnh)"]
        camera_movements = ["Static (Giữ máy cố định)", "Push-in (Dịch máy vào gần chậm)", "Pan Left/Right (Quét máy sang ngang)", "Handheld (Cầm tay rung lắc tự nhiên)"]
    
        for idx, scene in enumerate(script_scenes):
            time_frame = scene.get("time", "00:00")
            visual_desc = scene.get("visual", "")
            shot_type = shot_types[idx % len(shot_types)]
            movement = camera_movements[idx % len(camera_movements)]

            if idx == 0:
                director_note = "Phải giữ chân người xem trong 3 giây đầu. Mặt Creator phải biểu cảm thật cường điệu hoặc đứng ở vị trí gây tò mò."
                props = "Điện thoại quay, Mic không dây gắn áo."
            elif idx == len(script_scenes) - 1:
                director_note = "Cảnh kết thúc, Creator nhìn thẳng vào ống kính để kêu gọi comment hành động. Text CTA nhảy ra bên cạnh tai."
                props = "Sản phẩm/Đạo cụ đặc trưng của kênh để tạo độ nhận diện."
            else:
                director_note = "Quay B-roll chèn xen kẽ liên tục mỗi 2 giây một góc máy khác để người xem không bị nhàm chán."
                props = "Chân máy (Tripod) di động hoặc Gimbal cầm tay."

            shot_list.append({
                "scene_number": idx + 1,
                "time_range": time_frame,
                "script_context": visual_desc,
                "cinematography": {
                    "shot_size": shot_type,
                    "camera_movement": movement,
                    "framing_guide": f"Bố cục 1/3, đặt camera ngang tầm mắt của {creator_name}."
                },
                "production_details": {
                    "equipment_needed": props,
                    "director_note": director_note
                }
            })

        return {
            "status": "success",
            "storyboard_summary": {
                "total_shots_to_film": len(shot_list),
                "estimated_shooting_time": "30 - 45 phút tại hiện trường",
                "aspect_ratio_target": "9:16 (Dọc - TikTok/Shorts/Reels)"
            },
            "detailed_shot_list": shot_list
        }
        
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
                if result.get("status") == "success":
                    self._content_cache = result

            elif tool_name == "GetDuration":
                content = self._content_cache
                if content is None:
                    return "Error: getContent must be called before GetDuration."
                result = ReActAgent.GetDuration(content)

            elif tool_name == "getScene":
                content = self._content_cache
                if content is None:
                    return "Error: getContent must be called before getScene."
                result = ReActAgent.getScene(content)

            else:
                return f"Tool '{tool_name}' is registered but has no handler."

        except Exception as e:
            return f"Error executing '{tool_name}': {e}"

        return json.dumps(result, ensure_ascii=False)
