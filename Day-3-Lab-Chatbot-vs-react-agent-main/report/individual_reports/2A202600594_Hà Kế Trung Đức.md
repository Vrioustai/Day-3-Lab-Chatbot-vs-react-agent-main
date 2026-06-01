# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Hà Kế Trung Đức
- **Student ID**: 2A202600594
- **Date**: 01/06/26

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: def getActivity / def getContent / def GetDuration / Mock Data (ACTIVITIES_DB) / Hashtags system
- **Code Highlights**: 

```python
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
```

```python
@staticmethod
def getContent(activity_item: dict, creator_persona: dict, trending_info: dict = None) -> dict:
    location = activity_item.get("name", "Địa điểm bí ẩn")
    fact = activity_item.get("fact", "Một sự thật thú vị chưa được tiết lộ.")
    insight_gap = activity_item.get("insight_gap", "Góc tiếp cận độc lạ chưa ai làm.")

    creator_name = creator_persona.get("name", "Creator X")
    tone = creator_persona.get("tone_of_voice", "Hài hước, châm biếm")
    
    # ... logic xử lý kịch bản, hashtag và trả về metadata ...

    return {
        "status": "success",
        "metadata": {
            "creator": creator_name,
            "tone_applied": tone,
        },
        "title_suggestions": [...],
        "script_scenes": [...]
    }
```

```python
@staticmethod
def GetDuration(content_output: dict) -> dict:
    if content_output.get("status") != "success":
        return {"error": "Dữ liệu đầu vào từ getContent không hợp lệ hoặc thiếu kịch bản."}

    scenes = content_output.get("script_scenes", [])
    total_words, total_seconds = 0, 0

    # ... logic phân tích số từ, số giây và nhịp độ nói (wpm) ...

    return {
        "status": "success",
        "video_duration_analysis": {
            "total_duration": f"{total_seconds} giây",
            "calculated_wpm": round(wpm, 1),
            "pace_rating": speaking_pace
        },
        "structure_breakdown": duration_breakdown,
        "retention_insights": optimization_recommendations
    }
```

### **Documentation: Tương tác của Mã nguồn với Vòng lặp ReAct**

## 1. Mock Data và Hashtags
Tôi đã thiết kế cấu trúc dữ liệu `ACTIVITIES_DB` (Mock Data) đóng vai trò như một cơ sở dữ liệu giả lập để Agent có thể truy xuất thông tin về các địa điểm, sự thật thú vị và `insight_gap`. Ngoài ra, tôi cũng tích hợp hệ thống Hashtag tự động dựa trên `platform` và `tone` của Creator để tối ưu hóa SEO cho video đầu ra.

## 2. Giai đoạn Act (Hành động)
* `getActivity`: Công cụ lấy dữ liệu từ `ACTIVITIES_DB` dựa trên thành phố và danh mục do LLM truyền vào. Nếu Agent đoán sai danh mục, hàm có cơ chế trả về lỗi chi tiết kèm danh sách các danh mục hợp lệ.
* `getContent`: Tool dùng để kết hợp thông tin địa điểm (từ `getActivity`) và persona của người sáng tạo nội dung (`creator_persona`) để tạo thành kịch bản video hoàn chỉnh.
* `GetDuration`: Tool đo lường thời lượng và nhịp độ nói (WPM) dựa trên kịch bản từ `getContent`, sau đó cung cấp các đề xuất tối ưu tỷ lệ giữ chân người xem (retention insights).

## 3. Giai đoạn Observe & Reason
* Dữ liệu từ `getActivity` cung cấp `Observation` quan trọng. Agent nhận về `status: success` kèm nội dung sự thật thú vị (`fact`) để chuyển sang bước tư duy tiếp theo.
* Khi đã có dữ liệu thực, Agent `Thought` rằng cần dùng dữ liệu đó để gọi tiếp `getContent`.
* Sau khi nhận kịch bản từ `getContent`, Agent tiếp tục lập luận và gọi `GetDuration` để phân tích thời lượng. Chuỗi dữ liệu được dẫn dắt liền mạch qua 3 bước thay vì để LLM tự "ảo giác" (hallucinate) thông tin hay phỏng đoán bừa bãi về độ dài video.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent bị kẹt khi gọi `getActivity` do tự nghĩ ra một danh mục không có trong hệ thống Mock Data.
- **Log Source**: `Tool Execution Failed: Không tìm thấy danh mục 'ẩm thực đường phố'...`
- **Diagnosis**: LLM đã suy đoán danh mục không khớp với khoá trong cấu trúc `ACTIVITIES_DB`. Do không có hướng dẫn từ lỗi, nó tiếp tục loay hoay gọi các danh mục sai khác.
- **Solution**: Đã nâng cấp hàm `getActivity` bằng cách bổ sung logic tự động trả về danh sách các danh mục hợp lệ (`valid_cates = ", ".join(ACTIVITIES_DB[city_key].keys())`) trực tiếp trong thông báo lỗi. Từ đó `Observation` cung cấp đúng gợi ý, giúp Agent tự sửa sai ngay ở vòng lặp sau.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Bước `Thought` giúp Agent nhận ra tính phụ thuộc của dữ liệu: cần phải có thông tin xác thực về địa điểm (bằng cách dùng tool `getActivity`) trước khi có thể viết kịch bản sâu sắc. Một chatbot thông thường có xu hướng tự tạo thông tin giả.
2.  **Reliability**: Trong các yêu cầu viết lách chung chung hoặc cần tốc độ phản hồi cực nhanh, Agent có độ trễ lớn và tiêu tốn nhiều tài nguyên hơn so với một lệnh prompt thông thường đến chatbot.
3.  **Observation**: Khả năng quan sát thông báo lỗi (ví dụ: cung cấp danh mục đúng) cho thấy Agent có thể linh hoạt tự sửa đổi chuỗi suy luận của chính nó, giúp tự hành động mượt mà hơn trong môi trường hạn chế về công cụ và dữ liệu.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Thay thế Mock Data (`ACTIVITIES_DB`) bằng việc kết nối API thời gian thực với các cơ sở dữ liệu lớn như Google Places API hoặc Foursquare.
- **Safety**: Cần thêm một bộ phận kiểm duyệt ngôn từ để đảm bảo nội dung sinh ra (đặc biệt là tone "châm biếm") không vi phạm tiêu chuẩn cộng đồng của các nền tảng (TikTok, YouTube).
- **Performance**: Xây dựng hệ thống bộ nhớ đệm (Caching) cho các lời gọi `getActivity` với các địa điểm phổ biến để tiết kiệm Token và rút ngắn độ trễ phản hồi của hệ thống.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
