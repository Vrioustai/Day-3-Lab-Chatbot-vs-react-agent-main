# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: LÂM VĂN TÀI
- **Student ID**: 2A202600938
- **Date**: 01/06/26

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: def budget_estimator / def getScene
- **Code Highlights**: 

```python
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
```

```python
@staticmethod
def getScene(content_output: dict) -> dict:
    if content_output.get("status") != "success":
        return {"error": "Dữ liệu đầu vào từ getContent không hợp lệ."}

    script_scenes = content_output.get("script_scenes", [])
    creator_name = content_output.get("metadata", {}).get("creator", "Creator")

    shot_list = []

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

        shot_item = {
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
        }
        shot_list.append(shot_item)

    return {
        "status": "success",
        "storyboard_summary": {
            "total_shots_to_film": len(shot_list),
            "estimated_shooting_time": "30 - 45 phút tại hiện trường",
            "aspect_ratio_target": "9:16 (Dọc - TikTok/Shorts/Reels)"
        },
        "detailed_shot_list": shot_list
    }
```

- **Documentation**: [Brief explanation of how your code interacts with the ReAct loop]

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: [e.g., Agent caught in an infinite loop with `Action: search(None)`]
- **Log Source**: [Link or snippet from `logs/YYYY-MM-DD.log`]
- **Diagnosis**: [Why did the LLM do this? Was it the prompt, the model, or the tool spec?]
- **Solution**: [How did you fix it? (e.g., updated `Thought` examples in the system prompt)]

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
3.  **Observation**: How did the environment feedback (observations) influence the next steps?

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: [e.g., Use an asynchronous queue for tool calls]
- **Safety**: [e.g., Implement a 'Supervisor' LLM to audit the agent's actions]
- **Performance**: [e.g., Vector DB for tool retrieval in a many-tool system]

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
