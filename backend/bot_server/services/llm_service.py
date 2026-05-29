"""
llm_service.py
==============
AI layer for the Zalo bot.

Functions:
  - extract_lead_info(message)  → dict with keys: full_name, phone, email
  - generate_rag_response(query, context) → str reply to send back to user

Uses OpenAI SDK directly (no LangChain dependency).
Field names match Google Sheet column order:
  Col A: id  |  Col B: phone  |  Col C: full_name  |  Col D: email
"""

import json
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

# Use local Ollama via OpenAI-compatible endpoint for cost efficiency
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" # required but unused
)
MODEL = "qwen2.5:7b-instruct"


# ─── Lead Extraction ─────────────────────────────────────────────────────────

def extract_lead_info(user_message: str) -> dict:
    """
    Scan the user message for contact details.

    Returns a dict with keys matching the Google Sheet schema:
      {
        "full_name": str | "",   ← Col C
        "phone":     str | "",   ← Col B
        "email":     str | "",   ← Col D
      }
    Returns all-empty dict if nothing is found (never raises).
    """
    prompt = f"""Bạn là AI trích xuất thông tin liên hệ từ tin nhắn của khách hàng Việt Nam.

Nhiệm vụ: Đọc tin nhắn bên dưới và trả về JSON với đúng 3 trường sau:
- "full_name": Họ và tên đầy đủ của khách. Để trống ("") nếu không có.
- "phone": Số điện thoại (chỉ số, không có khoảng cách hay dấu gạch ngang). Để trống nếu không có.
- "email": Địa chỉ email. Để trống nếu không có.

Quy tắc:
- Chỉ trả về JSON, không giải thích thêm.
- Nếu không có thông tin nào, trả về {{"full_name": "", "phone": "", "email": ""}}.
- Chỉ trích xuất số điện thoại VN hợp lệ (10 số bắt đầu bằng 0, hoặc +84).

Tin nhắn: "{user_message}"
"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)

        # Normalise keys — ensure all 3 fields exist
        return {
            "full_name": data.get("full_name", "").strip(),
            "phone":     data.get("phone", "").strip(),
            "email":     data.get("email", "").strip(),
        }
    except Exception as e:
        logger.error("extract_lead_info error: %s", e)
        return {"full_name": "", "phone": "", "email": ""}


# ─── RAG Response ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Bạn là trợ lý ảo AI của Viện SIGE (Viện Khoa học Giáo dục Toàn Cầu).
Nhiệm vụ của bạn là tư vấn chuyên nghiệp, thân thiện về du học Đài Loan.

Thông tin nội bộ của Viện SIGE để tham khảo:
<knowledge_base>
{context}
</knowledge_base>

Tuân thủ chính sách Zalo Bot Platform:
1. Chỉ tư vấn về dịch vụ du học Đài Loan của Viện SIGE. TỪ CHỐI mọi câu hỏi ngoài phạm vi, chính trị, tôn giáo hoặc độc hại.
2. Không bịa đặt thông tin. Nếu không có trong knowledge_base, hướng dẫn khách để lại SĐT để cán bộ tuyển sinh gọi lại.
3. Cam kết bảo mật 100% thông tin cá nhân khách hàng theo chính sách quyền riêng tư của Zalo và Viện SIGE.
4. Trả lời ngắn gọn, súc tích, dễ đọc. Không spam nhiều tin nhắn liên tiếp.
5. Cuối mỗi câu trả lời, khéo léo nhắc khách để lại Số điện thoại hoặc đăng ký tư vấn miễn phí 📞."""


def generate_rag_response(query: str, retrieved_context: str) -> str:
    """
    Generate a reply using the RAG context retrieved from FAISS.
    Falls back to a polite error message if OpenAI call fails.
    """
    system_msg = _SYSTEM_PROMPT.format(context=retrieved_context or "Không có thông tin bổ sung.")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system",  "content": system_msg},
                {"role": "user",    "content": query},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("generate_rag_response error: %s", e)
        return (
            "Xin lỗi, hệ thống đang bận. "
            "Bạn vui lòng để lại Số điện thoại để cán bộ tuyển sinh Viện SIGE gọi lại hỗ trợ nhé! 📞"
        )
