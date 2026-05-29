from fastapi import FastAPI, Request, Response, BackgroundTasks
import hashlib
import requests
import json
from backend.bot_server.config import ZALO_APP_ID, ZALO_SECRET_KEY, ZALO_OA_ACCESS_TOKEN, N8N_WEBHOOK_URL
from backend.bot_server.scripted_response import get_scripted_response
from backend.bot_server.services.rag_service import retrieve_context
from backend.bot_server.services.llm_service import generate_rag_response, extract_lead_info

app = FastAPI(title="Zalo Bot Server", version="2.0")

def send_zalo_message(user_id: str, text: str, buttons: list = None):
    """
    Sends a message to a Zalo user via Zalo OA OpenAPI.
    Supports Zalo Action Buttons (Template payload)
    """
    if not ZALO_OA_ACCESS_TOKEN:
        print("Missing ZALO_OA_ACCESS_TOKEN")
        return
        
    if text:
        text = text.replace("**", "")

        
    url = "https://openapi.zalo.me/v3.0/oa/message/cs"
    headers = {
        "access_token": ZALO_OA_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": text
        }
    }
    
    # Transform generic buttons into Zalo-specific format
    if buttons:
        zalo_buttons = []
        for btn in buttons:
            zalo_buttons.append({
                "title": btn.get("text", "Chi tiết"),
                "type": "oa.query.show",
                "payload": btn.get("callback", "callback")
            })
            
        payload["message"] = {
            "text": text,
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "buttons": zalo_buttons
                }
            }
        }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        print(f"[Zalo API Response] {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Failed to send Zalo message: {e}")

def push_to_n8n(data: dict):
    """
    Pushes extracted lead data to n8n webhook.
    """
    if not N8N_WEBHOOK_URL:
        print("Missing N8N_WEBHOOK_URL")
        return
        
    try:
        res = requests.post(N8N_WEBHOOK_URL, json=data)
        print(f"[n8n API Response] {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Failed to push to n8n: {e}")

def send_telegram_notification(data: dict):
    """
    Sends a message to the configured Telegram chat IDs when a lead is captured.
    """
    from backend.bot_server.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return
        
    chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_ID.split(",") if cid.strip()]
    
    phone = data.get('phone')
    clean_phone = "".join(filter(str.isdigit, phone))
    phone_link = f'<a href="tel:{clean_phone}">{phone}</a>'
    
    # Format a professional notification message
    message = (
        "🌟 <b>THÔNG BÁO LEAD MỚI TỪ ZALO BOT</b> 🌟\n\n"
        f"📞 Số điện thoại: {phone_link}\n"
    )
    
    for chat_id in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            res = requests.post(url, json=payload)
            print(f"[Telegram Notification] Sent to {chat_id}: status {res.status_code}")
        except Exception as e:
            print(f"Failed to send Telegram message to {chat_id}: {e}")

def process_zalo_message(user_id: str, message: str):
    print(f"[Webhook] Nhận tin nhắn từ {user_id}: {message}")
    
    # 1. HOT LEAD RADAR: Detect 10-digit Vietnamese phone numbers using regex
    import re
    cleaned_message = message.replace(".", "").replace(" ", "").replace("-", "")
    phone_match = re.search(r'(0[3|5|7|8|9][0-9]{8})', cleaned_message)
    
    if phone_match:
        hot_phone = phone_match.group(1)
        print(f"🎯 HOT LEAD DETECTED from user {user_id}: {hot_phone}")
        
        lead_info = {
            "phone": hot_phone
        }
        
        # Phat hien Lead moi -> Push to n8n & Telegram
        push_to_n8n(lead_info)
        send_telegram_notification(lead_info)
        
        # Phản hồi lịch sự ngay lập tức cho khách và dừng luồng xử lý (không gọi AI trả lời bừa bãi)
        thank_you_msg = (
            "Dạ, Viện SIGE xin chân thành cảm ơn anh/chị đã để lại thông tin liên hệ! 🌟\n\n"
            "Chúng tôi đã ghi nhận số điện thoại tư vấn của anh/chị. Trưởng phòng Tuyển sinh của Viện sẽ liên hệ trực tiếp cho mình trong thời gian sớm nhất để hỗ trợ kiểm tra hồ sơ và giữ suất học bổng ưu đãi tốt nhất nhé!\n\n"
            "Chúc anh/chị một ngày tốt lành! 😊"
        )
        send_zalo_message(user_id, thank_you_msg)
        return

    # 2. Hybrid Routing (Scripted vs RAG)
    scripted_res = get_scripted_response(message)
    
    if scripted_res:
        print("[Scripted] Su dung kich ban co san (Scripted)")
        send_zalo_message(user_id, scripted_res.get("text", ""), scripted_res.get("buttons"))
    else:
        print("[RAG] Su dung AI RAG de tra loi")
        # RAG Logic
        context = retrieve_context(message, top_k=3)
        reply = generate_rag_response(message, context)
        send_zalo_message(user_id, reply)

@app.get("/")
def home():
    # Meta tag cho Zalo Domain Verification (như bản Node.js cũ)
    html_content = """
    <html>
      <head>
        <meta name="zalo-platform-site-verification" content="P_E7SRh-1sT-mzndfkbcQd7io4ATcXqRDZCr" />
        <title>Zalo AI Bot Server</title>
      </head>
      <body>
        <h1>Zalo AI Bot Server is Running!</h1>
      </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

@app.get("/zalo_verifierP_E7SRh-1sT-mzndfkbcQd7io4ATcXqRDZCr.html")
def zalo_verification_file():
    html_content = """
    <html>
      <head>
        <meta name="zalo-platform-site-verification" content="P_E7SRh-1sT-mzndfkbcQd7io4ATcXqRDZCr" />
      </head>
      <body>
        Zalo Domain Verification
      </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

@app.post("/webhook")
async def zalo_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint nhận Webhook từ Zalo.
    """
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')
    
    # 1. Xác thực Zalo MAC (Security)
    x_zevent_signature = request.headers.get("x-zevent-signature")
    if x_zevent_signature:
        expected_mac = x_zevent_signature.replace("mac=", "") if x_zevent_signature.startswith("mac=") else x_zevent_signature
        timestamp = request.headers.get("x-zevent-timestamp", "")
        # Công thức: sha256(app_id + body_json + timestamp + secret_key)
        raw_mac = f"{ZALO_APP_ID}{body_str}{timestamp}{ZALO_SECRET_KEY}"
        mac = hashlib.sha256(raw_mac.encode('utf-8')).hexdigest()
        
        if mac != expected_mac:
            print(f"[MAC Error] Sai MAC Signature! Expect: {mac}, Got: {expected_mac}")
            # Tuỳ policy có thể return 400. Zalo dev doc khuyến nghị log lại.
    
    try:
        data = json.loads(body_str)
        event_name = data.get("event_name")
        print(f"[Webhook] Nhan su kien Zalo: {event_name}")
        
        if event_name == "user_send_text":
            user_id = data.get("sender", {}).get("id")
            message = data.get("message", {}).get("text", "")
            
            # Đưa tác vụ xử lý tin nhắn vào Background để trả về HTTP 200 ngay lập tức cho Zalo,
            # tránh việc Zalo chờ lâu quá sẽ gửi lại webhook (Retry).
            if user_id and message:
                background_tasks.add_task(process_zalo_message, user_id, message)
        else:
            print(f"[Skip] Bo qua su kien khong phai tin nhan van ban: {event_name}")
                
    except Exception as e:
        print(f"Error parsing Zalo webhook: {e}")
        
    # Luôn luôn trả về 200 OK cho Zalo
    return {"status": "ok"}
