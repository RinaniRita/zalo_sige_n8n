# Hướng dẫn Thiết lập Luồng Tự động hóa Lead Zalo bằng n8n

Chào bạn, dưới đây là các bước để đưa luồng tự động hóa Zalo OA -> Google Sheets vào hoạt động trên hệ thống n8n của bạn.
(Lưu ý: Hệ thống hiện tại đã chuyển sang dùng LLM cục bộ (Ollama - Qwen2.5) để tiết kiệm chi phí, và Node Gmail đã được loại bỏ theo yêu cầu).

## Bước 1: Import Workflow vào n8n

1. Mở trình duyệt và truy cập vào n8n của bạn: `https://zalo-n8n.ngrok.dev`
2. Ở menu bên trái, chọn **Workflows** -> Nhấn **Add Workflow**.
3. Ở góc trên cùng bên phải, nhấn vào nút **...** (Options) -> Chọn **Import from File**.
4. Chọn file `zalo_lead_workflow.json` nằm trong thư mục `d:\work\zalo_n8n` của bạn.

## Bước 2: Kết nối Tài khoản (Credentials)

Sau khi import, bạn sẽ thấy 2 node: Webhook Zalo OA và Google Sheets.

### Node Google Sheets
1. Nhấp đúp vào node **Save to Google Sheets**.
2. Ở mục **Credential for Google Sheets API**, chọn tài khoản Google của bạn (hoặc **Create New Credential** nếu chưa có).
3. Mode hiện tại là **Map Each Column Manually**, với Sheet được chọn là `Data`.

### Thiết lập Google Sheets (Quan trọng)
Luồng này sử dụng Sheet có tên là `Data` làm nơi chứa dữ liệu thô để tránh lỗi cấu trúc bảng của n8n.
1. Tạo một tab tên là `Data` trong file Google Sheets của bạn.
2. Tại ô **A1**, bạn hãy dán công thức sau để tự động tạo cột ID và tự động đánh số thứ tự:
   `={"ID"; ARRAYFORMULA(IF(B2:B<>""; ROW(B2:B)-1; ""))}`
3. Tại các ô tiếp theo, nhập tên cột tương ứng: **B1**: `Số điện thoại`, **C1**: `Tên FB`, **D1**: `Mail`.

## Bước 3: Cấu hình Webhook trên Zalo OA

1. Nhấp đúp vào node **Webhook Zalo OA**.
2. Đảm bảo Webhook URL được trỏ về `https://zalo-n8n.ngrok.dev/webhook-test/zalo-internal` (khi test) hoặc webhook production.
3. Trong file `.env` của thư mục code gốc, đường dẫn `N8N_WEBHOOK_URL` cũng đã được trỏ tương ứng.
4. (Optional) Zalo Bot Server FastAPI đang chạy tại `https://zalo.ngrok.dev` và dùng ngrok riêng biệt.

## Bước 4: Test & Chạy Thực tế (Activate)

1. Trên n8n, nhấn nút **Test Workflow** (hoặc Listen for Test Event ở Node Webhook).
2. Dùng điện thoại nhắn tin vào Zalo OA với nội dung có chứa số điện thoại để bot nhận diện.
3. Node Google Sheet sẽ tự động map (điền) dữ liệu vào các cột trong Sheet `Data` của bạn.
4. Nếu mọi thứ hoạt động trơn tru, hãy bật công tắc **Active** (Góc trên bên phải Workflow) để luồng này chạy ngầm 24/7.
