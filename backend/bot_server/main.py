from fastapi import FastAPI, Request, Response, BackgroundTasks
import hashlib
import requests
import json
from backend.bot_server.config import ZALO_APP_ID, ZALO_SECRET_KEY, ZALO_OA_ACCESS_TOKEN, N8N_WEBHOOK_URL
from backend.bot_server.scripted_response import get_scripted_response
from backend.bot_server.services.rag_service import retrieve_context
from backend.bot_server.services.llm_service import generate_rag_response, extract_lead_info

app = FastAPI(title="Zalo Bot Server", version="2.0")

def send_zalo_message(user_id: str, text: str):
    """
    Sends a message to a Zalo user via Zalo OA OpenAPI.
    """
    if not ZALO_OA_ACCESS_TOKEN:
        print("Missing ZALO_OA_ACCESS_TOKEN")
        return
        
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

def process_zalo_message(user_id: str, message: str):
    print(f"[Webhook] Nhận tin nhắn từ {user_id}: {message}")
    
    # 1. Trích xuất thông tin Lead trong nền (Tên, SĐT, Email, Note)
    lead_info = extract_lead_info(message)
    lead_info["zalo_user_id"] = user_id
    lead_info["raw_message"] = message
    
    # Nếu lấy được SĐT hoặc Email, push về n8n
    if lead_info.get("phone") or lead_info.get("email"):
        print(f"[Lead] Phat hien Lead moi: {lead_info}")
        push_to_n8n(lead_info)

    # 2. Hybrid Routing (Scripted vs RAG)
    scripted_text = get_scripted_response(message)
    
    if scripted_text:
        print("[Scripted] Su dung kich ban co san (Scripted)")
        send_zalo_message(user_id, scripted_text)
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
