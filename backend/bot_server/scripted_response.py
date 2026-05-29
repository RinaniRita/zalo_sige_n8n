import re
from typing import Optional

# Dictionary mapping identifying keys to scripted markdown responses and CTAs
MAIN_2_BUTTONS = [
    {"text": "🎯 Đăng ký tư vấn ngay", "callback": "start_lead_form"}, 
    {"text": "🎓 Khám phá các hệ học", "callback": "show_program_menu"}
]

SCRIPTED_ANSWERS = {
    # ================== 10 CASES TÂM LÝ ==================
    "case_1_dat_lich": {
        "text": """Chào bạn! Cảm ơn bạn đã liên hệ SIGE. 🎓✨\n\nBạn vui lòng để lại Số điện thoại để cán bộ tuyển sinh cấp cao gọi lại hỗ trợ lộ trình DU HỌC ĐÀI LOAN sớm nhất nhé👇""",
        "buttons": MAIN_2_BUTTONS
    },

    "case_2_chi_phi": {
        "text": """Chào bạn, gói dịch vụ du học bên SIGE trọn gói chỉ từ 36 cho đến 55 triệu với các hệ miễn 100% học phí hoặc thực tập có lương.\n\nBạn vui lòng bấm nút bên dưới để cán bộ tuyển sinh định hướng lộ trình phù hợp với tài chính gia đình nhé👇""",
        "buttons": MAIN_2_BUTTONS
    },

    "case_3_chon_nganh": {
        "text": """Chào bạn! Với hơn 20 năm kinh nghiệm B2B tại Đài Loan, SIGE cam kết chọn đúng trường, đúng ngành và bảo chứng việc làm đầu ra. 🎓✨\n\nBấm nút bên dưới để cán bộ tuyển sinh của SIGE hỗ trợ trực tiếp cho bạn nhé👇""",
        "buttons": MAIN_2_BUTTONS
    },

    "case_4_like_tuong_tac": {
        "text": (
            "Để cán bộ tuyển sinh SIGE hỗ trợ cho bạn tốt nhất, vui lòng để lại số điện thoại."
        )
    },

    "nudge_proactive_follow_up": {
        "text": """Bạn ơi, không biết thông tin trên đã giúp ích được cho mình chưa? ✨\n\nĐể tiết kiệm thời gian, cán bộ tuyển sinh SIGE có thể gọi điện giải đáp 1-1 cho bạn trong 15 phút tới không? Chỉ cần để lại SĐT thôi ạ! 🎯""",
        "buttons": [
            {"text": "📞 Gửi SĐT ngay", "callback": "start_lead_form"},
            {"text": "🏠 Xem Menu chính", "callback": "GET_STARTED"}
        ]
    },

    "case_5_dich_vu": {
        "text": """Chào bạn! SIGE không chỉ xử lý hồ sơ mà còn cam kết bảo chứng 100% cơ hội việc làm sau khi sang Đài Loan. 🎓✨\n\nVui lòng bấm vào nút dưới đây để kết nối với cán bộ tuyển sinh tư vấn ngay! 👇""",
        "buttons": MAIN_2_BUTTONS
    },

    "case_6_nghi_van": {
        "text": """Chào bạn! Quyền lợi "học bổng" hay "bảo chứng việc làm" tại SIGE là cam kết có thật từ mạng lưới doanh nghiệp hơn 20 năm qua. 🎓✨\n\nBấm nút bên dưới để cán bộ tuyển sinh hỗ trợ bạn kiểm chứng thông tin trực tiếp nhé! 👇""",
        "buttons": MAIN_2_BUTTONS
    },

    "case_7_phu_huynh": {
        "text": """Tại phiên làm việc sắp tới, cán bộ tuyển sinh SIGE rất sẵn lòng mời cả phụ huynh cùng tham gia để phân tích rõ bài toán tài chính và hợp đồng. 👨‍👩‍👧\n\nVui lòng bấm nút bên dưới thiết lập cuộc gọi cho cả gia đình nhé 👇""",
        "buttons": MAIN_2_BUTTONS
    },

    "case_9_ngu_dong": {
        "text": """Hồ sơ của bạn đang bảo lưu. Lịch hẹn trống của cán bộ tuyển sinh tuần này chỉ còn 3 suất.\n\nVui lòng bấm nút dưới đây để thiết lập lịch ưu tiên ngay hôm nay! 👇""",
        "buttons": MAIN_2_BUTTONS
    },

    "case_10_o_xa": {
        "text": """Chào bạn! SIGE hỗ trợ tư vấn và nộp hồ sơ Online & Zoom trên toàn quốc. 🌍\n\nVui lòng bấm nút dưới đây để thiết lập cuộc gọi phân tích hồ sơ nhé 👇""",
        "buttons": MAIN_2_BUTTONS
    },

    # ================== LOGIC PHÂN NHÁNH 2 (HOOKS) ==================
    "hook_14": {
        "text": """Hệ 1+4 (Hệ dự bị Đại học): Dành cho các bạn chưa có tiếng Trung. Học 1 năm tiếng, sau đó học tiếp 4 năm Đại học chính quy.\n\nBạn có muốn cán bộ tuyển sinh tư vấn trực tiếp lộ trình này ngay bây giờ không?""",
        "buttons": [
            {"text": "📞 Liên hệ ngay cho tôi", "callback": "start_lead_form"}
        ]
    },

    "hook_vhvl": {
        "text": """Hệ Vừa Học Vừa Làm: Cơ hội rèn luyện và thực tập hưởng lương 18-25tr/tháng ngay từ năm nhất. Thích hợp cho bạn muốn tự chủ tài chính.\n\nBạn có muốn cán bộ tuyển sinh tư vấn trực tiếp lộ trình này ngay bây giờ không?""",
        "buttons": [
            {"text": "📞 Liên hệ ngay cho tôi", "callback": "start_lead_form"}
        ]
    },

    "danh_sach_truong": {
        "text": """🏫 **DANH SÁCH CÁC TRƯỜNG ĐẠI HỌC LIÊN KẾT CHIẾN LƯỢC (Kỳ 9/2026)**\n\nDạ, SIGE tự hào là đối tác tuyển sinh trực tiếp của các trường Top đầu Đài Loan như: ĐH Minh Truyền, ĐH Lĩnh Đông, ĐH Đài Cương...\n\nTùy vào tính cách và nguyện vọng (Thích ở phố lớn, hay thích ở gần nhà máy để đi làm thêm), cán bộ tuyển sinh sẽ chọn trường phù hợp nhất.\n\n📞 Nhắn cho SIGE xin SỐ ĐIỆN THOẠI của anh/chị, cán bộ tuyển sinh sẽ gọi điện định hướng trực tiếp để không chọn sai trường nhé!""",
        "buttons": [
            {"text": "✍️ Tư vấn chọn trường", "callback": "start_lead_form"},
            {"text": "📞 Gặp cán bộ tuyển sinh", "callback": "show_contact"}
        ]
    },

    "hoc_bong_14": {
        "text": """🎯 **CHƯƠNG TRÌNH HỆ CHUYÊN BAN QUỐC TẾ 1+4 (DỰ BỊ ĐẠI HỌC)**\n\nHệ Dự bị 1+4 đang là chương trình HOT nhất tại SIGE lúc này!\n\n✅ Ưu điểm lớn nhất: Không yêu cầu biết tiếng Trung từ trước. Năm nhất được Chính phủ Đài Loan hỗ trợ 50% - 100% học phí.\n✅ Cam kết: Sang đến nơi, Giám đốc SIGE ở Đài Loan sẽ trực tiếp hỗ trợ các em vào KTX và làm thẻ cư trú.\n\n⚠️ Lưu ý: Hệ 1+4 chốt hồ sơ rất sớm và chỉ nhận các bạn có điểm cấp 3 từ 6.0 trở lên.\n\n📞 Anh/chị vui lòng để lại SỐ ĐIỆN THOẠI, Trưởng phòng Tuyển sinh sẽ gọi check điểm hồ sơ và giữ suất ưu đãi 100% học phí cho mình ngay nhé!""",
        "buttons": [
            {"text": "📥 Giữ suất ưu đãi 100%", "callback": "start_lead_form"},
            {"text": "🏫 Xem danh sách trường", "callback": "ask_danh_sach_truong"}
        ]
    },

    "he_vhvl_detail": {
        "text": """💆 **HỆ VỪA HỌC VỪA LÀM (VHVL) - CƠ HỘI TỰ CHỦ TÀI CHÍNH**\n\nChương trình Vừa học Vừa làm cực kỳ phù hợp để tự chủ tài chính!\n\n✅ Đi làm thêm có lương ngay tháng đầu tiên (Lương từ 18 - 25 triệu/tháng).\n✅ Trường Đại học Lĩnh Đông đang cấp 20 suất Học bổng 100% học phí độc quyền qua SIGE.\n\n🎁 SIGE đang tặng 05 suất [Miễn phí lớp học tiếng/ Tặng vali] cho hồ sơ đăng ký tuần này.\n\n📞 Chỉ còn đúng 3 suất nhận ưu đãi, anh/chị gõ SỐ ĐIỆN THOẠI để cán bộ tuyển sinh SIGE gọi điện tư vấn lộ trình và cách nhận lương thực tập sớm nhất nhé!""",
        "buttons": [
            {"text": "✅ Đăng ký nhận quà 🎁", "callback": "start_lead_form"},
            {"text": "🏫 Các hệ khác", "callback": "show_program_menu"}
        ]
    },

    "he_thac_si_detail": {
        "text": """Chương trình Thạc sĩ: Dành cho Cử nhân Đại học. Học bổng 50-100% tuỳ hồ sơ, dễ dàng tìm việc làm quản lý và định cư lâu dài.\n\nBạn có muốn cán bộ tuyển sinh tư vấn trực tiếp lộ trình này ngay bây giờ không?""",
        "buttons": [
            {"text": "📞 Liên hệ ngay cho tôi", "callback": "start_lead_form"}
        ]
    },

    "he_ngon_ngu_detail": {
        "text": """Hệ Ngôn ngữ: Dành cho người muốn học nhanh tiếng Trung tại bản xứ. Sau 6 tháng được làm thêm, chi phí đầu tư ban đầu thấp.\n\nBạn có muốn cán bộ tuyển sinh tư vấn trực tiếp lộ trình này ngay bây giờ không?""",
        "buttons": [
            {"text": "📞 Liên hệ ngay cho tôi", "callback": "start_lead_form"}
        ]
    },

    "tai_chinh_goi_dich_vu": {
        "text": """💰 **CÁC GÓI DỊCH VỤ DỊCH VỤ TƯ VẤN TRỌN GÓI TẠI SIGE**\n\nViện SIGE cung cấp các gói dịch vụ minh bạch, cam kết không phát sinh ẩn phí trong quá trình xử lý:\n\n1️⃣ **Gói Dịch vụ Cơ bản (36.000.000 VNĐ):**\n- Xử lý hồ sơ báo danh 2 nguyện vọng.\n- Dịch thuật, công chứng, hợp thức hóa hồ sơ.\n- Luyện phỏng vấn trường và phỏng vấn Visa.\n- Khám sức khỏe tại Việt Nam & Lệ phí Visa lần 1.\n\n2️⃣ **Gói Dịch vụ VIP (55.000.000 VNĐ):**\n- Bao gồm toàn bộ danh mục trọn gói của Gói Cơ bản.\n- **Tặng thêm:** Gói đào tạo tiếng Trung online/offline đạt trình độ A1-A2.\n- **Tặng thêm:** Vé máy bay 1 chiều sang Đài Loan.\n- **Hỗ trợ tại Đài Loan:** Thẻ lưu trú, thẻ lao động, bảo hiểm 6 tháng đầu, trọn bộ tư trang (chăn, ga, gối).\n\n3️⃣ **Gói Du học bằng Tiếng Anh (70.000.000 VNĐ):**\n- Bao gồm toàn bộ danh mục của Gói VIP.\n- **Đặc biệt:** Đào tạo tiếng Anh IELTS cam kết đầu ra 5.0.\n\n👇 *Vui lòng để lại Số điện thoại để chuyên viên tư vấn hỗ trợ chi tiết hơn về các gói này nhé!*""",
        "buttons": [
            {"text": "📊 Bảng phí chi tiết", "callback": "ask_tai_chinh_tong_quan"},
            {"text": "📞 Tư vấn gói phù hợp", "callback": "start_lead_form"}
        ]
    },

    "tai_chinh_tong_quan": {
        "text": """📊 **VẤN ĐỀ TÀI CHÍNH KHI DU HỌC ĐÀI LOAN**\n\nDạ, vấn đề tài chính phụ thuộc vào hồ sơ của mình có đạt học bổng hay không.\n\nChi phí đi qua SIGE là Trọn gói & Minh bạch 100%. Nếu học bạ đẹp, SIGE sẽ xin được suất miễn 100% học phí, lúc đó chi phí ban đầu cực kỳ thấp.\n\nĐể có bảng dự toán chính xác đến từng đồng (Không phát sinh), anh/chị vui lòng để lại SỐ ĐIỆN THOẠI. Cán bộ tuyển sinh sẽ gọi hỏi điểm cấp 3 và báo giá luôn ạ!""",
        "buttons": [
            {"text": "💰 Nhận bảng dự toán", "callback": "start_lead_form"},
            {"text": "💼 Tìm học bổng giảm phí", "callback": "ask_hoc_bong_chung"}
        ]
    },

    "ho_so_chuan_bi": {
        "text": """📂 **DANH MỤC HỒ SƠ CẦN CHUẨN BỊ (7 BƯỚC CHUYÊN NGHIỆP)**\n\nĐể kịp kỳ bay tháng 9/2026, bạn nên chuẩn bị sớm các giấy tờ sau:\n\n1️⃣ **Hồ sơ Học thuật:** Bằng tốt nghiệp THPT (hoặc bằng CĐ/ĐH) và Học bạ/Bảng điểm gốc.\n2️⃣ **Hồ sơ Cá nhân:** Hộ chiếu, CCCD, Giấy khai sinh bản sao mẫu mới nhất.\n3️⃣ **Lý lịch tư pháp:** Bản số 2 (do Sở Tư pháp cấp).\n4️⃣ **Sức khỏe:** Khám sức khỏe tổng quát theo mẫu du học tại các bệnh viện chỉ định.\n5️⃣ **Tài chính:** Sổ tiết kiệm gốc (từ 150 - 180 triệu VNĐ) mang tên SV hoặc Bố/Mẹ.\n6️⃣ **Chứng chỉ ngoại ngữ:** Bản gốc chứng chỉ TOCFL hoặc IELTS tương ứng với hệ du học.\n\n👉 *Viện SIGE sẽ hỗ trợ bạn scan, dịch thuật, công chứng và nộp hồ sơ xin giấy phép từ các cơ quan ban ngành tại Đài Loan.*""",
        "buttons": [
            {"text": "🚀 Bắt đầu làm hồ sơ", "callback": "ask_quy_trinh_chi_tiet"}
        ]
    },

    "quy_trinh_chi_tiet": {
        "text": """🚀 **QUY TRÌNH HỒ SƠ CHUẨN TẠI VIỆN SIGE (7 BƯỚC)**\n\nBạn sẽ được cán bộ chuyên trách của Viện hỗ trợ từng bước một:\n\n1. **Bước 1 (Ghi danh):** Ký hợp đồng tư vấn, nộp tiền cọc (10-20M) và điền form online.\n2. **Bước 2 (Nộp hồ sơ):** SV nộp 5 mục hồ sơ cơ bản (Bằng, học bạ, hộ chiếu...).\n3. **Bước 3 (Luyện phỏng vấn):** SV viết tự truyện, kế hoạch học tập và phỏng vấn với trường bên Đài Loan.\n4. **Bước 4 (Nộp Visa):** Sau khi có thông báo đỗ trường, SV đi khám sức khỏe và chuẩn bị sổ tiết kiệm gốc để nộp Visa.\n5. **Bước 5 (Phỏng vấn Visa):** Tùy hệ du học, SV có thể phải phỏng vấn trực tiếp tại Văn phòng Kinh tế & Văn hóa Đài Bắc (VPDB).\n6. **Bước 6 (Tập kết & Bay):** Sau khi có Visa, Viện xuất vé máy bay và hướng dẫn SV tập kết tại sân bay Nội Bài/Tân Sơn Nhất.\n7. **Bước 7 (Hạ cánh):** Trường đón SV tại sân bay Đài Loan, đưa về KTX và hỗ trợ làm thẻ cư trú.\n\n👉 *Toàn bộ quy trình thường kéo dài từ 3-4 tháng. Hãy bắt đầu ngay hôm nay!*""",
        "buttons": [
            {"text": "✍️ Đăng ký tư vấn lộ trình", "callback": "start_lead_form"}
        ]
    },

    "hoc_bong_chung": {
        "text": """💰 **CHÍNH SÁCH HỌC BỔNG & HỖ TRỢ TÀI CHÍNH TẠI SIGE**\n\nSIGE cam kết giúp sinh viên tối ưu hóa chi phí thông qua quỹ học bổng doanh nghiệp và chính sách của nhà trường:\n\n- **Học bổng 100%:** Dành cho sinh viên ưu tú hệ VHVL hoặc các trường như Đài Cương, John...\n- **Học bổng Chính phủ (Hệ 1+4):** Miễn phí năm đầu tiên cho hầu hết sinh viên.\n- **Gói Hỗ trợ SIGE:** Giảm phí dịch vụ cho SV có thành tích xuất sắc hoặc hoàn cảnh khó khăn.\n\n⚠️ **Lưu ý:** Ngay khi sang Đài Loan, sinh viên vẫn nên chuẩn bị một khoản tiền nhỏ (~40M) để đóng các tạp phí ban đầu, sau đó nhà trường sẽ xét duyệt hồ sơ và hoàn lại tiền học bổng theo quy định.\n\n👇 *Để biết chính xác mức Học bổng bạn có thể đạt được dựa trên Điểm trung bình hiện tại, hãy để lại Số điện thoại nhé!*""",
        "buttons": [
            {"text": "💰 Tính phí ưu đãi", "callback": "start_lead_form"},
            {"text": "📞 Gặp tư vấn viên", "callback": "show_contact"}
        ]
    },

    "co_hoi_viec_lam": {
        "text": """💼 **THỰC TẬP & CƠ HỘI VIỆC LÀM TẠI ĐÀI LOAN (Kỳ 2026)**\n\nDu học Đài Loan không chỉ là học tập, mà còn là bước khởi đầu cho sự nghiệp quốc tế bền vững.\n\n🔹 **Trong quá trình học:** \n- Bạn được phép đi làm thêm 20h/tuần (thu nhập ~15-18 triệu VNĐ/tháng).\n- Hệ VHVL thực tập tại doanh nghiệp đối tác với mức lương hỗ trợ lên đến 22 triệu VNĐ/tháng.\n\n🔹 **Sau khi tốt nghiệp:**\n- SIGE cam kết kết nối sinh viên với các doanh nghiệp tại Đài Loan để làm việc chính thức.\n- Mức lương khởi điểm cho kĩ sư/biên dịch trình độ đại học từ **31.150 TWD/tháng** (~25 triệu VNĐ) trở lên.\n- Hỗ trợ thủ tục chuyển đổi sang Visa lao động dài hạn hoặc định cư.\n\n👉 *Đài Loan đang rất thiếu nhân lực chất lượng cao trong các ngành Công nghệ, Dịch vụ và Y tế!*""",
        "buttons": [
            {"text": "💼 Tìm việc làm lương cao", "callback": "start_lead_form"}
        ]
    },

    "du_hoc_dai_loan": {
        "text": """🇹🇼 **HỆ SINH THÁI DU HỌC SIGE - TẦM NHÌN 20 NĂM**\n\nChào mừng bạn đến với SIGE AI - hệ thống hỗ trợ du học chuyên sâu được vận hành bởi Viện Khoa học Giáo dục Toàn Cầu.\n\n✨ **Tại sao bạn nên chọn SIGE?**\n- **Đối tác Chiến lược:** Liên kết trực tiếp với các trường đại học hàng đầu, đảm bảo tỷ lệ đỗ trường 99%.\n- **Bảo trợ Trọn đời:** Chúng tôi có văn phòng tại Đài Loan để hỗ trợ bạn những lúc gặp khó khăn trong sinh hoạt, ốm đau hay chuyển công tác.\n- **Minh bạch:** Phí dịch vụ rõ ràng, lộ trình đào tạo bài bản.\n\n✨ **Vibe từ Viện trưởng:**\n> *"Với mạng lưới 20 năm tâm huyết tại Đài Loan của tôi, SIGE không chỉ đưa bạn đi học, mà là đưa bạn vào một hệ sinh thái bảo trợ trọn đời. Sự thành công của sinh viên là thước đo giá trị lớn nhất của Viện SIGE."* \n— **ThS. Nguyễn Thị Điệp** (Viện trưởng SIGE)\n\n📍 Địa chỉ: Tầng 4, Tòa VINATA 2B, 289 Khuất Duy Tiến, TP. Hà Nội.\n🌐 Website: **www.sige.edu.vn**\nĐể nhận tư vấn lộ trình 1-1 miễn phí, vui lòng để lại số điện thoại!""",
        "buttons": [
            {"text": "🚀 Đăng Ký Tư Vấn VIP 1-1", "callback": "start_lead_form"}
        ]
    }
}

