# Hệ thống Khảo sát Nhiều Đáp Án

Ứng dụng Streamlit để tạo và quản lý hệ thống khảo sát với khả năng hỗ trợ nhiều đáp án đúng. Hệ thống sử dụng Supabase làm cơ sở dữ liệu.

## Tính năng

- **Dành cho học viên**:
  - Làm bài khảo sát với nhiều loại câu hỏi
  - Xem lịch sử làm bài và kết quả
  - Theo dõi tiến độ cải thiện qua các lần làm

- **Dành cho quản trị viên**:
  - Quản lý câu hỏi: Thêm, sửa, xóa câu hỏi
  - Báo cáo & thống kê: Phân tích kết quả, biểu đồ trực quan
  - Quản trị hệ thống: Quản lý học viên, xuất dữ liệu

## Cài đặt

### Yêu cầu

- Python 3.7 trở lên
- [Tài khoản Supabase](https://supabase.com/)

### Thiết lập dự án

1. Clone repository:
```bash
git clone https://github.com/yourusername/survey-system.git
cd survey-system
```

2. Cài đặt thư viện cần thiết:
```bash
pip install -r requirements.txt
```

3. Thiết lập Supabase:
   - Tạo tài khoản và dự án mới trên [Supabase](https://supabase.com/)
   - Tạo bảng cần thiết bằng cách sử dụng tệp SQL trong thư mục `sql/` hoặc chạy các lệnh SQL được cung cấp trong file `create_tables.sql`.

4. Thiết lập biến môi trường:
   - Tạo tệp `.env` trong thư mục gốc của dự án
   - Sao chép nội dung từ `.env.example` và cập nhật thông tin kết nối Supabase của bạn

### Khởi chạy ứng dụng

```bash
streamlit run app.py
```

## Cấu trúc dự án

```
survey-system/
│
├── app.py                  # File chính của ứng dụng
├── database_helper.py      # Kết nối và thao tác với Supabase
├── question_manager.py     # Quản lý câu hỏi
├── survey_handler.py       # Xử lý bài khảo sát
├── stats_dashboard.py      # Thống kê và báo cáo
├── admin_dashboard.py      # Quản trị hệ thống
│
├── sql/                    # Các file SQL để thiết lập cơ sở dữ liệu
│   └── create_tables.sql   # Tạo bảng questions và submissions
│
├── .env.example            # Mẫu cấu hình biến môi trường
├── .gitignore              # Các file/thư mục được loại trừ khỏi Git
├── requirements.txt        # Danh sách thư viện cần thiết
└── README.md               # File này
```

## Cấu trúc cơ sở dữ liệu

### Bảng `questions`
- `id`: ID câu hỏi (primary key)
- `question`: Nội dung câu hỏi
- `type`: Loại câu hỏi (Checkbox/Combobox)
- `answers`: Danh sách đáp án (dạng JSON)
- `correct`: Danh sách vị trí đáp án đúng (dạng JSON)
- `score`: Điểm số cho câu hỏi
- `created_at`: Thời gian tạo

### Bảng `submissions`
- `id`: ID bài nộp (primary key)
- `email`: Email của học viên
- `responses`: Các câu trả lời (dạng JSON)
- `score`: Điểm số đạt được
- `timestamp`: Thời gian nộp bài
- `created_at`: Thời gian tạo bản ghi

## An toàn và bảo mật

- Phải đặt file `.env` vào `.gitignore` để tránh đưa thông tin nhạy cảm lên git
- Không sử dụng API key với quyền `service_role` trong ứng dụng
- Thiết lập Row Level Security (RLS) trong Supabase để bảo vệ dữ liệu

## Đóng góp

Vui lòng đọc [CONTRIBUTING.md](CONTRIBUTING.md) để biết chi tiết về quy trình đóng góp.

## Giấy phép

Dự án này được cấp phép theo Giấy phép MIT - xem file [LICENSE](LICENSE) để biết chi tiết.


Hướng dẫn thiết lập môi trường cục bộ khi làm việc nhóm
Khi làm việc nhóm trên dự án này, việc thiết lập môi trường cục bộ đồng nhất giữa các thành viên là rất quan trọng. Dưới đây là hướng dẫn chi tiết để đảm bảo mọi người đều có thể làm việc hiệu quả:
1. Thống nhất phiên bản và công cụ
1.1. Phiên bản Python
Phiên bản khuyến nghị: Python 3.9 hoặc 3.10

Kiểm tra phiên bản: python --version
Đề xuất sử dụng công cụ quản lý phiên bản Python như pyenv để dễ dàng chuyển đổi giữa các phiên bản.

1.2. Bộ quản lý gói
Sử dụng pip cho quản lý gói Python

Đảm bảo pip được cập nhật: python -m pip install --upgrade pip

1.3. Công cụ quản lý mã nguồn
Sử dụng Git và GitHub

Thống nhất quy trình làm việc với Git (gitflow hoặc GitHub flow)
Sử dụng nhánh riêng cho từng tính năng

2. Thiết lập dự án lần đầu
2.1. Clone repository
bashgit clone https://github.com/ten-nhom/ten-du-an.git
cd ten-du-an
2.2. Tạo môi trường ảo
bash# Sử dụng venv (built-in với Python)
python -m venv venv

# Kích hoạt môi trường ảo
# Trên Windows:
venv\Scripts\activate
# Trên macOS/Linux:
source venv/bin/activate
2.3. Cài đặt thư viện
bashpip install -r requirements.txt
2.4. Thống nhất về cấu hình IDE
Khuyến nghị sử dụng Visual Studio Code

Chia sẻ file .vscode/settings.json trong repo để đồng bộ cài đặt
Cài đặt các extension khuyến nghị: Python, Pylance, Streamlit

3. Thiết lập biến môi trường
3.1. Tạo file .env cục bộ
bash# Sao chép file mẫu
cp .env.example .env
3.2. Quyết định về việc chia sẻ dự án Supabase
Phương án 1: Dùng chung một dự án Supabase

Ưu điểm: Dữ liệu đồng nhất giữa các thành viên
Nhược điểm: Có thể gây xung đột khi nhiều người làm việc cùng lúc

# Ai đó trong nhóm tạo dự án trên Supabase và chia sẻ thông tin qua kênh an toàn
SUPABASE_URL=https://shared-project-id.supabase.co
SUPABASE_KEY=shared-anon-key
Phương án 2: Mỗi thành viên dùng dự án Supabase riêng

Ưu điểm: Độc lập khi phát triển, không lo xung đột
Nhược điểm: Cần đồng bộ cấu trúc database giữa các thành viên

# Mỗi thành viên tự tạo dự án và cấu hình riêng
SUPABASE_URL=https://your-own-project-id.supabase.co
SUPABASE_KEY=your-own-anon-key
3.3. Cách chia sẻ biến môi trường an toàn
TUYỆT ĐỐI KHÔNG commit file .env lên Git
Các phương pháp chia sẻ an toàn:

Sử dụng công cụ quản lý bí mật (như 1Password, LastPass, Bitwarden)
Sử dụng kênh liên lạc an toàn có mã hóa đầu cuối (Signal, WhatsApp)
Chia sẻ qua cuộc họp trực tiếp

4. Thiết lập cơ sở dữ liệu
4.1. Tạo các bảng cần thiết
Đảm bảo mọi thành viên đều có cấu trúc database giống nhau:
sql-- Tạo các bảng theo script SQL đã cung cấp
-- Đảm bảo cập nhật file create_tables.sql khi có thay đổi cấu trúc
4.2. Dữ liệu mẫu cho phát triển
Tạo script để thêm dữ liệu mẫu cho phát triển:
sql-- Lưu dưới dạng seed_data.sql trong thư mục sql/
-- Mỗi thành viên chạy để có dữ liệu giống nhau

-- Ví dụ thêm câu hỏi mẫu
INSERT INTO public.questions (question, type, answers, correct, score)
VALUES 
('Câu hỏi mẫu 1?', 'Checkbox', '["Đáp án 1", "Đáp án 2", "Đáp án 3"]', '[1, 2]', 2),
('Câu hỏi mẫu 2?', 'Combobox', '["Có", "Không", "Có thể"]', '[1]', 1);
5. Quy trình phát triển
5.1. Quy trình làm việc hàng ngày
bash# 1. Cập nhật code mới nhất từ repo chính
git checkout main
git pull origin main

# 2. Tạo nhánh mới cho tính năng
git checkout -b feature/ten-tinh-nang

# 3. Kích hoạt môi trường ảo
source venv/bin/activate  # hoặc venv\Scripts\activate trên Windows

# 4. Làm việc trên code

# 5. Chạy ứng dụng để kiểm tra
streamlit run app.py

# 6. Commit và push thay đổi
git add .
git commit -m "Mô tả thay đổi"
git push origin feature/ten-tinh-nang

# 7. Tạo Pull Request trên GitHub
5.2. Quản lý xung đột

Liên hệ với nhau khi làm việc trên cùng một file
Commit và merge thường xuyên để giảm thiểu xung đột
Sử dụng công cụ trực quan để giải quyết xung đột (như VSCode)

6. Kiểm tra chất lượng code
6.1. Style Guide

Tuân theo PEP 8 cho Python
Sử dụng docstring để mô tả hàm và lớp
Thống nhất quy ước đặt tên (camelCase cho biến, PascalCase cho lớp, v.v.)

6.2. Code Review

Mỗi Pull Request cần ít nhất 1 người review
Sử dụng comment trên GitHub để thảo luận về code
Không merge code khi còn vấn đề nghiêm trọng

7. Xử lý vấn đề với Supabase
7.1. Khi thay đổi cấu trúc database
1. Thống nhất thay đổi trong nhóm
2. Cập nhật file create_tables.sql
3. Thông báo cho mọi người về thay đổi
4. Mỗi thành viên tự cập nhật cơ sở dữ liệu của mình
7.2. Xử lý lỗi kết nối
1. Kiểm tra URL và API Key trong file .env
2. Đảm bảo dự án Supabase đang hoạt động
3. Kiểm tra cấu trúc bảng khớp với code
4. Xóa cache:
   - streamlit cache clear
   - Khởi động lại ứng dụng
8. Tài liệu và giao tiếp
8.1. Cập nhật tài liệu

Cập nhật README.md khi thêm tính năng mới
Thêm comment vào code phức tạp
Duy trì CHANGELOG.md để theo dõi thay đổi

8.2. Giao tiếp trong nhóm

Sử dụng Issues trên GitHub để theo dõi nhiệm vụ
Thống nhất kênh chat cho giao tiếp nhanh (Slack, Discord, etc.)
Tổ chức họp định kỳ để cập nhật tiến độ

9. Triển khai
9.1. Môi trường phát triển vs sản xuất
Tách biệt các biến môi trường:
- .env.development
- .env.production
9.2. Quy trình triển khai
1. Merge code vào nhánh main
2. Kiểm thử tích hợp
3. Triển khai lên môi trường UAT/Staging
4. Kiểm tra cuối cùng
5. Triển khai lên môi trường sản xuất
10. Danh sách kiểm tra cho thành viên mới
[ ] Cài đặt Python phiên bản đúng
[ ] Clone repository
[ ] Tạo và kích hoạt môi trường ảo
[ ] Cài đặt dependencies
[ ] Tạo file .env và cấu hình
[ ] Tạo dự án Supabase
[ ] Chạy script tạo bảng
[ ] Thêm dữ liệu mẫu
[ ] Kiểm tra ứng dụng chạy bình thường
[ ] Đọc tài liệu dự án
Bằng cách tuân theo hướng dẫn này, nhóm của bạn sẽ có môi trường phát triển đồng nhất và tránh được nhiều vấn đề thường gặp khi làm việc nhóm trên dự án phần mềm.