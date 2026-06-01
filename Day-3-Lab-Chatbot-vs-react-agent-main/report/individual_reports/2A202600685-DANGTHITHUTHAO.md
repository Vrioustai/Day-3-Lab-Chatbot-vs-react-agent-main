# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: ĐẶNG THỊ THU THẢO
- **Student ID**: 2A202600685
- **Date**: 01/06/26

---

## I. Technical Contribution (15 Points)

### Modules Implemented

Tôi chịu trách nhiệm implement hai tool trong pipeline của ReAct Agent:

- `getScene` — Chuyển kịch bản từ `getContent` thành shot list chi tiết để quay.
- `generate_seo_metadata` — Sinh metadata SEO (title, description, hashtag, keyword) theo từng platform.

---

### Code Highlights

#### `getScene`

```python
@staticmethod
def getScene(content_output: dict) -> dict:
    if not isinstance(content_output, dict) or content_output.get("status") != "success":
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
        shot_type = shot_types[idx % len(shot_types)]
        movement = camera_movements[idx % len(camera_movements)]

        if idx == 0:
            director_note = "Hook: Giữ chân người xem trong 3s đầu..."
            props = ["Điện thoại quay", "Mic không dây"]
        elif idx == len(script_scenes) - 1:
            director_note = "Kết: Creator nhìn vào camera, CTA rõ ràng..."
            props = ["Đạo cụ nhận diện kênh"]
        else:
            director_note = "B-roll: xen kẽ close-up và wide, chuyển cảnh mỗi 2-3s..."
            props = ["Tripod/Gimbal", "Phụ kiện trang trí"]

        shot_list.append({ ... })  # shot item đầy đủ

    return {"status": "success", "storyboard_summary": ..., "detailed_shot_list": shot_list}
```

Tool này nhận `content_output` từ `getContent`, duyệt qua từng scene và gán shot type + camera movement theo vòng lặp modulo. Điểm đáng chú ý là logic phân biệt 3 loại cảnh (hook / body / CTA) theo `idx`, thay vì hardcode, giúp tool hoạt động đúng bất kể kịch bản có bao nhiêu scene.

---

#### `generate_seo_metadata`

```python
@staticmethod
def generate_seo_metadata(content_output: dict, platform: str = "tiktok") -> dict:
    if not isinstance(content_output, dict) or content_output.get("status") != "success":
        return {"error": "Dữ liệu đầu vào từ getContent không hợp lệ."}

    valid_platforms = ["tiktok", "youtube_shorts", "reels"]
    platform = (platform or "tiktok").lower().strip()
    if platform not in valid_platforms:
        return {"error": f"Platform không hợp lệ: '{platform}'."}

    # Trích xuất keyword từ voiceover, lọc stopword
    raw_words = re.findall(r"\b[\wđ]{4,}\b", all_voiceover.lower())
    word_freq: Dict[str, int] = {}
    for w in raw_words:
        if w in stopwords:
            continue
        word_freq[w] = word_freq.get(w, 0) + 1
    top_keywords = sorted(word_freq, key=lambda x: word_freq[x], reverse=True)[:8]

    return {
        "status": "success",
        "seo_title": seo_title,
        "description": description,
        "hashtags": final_hashtags,
        "top_keywords": top_keywords,
        "posting_tips": posting_tips_map.get(platform, [])
    }
```

Tool này có ba phần logic chính: (1) giới hạn độ dài title theo từng platform, (2) build hashtag bằng cách merge base + tone + platform rồi deduplicate bằng `dict.fromkeys`, (3) trích xuất keyword từ voiceover bằng regex + đếm tần suất thay vì hardcode từ khóa.

---

### How These Tools Interact with the ReAct Loop

Cả hai tool đều là **downstream tools** — chúng không tự gọi API hay truy vấn DB, mà phụ thuộc hoàn toàn vào output của `getContent`. Trong ReAct loop, flow thường diễn ra như sau:

```
getActivity → getContent → getScene / generate_seo_metadata / GetDuration
```

Agent cần tự suy luận (Thought) rằng cần chạy `getContent` trước, lưu kết quả, rồi mới truyền vào các tool downstream. Để hỗ trợ điều này, `_execute_tool` có cơ chế `self.last_content_output` — tự động lưu kết quả `getContent` thành state để các lượt sau agent có thể tham chiếu lại mà không cần chạy lại từ đầu.

---

## II. Debugging Case Study (10 Points)

### Problem Description

