import re
from typing import Optional

# Dictionary mapping identifying keys to scripted markdown responses (no buttons)
SCRIPTED_ANSWERS = {
    # ================== 10 CASES TÂM LÝ ==================
    "case_1_dat_lich": {
        "text": "Chào bạn! Cảm ơn bạn đã liên hệ SIGE. 🎓✨\n\nBạn vui lòng để lại Số điện thoại để cán bộ tuyển sinh cấp cao gọi lại hỗ trợ lộ trình DU HỌC ĐÀI LOAN sớm nhất nhé!"
    },

    "case_2_chi_phi": {
        "text": "Chào bạn, SIGE cung cấp các gói dịch vụ tư vấn du học trọn gói với chi phí tối ưu, kết hợp cùng các hệ miễn 100% học phí năm đầu hoặc thực tập có lương để giảm gánh nặng tài chính.\n\nBạn vui lòng để lại Số điện thoại để cán bộ tuyển sinh định hướng lộ trình phù hợp với tài chính gia đình nhé!"
    },

    "case_3_chon_nganh": {
        "text": "Chào bạn! Với hơn 20 năm kinh nghiệm B2B tại Đài Loan, SIGE cam kết chọn đúng trường, đúng ngành và bảo chứng việc làm đầu ra. 🎓✨\n\nHãy để lại Số điện thoại để cán bộ tuyển sinh của SIGE hỗ trợ trực tiếp cho bạn nhé!"
    },

    "case_4_like_tuong_tac": {
        "text": """🏫 VIỆN SIGE - ĐỒNG HÀNH DU HỌC ĐÀI LOAN 🇹🇼

Viện Khoa học Giáo dục Toàn Cầu (Viện SIGE) là đơn vị tiên phong xây dựng & hoàn thiện hệ sinh thái giáo dục toàn diện Việt Nam - Đài Loan. Chúng tôi tự hào là cầu nối chiến lược hỗ trợ học sinh, sinh viên tiếp cận các chương trình chất lượng với chi phí tối ưu nhất!

✨ SỨ MỆNH & TẦM NHÌN
💎 Hệ sinh thái khép kín: Đào tạo ngoại ngữ, thực tập doanh nghiệp và cam kết việc làm đầu ra.
💎 Hỗ trợ toàn diện: Thiết kế lộ trình học & học bổng tối ưu nhất cho từng học viên.
💎 Bảo trợ tại Đài Loan: Đơn vị DUY NHẤT có văn phòng đại diện tại Đài Bắc, Đào Viên và Cao Hùng để hỗ trợ bạn ngay khi nhập cảnh.

🎯 DỊCH VỤ MŨI NHỌN
✅ Hỗ trợ chọn trường & thiết kế học bổng riêng biệt.
✅ Xử lý thủ tục Visa, bảo hiểm và nhập cảnh nhanh chóng.
✅ Đăng ký thực tập hưởng lương ngay từ năm nhất.
✅ Bảo chứng 100% cơ hội việc làm sau khi tốt nghiệp.

Để được tư vấn chi tiết, bạn vui lòng để lại số điện thoại 📞 nhé!"""
    },

    "nudge_proactive_follow_up": {
        "text": "Bạn ơi, không biết thông tin trên đã giúp ích được cho mình chưa? ✨\n\nĐể tiết kiệm thời gian, cán bộ tuyển sinh SIGE có thể gọi điện giải đáp 1-1 cho bạn trong 15 phút tới không? Chỉ cần để lại SĐT thôi ạ! 🎯"
    },

    "case_5_dich_vu": {
        "text": "Chào bạn! SIGE không chỉ xử lý hồ sơ mà còn cam kết bảo chứng 100% cơ hội việc làm sau khi sang Đài Loan. 🎓✨\n\nVui lòng để lại Số điện thoại để kết nối với cán bộ tuyển sinh tư vấn ngay!"
    },

    "case_6_nghi_van": {
        "text": "Chào bạn! Quyền lợi \"học bổng\" hay \"bảo chứng việc làm\" tại SIGE là cam kết có thật từ mạng lưới doanh nghiệp hơn 20 năm qua. 🎓✨\n\nHãy để lại Số điện thoại để cán bộ tuyển sinh hỗ trợ bạn kiểm chứng thông tin trực tiếp nhé!"
    },

    "case_7_phu_huynh": {
        "text": "Tại phiên làm việc sắp tới, cán bộ tuyển sinh SIGE rất sẵn lòng mời cả phụ huynh cùng tham gia để phân tích rõ bài toán tài chính và hợp đồng. 👨‍👩‍👧\n\nVui lòng để lại Số điện thoại để thiết lập cuộc gọi cho cả gia đình nhé!"
    },

    "case_9_ngu_dong": {
        "text": "Hồ sơ của bạn đang bảo lưu. Lịch hẹn trống của cán bộ tuyển sinh tuần này chỉ còn 3 suất.\n\nVui lòng để lại Số điện thoại để thiết lập lịch ưu tiên ngay hôm nay!"
    },

    "case_10_o_xa": {
        "text": "Chào bạn! SIGE hỗ trợ tư vấn và nộp hồ sơ Online & Zoom trên toàn quốc. 🌍\n\nVui lòng để lại Số điện thoại để thiết lập cuộc gọi phân tích hồ sơ nhé!"
    },

    # ================== LOGIC PHÂN NHÁNH 2 (HOOKS) ==================
    "hook_14": {
        "text": "Hệ 1+4 (Hệ dự bị Đại học): Dành cho các bạn chưa có tiếng Trung. Học 1 năm tiếng, sau đó học tiếp 4 năm Đại học chính quy.\n\nĐể nhận tư vấn lộ trình này ngay bây giờ, bạn hãy để lại Số điện thoại nhé!"
    },

    "hook_vhvl": {
        "text": "Hệ Vừa Học Vừa Làm: Cơ hội rèn luyện và thực tập hưởng lương 18-25tr/tháng ngay từ năm nhất. Thích hợp cho bạn muốn tự chủ tài chính.\n\nĐể nhận tư vấn lộ trình này ngay bây giờ, bạn hãy để lại Số điện thoại nhé!"
    },

    # (Original scripted answers follow, but with our 3 main buttons if appropriate)
    "danh_sach_truong": {
        "text": """🏫 DANH SÁCH CÁC TRƯỜNG ĐẠI HỌC LIÊN KẾT CHIẾN LƯỢC

Dạ, SIGE tự hào là đối tác tuyển sinh trực tiếp của các trường Top đầu Đài Loan như: ĐH Quốc tế Minh Truyền (MCU), ĐH Quốc lập Ky Nam (NCNU), ĐH Công nghệ Trung Tín (CTBC), ĐH KHKT Lĩnh Đông (LTU)...

Tùy vào năng lực học tập và nguyện vọng, cán bộ tuyển sinh sẽ chọn trường phù hợp nhất.

📞 Nhắn cho SIGE xin [SỐ ĐIỆN THOẠI] của anh/chị, cán bộ tuyển sinh sẽ gọi điện định hướng trực tiếp để không chọn sai trường nhé!"""
    },

    "hoc_bong_14": {
        "text": """🎯 CHƯƠNG TRÌNH HỆ CHUYÊN BAN QUỐC TẾ 1+4 (DỰ BỊ ĐẠI HỌC)

Hệ Dự bị 1+4 đang là chương trình HOT nhất tại SIGE lúc này!

✅ Ưu điểm lớn nhất: Không yêu cầu chứng chỉ ngoại ngữ từ trước. Năm nhất được miễn 100% học phí.
✅ Cam kết: Có mạng lưới văn phòng hỗ trợ ngay khi nhập cảnh (Đài Bắc, Đào Viên, Cao Hùng).

⚠️ Lưu ý: Hệ 1+4 chốt hồ sơ rất sớm và yêu cầu điểm GPA mỗi học kỳ từ 7.0 trở lên.

📞 Anh/chị vui lòng để lại [SỐ ĐIỆN THOẠI], Trưởng phòng Tuyển sinh sẽ gọi check điểm hồ sơ và giữ suất ưu đãi 100% học phí cho mình ngay nhé!"""
    },

    "he_vhvl_detail": {
        "text": """💆 HỆ VỪA HỌC VỪA LÀM (VHVL) - CƠ HỘI TỰ CHỦ TÀI CHÍNH

Chương trình Vừa học Vừa làm cực kỳ phù hợp để tự chủ tài chính!

✅ Đi làm thêm có lương ngay trong quá trình học (Thu nhập thực tập hỗ trợ lên đến 22 - 28 triệu VNĐ/tháng).
✅ Hỗ trợ chuyển đổi từ visa sinh viên sang visa kỹ sư để ở lại làm việc dài hạn.

🎁 SIGE đang tặng 05 suất [Miễn phí lớp học tiếng/ Tặng vali] cho hồ sơ đăng ký tuần này.

📞 Chỉ còn đúng 3 suất nhận ưu đãi, anh/chị gõ [SỐ ĐIỆN THOẠI] để cán bộ tuyển sinh SIGE gọi điện tư vấn lộ trình và cách nhận lương thực tập sớm nhất nhé!"""
    },

    "he_thac_si_detail": {
        "text": "Chương trình Thạc sĩ: Dành cho Cử nhân Đại học. Học bổng 50-100% tuỳ hồ sơ, dễ dàng tìm việc làm quản lý và định cư lâu dài.\n\nĐể được tư vấn trực tiếp lộ trình này ngay bây giờ, bạn hãy để lại Số điện thoại nhé!"
    },

    "he_ngon_ngu_detail": {
        "text": "Hệ Ngôn ngữ: Dành cho người muốn học nhanh tiếng Trung tại bản xứ. Sau 6 tháng được làm thêm, chi phí đầu tư ban đầu thấp.\n\nĐể được tư vấn trực tiếp lộ trình này ngay bây giờ, bạn hãy để lại Số điện thoại nhé!"
    },

    "tai_chinh_goi_dich_vu": {
        "text": """💰 CÁC GÓI DỊCH VỤ DỊCH VỤ TƯ VẤN TRỌN GÓI TẠI SIGE

Viện SIGE cung cấp các gói dịch vụ minh bạch, cam kết không phát sinh ẩn phí trong quá trình xử lý:

1️⃣ Hỗ trợ toàn diện từ A-Z:
- Định hướng chọn trường, chọn ngành phù hợp.
- Hỗ trợ dịch thuật, công chứng, hợp thức hóa hồ sơ.
- Luyện phỏng vấn xin Visa chuyên sâu.

2️⃣ Bảo trợ sinh viên tại Đài Loan:
- Đón sân bay, hỗ trợ làm thẻ cư trú, thẻ lao động.
- Liên kết doanh nghiệp tài trợ học bổng và cam kết việc làm đầu ra.

3️⃣ Hỗ trợ định cư:
- Hỗ trợ chuyển đổi Visa sinh viên sang Visa kỹ sư.

📞 Hãy để lại số điện thoại để nhận bảng ước tính tổng tài chính cần chuẩn bị khi sang Đài Loan nhé!"""
    },

    "tai_chinh_tong_quan": {
        "text": """📊 VẤN ĐỀ TÀI CHÍNH KHI DU HỌC ĐÀI LOAN

Dạ, vấn đề tài chính phụ thuộc vào hồ sơ của mình có đạt học bổng hay không.

Chi phí đi qua SIGE là Trọn gói & Minh bạch 100%. Nếu học bạ đẹp, SIGE sẽ xin được suất miễn 100% học phí, lúc đó chi phí ban đầu cực kỳ thấp.

Để có bảng dự toán chính xác đến từng đồng (Không phát sinh), anh/chị vui lòng để lại [SỐ ĐIỆN THOẠI]. Cán bộ tuyển sinh sẽ gọi hỏi điểm cấp 3 và báo giá luôn ạ!"""
    },

    "ho_so_chuan_bi": {
        "text": """📂 DANH MỤC HỒ SƠ ĐÀI LOAN CẦN CHUẨN BỊ (Lưu ý có thể thay đổi hoặc bổ sung)

Để kịp làm hồ sơ du học, bạn cần chuẩn bị đầy đủ các giấy tờ sau:

1️⃣ Bằng TN THPT/ TN ĐH (1 bản gốc)
2️⃣ Học bạ THPT/ Bảng điểm ĐH (1 bản gốc, đầy đủ dấu giáp lai. Nếu mất học bạ gốc cần Bảng điểm C3 + xác nhận)
3️⃣ Ảnh thẻ (05 ảnh theo quy định của văn phòng Đài Bắc)
4️⃣ Căn cước công dân photo (01 bản)
5️⃣ Hộ chiếu (1 bản gốc)
6️⃣ Giấy khai sinh bản sao mẫu mới nhất (01 bản sao mẫu mới, không phải bản photo công chứng)
7️⃣ Chứng chỉ IELTS (1 bản gốc, đối với chương trình học bằng tiếng Anh)
8️⃣ Chứng chỉ TOCFL (1 bản gốc, đối với chương trình tiếng Trung)
9️⃣ Sổ tiết kiệm (1 bản gốc khi có thông báo làm visa, thường từ 120-200 triệu tùy hệ du học)
🔟 Giấy khám sức khỏe và phiếu tiêm (1 bản gốc theo Viện chỉ định khi có thông báo)

👉 Viện SIGE sẽ hỗ trợ bạn scan, dịch thuật, công chứng và nộp hồ sơ xin giấy phép từ các cơ quan ban ngành tại Đài Loan."""
    },

    "quy_trinh_chi_tiet": {
        "text": """🚀 QUY TRÌNH HỒ SƠ CHUẨN TẠI VIỆN SIGE (7 BƯỚC)

Bạn sẽ được cán bộ chuyên trách của Viện hỗ trợ từng bước một:

1. Nộp hồ sơ: Gửi hồ sơ về phòng tuyển sinh SIGE hoặc điền form trực tuyến.
2. Phỏng vấn: Tham gia phỏng vấn với trường và doanh nghiệp (nếu có).
3. Đặt cọc: Hoàn thành thủ tục đặt cọc và phí hành chính.
4. Nhận thông báo: Nhận giấy báo nhập học chính thức từ trường bên Đài Loan.
5. Xin Visa: SIGE hỗ trợ làm thủ tục xin visa tại Văn phòng Kinh tế và Văn hóa Đài Bắc.
6. Nhập học: Xuất cảnh và nhập học theo thông báo, được đón tại sân bay và hỗ trợ nơi ở.

👉 Toàn bộ quy trình thường kéo dài từ 3-4 tháng. Hãy bắt đầu ngay hôm nay!"""
    },

    "hoc_bong_chung": {
        "text": """💰 CHÍNH SÁCH HỌC BỔNG & HỖ TRỢ TÀI CHÍNH TẠI SIGE

SIGE cam kết giúp sinh viên tối ưu hóa chi phí thông qua quỹ học bổng doanh nghiệp và chính sách của nhà trường:

- Học bổng 100%: Dành cho sinh viên ưu tú hệ VHVL hoặc các trường như Đài Cương, John...
- Học bổng Chính phủ (Hệ 1+4): Miễn phí năm đầu tiên cho hầu hết sinh viên.
- Gói Hỗ trợ SIGE: Giảm phí dịch vụ cho SV có thành tích xuất sắc hoặc hoàn cảnh khó khăn.

⚠️ Lưu ý: Ngay khi sang Đài Loan, sinh viên vẫn nên chuẩn bị một khoản tiền nhỏ (~40M) để đóng các tạp phí ban đầu, sau đó nhà trường sẽ xét duyệt hồ sơ và hoàn lại tiền học bổng theo quy định.

📞 Hãy để lại số điện thoại để cán bộ tuyển sinh kiểm tra mức Học bổng bạn có thể đạt được dựa trên Điểm trung bình hiện tại nhé!"""
    },

    "co_hoi_viec_lam": {
        "text": """💼 THỰC TẬP & CƠ HỘI VIỆC LÀM TẠI ĐÀI LOAN (Kỳ 2026)

Du học Đài Loan không chỉ là học tập, mà còn là bước khởi đầu cho sự nghiệp quốc tế bền vững.

🔹 Trong quá trình học:
- Đi làm thêm 20h/tuần (thu nhập ~15-18 triệu VNĐ/tháng).
- Hệ VHVL thực tập tại doanh nghiệp đối tác lớn như ASE, Liteon với mức trợ cấp lên đến ~22-25 triệu VNĐ/tháng (28.590 TWD).

🔹 Sau khi tốt nghiệp:
- SIGE cam kết kết nối sinh viên làm việc cho các tập đoàn với mức lương kỹ sư chính thức từ 31.150 TWD/tháng trở lên.
- Hỗ trợ thủ tục chuyển đổi sang Visa lao động dài hạn hoặc định cư.

👉 Đài Loan đang rất thiếu nhân lực chất lượng cao trong các ngành Công nghệ, Dịch vụ và Y tế!"""
    },

    "du_hoc_dai_loan": {
        "text": """🇹🇼 HỆ SINH THÁI DU HỌC SIGE - TẦM NHÌN 20 NĂM

Chào mừng bạn đến với SIGE AI - hệ thống hỗ trợ du học chuyên sâu được vận hành bởi Viện Khoa học Giáo dục Toần Cầu.

✨ Tại sao bạn nên chọn SIGE?
- Đối tác Chiến lược: Liên kết trực tiếp với các trường đại học hàng đầu, đảm bảo tỷ lệ đỗ trường 99%.
- Bảo trợ Trọn đời: Chúng tôi có văn phòng tại Đài Loan để hỗ trợ bạn những lúc gặp khó khăn trong sinh hoạt, ốm đau hay chuyển công tác.
- Minh bạch: Phí dịch vụ rõ ràng, lộ trình đào tạo bài bản.

✨ Vibe từ Viện trưởng:
> "Với mạng lưới 20 năm tâm huyết tại Đài Loan của tôi, SIGE không chỉ đưa bạn đi học, mà là đưa bạn vào một hệ sinh thái bảo trợ trọn đời. Sự thành công của sinh viên là thước đo giá trị lớn nhất của Viện SIGE."
— ThS. Nguyễn Thị Điệp (Viện trưởng SIGE)

📍 Địa chỉ: Tầng 4, Tòa VINATA 2B, 289 Khuất Duy Tiến, TP. Hà Nội.
🌐 Website: www.sige.edu.vn
Để nhận tư vấn lộ trình 1-1 miễn phí, vui lòng để lại số điện thoại!"""
    }
}