# Mapping of common phrase patterns to keys
QUERY_MAPPING = {
    # 10 Psychological Triggers
    r"đặt lịch|hẹn|đăng ký lịch|tư vấn ngay": "case_1_dat_lich",
    r"chi phí|giá|bao nhiêu tiền|tổng tiền|tài chính|học phí|sinh hoạt phí|gói dịch vụ|trọn gói": "case_2_chi_phi",
    r"ngành|học ngành|định hướng|chuyên ngành": "case_3_chon_nganh",
    r"dịch vụ|cung cấp gì|có gì": "case_5_dich_vu",
    r"lừa đảo|thật không|có tốt không|làm gì mà|có chắc|sợ": "case_6_nghi_van",
    r"bố mẹ|phụ huynh|gia đình|hỏi ý kiến|bàn với nhà": "case_7_phu_huynh",
    r"ở xa|tỉnh lẻ|ngoại thành|không ở hà nội|ngoại tỉnh": "case_10_o_xa",
    r"like|thả tim|hello|hi|chào|bắt đầu|tư vấn|tu van|tue vấn|tư vẩn|menu": "case_4_like_tuong_tac",

    # Standard Knowledge Base Triggers
    r"trường|danh sách|đại học|list trường": "danh_sach_truong",
    r"1\+4|dự bị|học tiếng trước": "hoc_bong_14",
    r"vhvl|vừa học làm|vừa học vừa làm|thực tập có lương": "he_vhvl_detail",
    r"thạc sĩ|thạc sỹ|sau đại học|master": "he_thac_si_detail",
    r"học tiếng|ngôn ngữ|trung tâm hoa ngữ|lớp tiếng": "he_ngon_ngu_detail",
    r"hồ sơ|thủ tục|giấy tờ|điều kiện|yêu cầu": "ho_so_chuan_bi",
    r"quy trình|các bước|lộ trình|phải làm gì": "quy_trinh_chi_tiet",
    r"học bổng|miễn phí|giảm phí|ưu đãi": "hoc_bong_chung",
    r"việc làm|làm gì xong|cơ hội nghề": "co_hoi_viec_lam",
    r"du học đài loan|tìm hiểu sige": "du_hoc_dai_loan",
    r"gói dịch vụ|gói tư vấn|trọn gói": "tai_chinh_goi_dich_vu"
}

def get_scripted_response(query: str) -> Optional[str]:
    """
    Checks if the user query matches any scripted response keywords.
    Returns the string text if found, otherwise None.
    Appends button text natively so it works on Zalo OA without templates.
    """
    query_clean = query.lower().strip()
    
    response_obj = None
    
    # 1. Exact match check
    if query_clean in SCRIPTED_ANSWERS:
        response_obj = SCRIPTED_ANSWERS[query_clean]
        
    # 2. Pattern match check
    if not response_obj:
        for pattern, key in QUERY_MAPPING.items():
            if re.search(pattern, query_clean):
                response_obj = SCRIPTED_ANSWERS[key]
                break
                
    if response_obj:
        text = response_obj.get("text", "")
        buttons = response_obj.get("buttons", [])
        if buttons:
            text += "\n\n(Bạn có thể nhấn vào Menu trên màn hình hoặc gõ các yêu cầu sau: "
            text += ", ".join([f"'{b['text']}'" for b in buttons])
            text += ")"
        return text
        
    return None