Trong quá trình test, agent bị lỗi khi user nhập câu kiểu: *"Tạo shot list cho kịch bản vừa làm"*. Tool `getScene` trả về `{"error": "Dữ liệu đầu vào từ getContent không hợp lệ."}` dù kịch bản đã được tạo ở bước trước.

### Log Snippet

```
[AGENT_STEP] step=1 response="Thought: Cần gọi getScene với content_output từ lượt trước.
Action: getScene({})"
[AGENT_STEP] step=2 response="Observation: {'error': 'Dữ liệu đầu vào từ getContent không hợp lệ.'}"
```

### Diagnosis

Nguyên nhân nằm ở **prompt, không phải code tool**: khi agent parse argument `{}` từ string `getScene({})`, nó truyền một dict rỗng thay vì `content_output` thực sự. LLM không có cơ chế tự nhớ kết quả từ lượt trước vì mỗi lần `run()` sinh ra prompt mới, không có state được inject vào.

Cụ thể: `_build_prompt` chưa inject `last_content_output` vào context khi user dùng từ khoá follow-up ("kịch bản vừa tạo", "kết quả trên"...).

### Solution

Thêm đoạn inject vào `_build_prompt`:

```python
followup_triggers = ["vừa tạo", "kịch bản trên", "kết quả trên", ...]
if self.last_content_output and any(kw in user_lower for kw in followup_triggers):
    injected = json.dumps(self.last_content_output, ensure_ascii=False)
    parts.append(f"[Kịch bản đã tạo ở lượt trước — dùng trực tiếp làm content_output]:\n{injected}\n")
```

Sau fix này, LLM nhìn thấy `content_output` thực sự trong context và truyền đúng vào `getScene`, không còn truyền dict rỗng.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**1. Reasoning — `Thought` block giúp gì?**

Với một chatbot thông thường, câu hỏi *"Làm shot list cho video về cà phê đường tàu Hà Nội"* sẽ nhận được câu trả lời hallucinate ngay lập tức — LLM tự bịa shot list dựa trên kiến thức chung. Với ReAct, `Thought` buộc agent phải lập luận: *"Chưa có kịch bản, phải gọi getActivity rồi getContent trước"*. Chuỗi Thought → Action → Observation tạo ra một dạng **grounding** — câu trả lời cuối cùng được xây trên data thực từ tool, không phải từ bộ nhớ của LLM.

**2. Reliability — Agent tệ hơn Chatbot khi nào?**

Agent thực sự tệ hơn trong hai trường hợp:

- **Câu hỏi đơn giản, không cần tool**: Hỏi *"Nên quay video dọc hay ngang cho TikTok?"* — chatbot trả lời ngay trong 1 giây, còn agent mất 3–4 step lòng vòng tìm tool phù hợp rồi vẫn không kết luận được.
- **Argument parsing phức tạp**: Khi args là nested JSON, agent hay bị lỗi parse do LLM sinh ra JSON không hợp lệ (thừa dấu phẩy, thiếu ngoặc). Chatbot không có vấn đề này vì không cần format output theo spec.

**3. Observation ảnh hưởng đến bước tiếp theo thế nào?**

Observation đóng vai trò **feedback loop** cho agent. Ví dụ: khi `getActivity` trả về `{"error": "city không hợp lệ"}`, LLM đọc observation này và tự điều chỉnh ở Thought tiếp theo: *"getActivity báo lỗi tên thành phố, thử lại với 'Ha Noi' thay vì 'Hà Nội'"*. Đây là điều chatbot không làm được — chatbot không có vòng lặp thử-sai, agent thì có.

---

## IV. Future Improvements (5 Points)

**Scalability:** Hiện tại tool dispatcher dùng chuỗi `if/elif` — thêm tool mới phải sửa trực tiếp vào `_execute_tool`. Cần refactor sang **tool registry pattern**: mỗi tool tự đăng ký handler, dispatcher chỉ lookup theo tên. Kết hợp với async queue (ví dụ Celery + Redis) để các tool chạy song song khi không có dependency.

**Safety:** Thêm một **Supervisor LLM** chạy song song, audit mỗi Action trước khi execute. Supervisor kiểm tra: tool có hợp lệ không, argument có bị prompt injection không, output có chứa thông tin nhạy cảm không. Cơ chế này quan trọng hơn khi agent được expose ra production với user thực.

**Performance:** Với hệ thống nhiều tool (20+ tools), việc nhét toàn bộ tool description vào system prompt làm tăng token cost và nhiễu. Giải pháp là dùng **vector DB để retrieve tool** — embed mô tả từng tool, mỗi lượt chỉ inject top-k tool liên quan nhất vào prompt thay vì toàn bộ danh sách.