# Mapping of common phrase patterns to keys
QUERY_MAPPING = {
    # 10 Psychological Triggers
    r"đặt lịch|hẹn|đăng ký lịch|tư vấn ngay|start_lead_form": "case_1_dat_lich",
    r"chi phí|giá|bao nhiêu tiền|tổng tiền|tài chính|học phí|sinh hoạt phí|gói dịch vụ|trọn gói": "case_2_chi_phi",
    r"ngành|học ngành|định hướng|chuyên ngành": "case_3_chon_nganh",
    r"dịch vụ|cung cấp gì|có gì|show_program_menu": "case_5_dich_vu",
    r"lừa đảo|thật không|có tốt không|làm gì mà|có chắc|sợ": "case_6_nghi_van",
    r"bố mẹ|phụ huynh|gia đình|hỏi ý kiến|bàn với nhà": "case_7_phu_huynh",
    r"ở xa|tỉnh lẻ|ngoại thành|không ở hà nội|ngoại tỉnh": "case_10_o_xa",
    r"like|thả tim|hello|hi|chào|bắt đầu|tư vấn|tu van|tue vấn|tư vẩn|menu|get_started": "case_4_like_tuong_tac",

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

def get_scripted_response(query: str) -> Optional[dict]:
    """
    Checks if the user query matches any scripted response keywords.
    Returns the dictionary (text) if found, otherwise None.
    """
    query_clean = query.lower().strip()
    
    # 1. Exact match check
    if query_clean in SCRIPTED_ANSWERS:
        return SCRIPTED_ANSWERS[query_clean]
        
    # 2. Pattern match check
    for pattern, key in QUERY_MAPPING.items():
        if re.search(pattern, query_clean):
            return SCRIPTED_ANSWERS[key]
            
    return None
