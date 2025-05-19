import os
import json
import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

# Thử tải từ dotenv nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Nếu không có dotenv, bỏ qua

# Hướng dẫn cài đặt và khởi động dự án

## Chuẩn bị

1. **Yêu cầu hệ thống**:
   - Python 3.7 trở lên
   - Tài khoản Supabase (https://supabase.com)

## Các bước cài đặt

1. **Sao chép dự án**:
```bash
git clone https://github.com/yourusername/survey-system.git
cd survey-system
```

2. **Cài đặt thư viện**:
```bash
pip install -r requirements.txt
```

3. **Thiết lập Supabase**:
   - Đăng nhập vào Supabase và tạo dự án mới
   - Sao chép URL và anon/public key từ Project Settings > API
   - Tạo các bảng cần thiết bằng SQL Editor (sử dụng file `create_tables.sql`)

4. **Cấu hình biến môi trường**:
   - Tạo file `.env` trong thư mục gốc dự án
   - Sao chép nội dung từ `.env.example`
   - Cập nhật Supabase URL và API Key

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

5. **Khởi động ứng dụng**:
```bash
streamlit run app.py
```

## Sử dụng ứng dụng

1. **Đăng nhập**:
   - Sử dụng form đăng nhập trong ứng dụng
   - Chọn loại tài khoản (Học viên/Quản trị viên)

2. **Quản trị viên**:
   - Quản lý câu hỏi: Thêm, sửa, xóa câu hỏi
   - Báo cáo & thống kê: Xem phân tích dữ liệu
   - Quản trị hệ thống: Quản lý học viên và xuất dữ liệu

3. **Học viên**:
   - Làm bài khảo sát
   - Xem kết quả và lịch sử làm bài

## Cấu trúc thư mục

- `app.py`: File chính của ứng dụng
- `database_helper.py`: Kết nối và thao tác với Supabase
- `question_manager.py`: Quản lý câu hỏi
- `survey_handler.py`: Xử lý bài khảo sát
- `stats_dashboard.py`: Thống kê và báo cáo
- `admin_dashboard.py`: Quản trị hệ thống
- `sql/`: Thư mục chứa file SQL
- `.env.example`: Mẫu cấu hình biến môi trường

## Xử lý lỗi thường gặp

1. **Lỗi kết nối Supabase**:
   - Kiểm tra URL và API Key trong file `.env`
   - Đảm bảo mạng internet hoạt động bình thường
   - Kiểm tra Supabase dashboard để xác nhận dịch vụ đang hoạt động

2. **Lỗi import module**:
   - Đảm bảo đã cài đặt đầy đủ thư viện:
     ```bash
     pip install -r requirements.txt
     ```

3. **Streamlit không hiển thị đúng**:
   - Thử xóa cache:
     ```bash
     streamlit cache clear
     ```
   - Khởi động lại ứng dụng