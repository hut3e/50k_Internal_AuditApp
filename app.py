import os
import streamlit as st
import json
from datetime import datetime
import report
# Thử tải từ dotenv nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Nếu không có dotenv, bỏ qua

# Import từ các module khác
from question_manager import manage_questions
from surveyhandler import survey_form
from stats_dashboard import stats_dashboard
from admin_dashboard import admin_dashboard
from database_helper import get_supabase_client, check_supabase_config
from PIL import Image, UnidentifiedImageError

# ------------ Cấu hình logo 2×3 cm ~ 76×113 px ------------
LOGO_WIDTH, LOGO_HEIGHT = 150, 150
SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "gif")

# Đường dẫn thư mục chứa logo
LOGO_DIR = "assets/logos"  # Thư mục chứa logo

# Tạo thư mục logo nếu chưa tồn tại
def ensure_logo_directory():
    """Đảm bảo thư mục logo tồn tại"""
    if not os.path.exists(LOGO_DIR):
        try:
            os.makedirs(LOGO_DIR, exist_ok=True)
            print(f"Đã tạo thư mục {LOGO_DIR}")
        except Exception as e:
            st.error(f"Không thể tạo thư mục logo: {e}")
            print(f"Lỗi: {e}")

# Lưu logo được tải lên
def save_uploaded_logo(logo_file, index):
    """Lưu logo đã tải lên vào thư mục"""
    ensure_logo_directory()
    try:
        file_extension = logo_file.name.split('.')[-1].lower()
        if file_extension not in SUPPORTED_FORMATS:
            return False, f"Định dạng không được hỗ trợ: {file_extension}"
        
        file_path = os.path.join(LOGO_DIR, f"logo{index}.{file_extension}")
        with open(file_path, "wb") as f:
            f.write(logo_file.getbuffer())
        return True, file_path
    except Exception as e:
        return False, str(e)

# Tìm tất cả logo đã lưu
def find_saved_logos():
    """Tìm các logo đã lưu trong thư mục"""
    ensure_logo_directory()
    logo_paths = []
    
    # Tìm kiếm file logo1.*, logo2.*, logo3.*
    for i in range(1, 4):
        for ext in SUPPORTED_FORMATS:
            pattern = f"logo{i}.{ext}"
            path = os.path.join(LOGO_DIR, pattern)
            if os.path.exists(path):
                logo_paths.append(path)
                break
    
    return logo_paths

def display_logos():
    """Cho phép tải lên 03 logo và hiển thị chúng cố định trên giao diện."""
    # Tạo container cho logo ở đầu trang
    logo_container = st.container()
    with logo_container:
        col1, col2, col3 = st.columns(3)
        
        # Tìm kiếm logo đã lưu
        saved_logos = find_saved_logos()
        
        # Hiển thị các logo đã lưu
        for i, logo_path in enumerate(saved_logos):
            try:
                if i == 0:
                    with col1:
                        st.image(logo_path, width=LOGO_WIDTH)
                elif i == 1:
                    with col2:
                        st.image(logo_path, width=LOGO_WIDTH)
                elif i == 2:
                    with col3:
                        st.image(logo_path, width=LOGO_WIDTH)
            except Exception as e:
                st.error(f"Lỗi khi hiển thị logo {logo_path}: {e}")
        
        # Hiển thị tiêu đề ứng dụng ở giữa
        st.title("TRAINING INTERNAL AUDIT ISO 50001 TEST APP")
    
    # Phần tải lên logo mới - ẩn trong expander để không chiếm nhiều không gian
    with st.expander("Cấu hình logo"):
        st.write("Tải lên 03 logo để hiển thị trên ứng dụng. Logo sẽ được lưu lại cho các lần sử dụng sau.")
        
        col1, col2, col3 = st.columns(3)
        
        # Tạo file uploader cho 3 logo
        with col1:
            logo1 = st.file_uploader("Logo 1", type=SUPPORTED_FORMATS, key="file1")
            if logo1:
                success, msg = save_uploaded_logo(logo1, 1)
                if success:
                    st.success("Đã lưu Logo 1")
                else:
                    st.error(f"Lỗi khi lưu Logo 1: {msg}")
        
        with col2:
            logo2 = st.file_uploader("Logo 2", type=SUPPORTED_FORMATS, key="file2")
            if logo2:
                success, msg = save_uploaded_logo(logo2, 2)
                if success:
                    st.success("Đã lưu Logo 2")
                else:
                    st.error(f"Lỗi khi lưu Logo 2: {msg}")
        
        with col3:
            logo3 = st.file_uploader("Logo 3", type=SUPPORTED_FORMATS, key="file3")
            if logo3:
                success, msg = save_uploaded_logo(logo3, 3)
                if success:
                    st.success("Đã lưu Logo 3")
                else:
                    st.error(f"Lỗi khi lưu Logo 3: {msg}")
        
        # Nếu có logo mới được tải lên, tải lại trang để hiển thị
        if logo1 or logo2 or logo3:
            if st.button("Cập nhật hiển thị logo"):
                st.rerun()

def main():
    st.set_page_config(
        page_title="Hệ thống kiểm tra học viên sau Đào tạo Đánh giá viên nội bộ ISO 50001:2018",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Hiển thị logo trước khi bất kỳ nội dung nào khác
    display_logos()
    
    # Kiểm tra cấu hình Supabase
    is_valid, message = check_supabase_config()
    
    # Nếu chưa thiết lập biến môi trường
    if not is_valid:
        st.error(message)
        setup_environment_variables()
        return  # Dừng ứng dụng cho đến khi thiết lập biến môi trường
    
    # Thiết lập Supabase client
    supabase = get_supabase_client()
    if not supabase:
        st.error("Không thể kết nối đến Supabase. Vui lòng kiểm tra lại cấu hình.")
        setup_environment_variables()
        return
    
    # Sidebar - Menu điều hướng
    with st.sidebar:
        st.title("📝 Hệ thống kiểm tra học viên sau Đào tạo Đánh giá viên nội bộ ISO 50001:2018")
        st.success("Đã kết nối thành công đến Supabase!")
        
        # Hiển thị thông tin dự án (ẩn key)
        with st.expander("Thông tin kết nối"):
            st.write(f"**URL:** {os.environ.get('SUPABASE_URL')}")
            api_key = os.environ.get('SUPABASE_KEY', '')
            masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "Chưa thiết lập"
            st.write(f"**API Key:** {masked_key}")
        
        # Kiểm tra đăng nhập
        if "user_role" not in st.session_state:
            st.session_state.user_role = None
            
        if "user_info" not in st.session_state:
            st.session_state.user_info = None
        
        # Nếu chưa đăng nhập
        if not st.session_state.user_role:
            with st.form("login_form"):
                st.subheader("Đăng nhập")
                email = st.text_input("Email", placeholder="Nhập email của bạn")
                password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
                
                # Thêm combobox cho loại người dùng (chỉ cho mục đích demo)
                user_type = st.selectbox("Loại tài khoản", ["Học viên", "Quản trị viên"])
                
                submit_button = st.form_submit_button("Đăng nhập")
                
                if submit_button:
                    # Trong ứng dụng thực tế sẽ có xác thực đúng mật khẩu
                    # Đây chỉ là demo đơn giản
                    if email and password:
                        if user_type == "Quản trị viên":
                            st.session_state.user_role = "admin"
                            st.session_state.user_info = {
                                "email": email,
                                "full_name": "Admin",
                                "class_name": "N/A"
                            }
                        else:
                            st.session_state.user_role = "student"
                            st.session_state.user_info = {
                                "email": email,
                                "full_name": "Học viên " + email.split("@")[0],
                                "class_name": "Lớp đào tạo đánh giá viên nội bộ ISO 50001:2018"
                            }
                        
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Vui lòng nhập email và mật khẩu!")
        
        # Đã đăng nhập - Hiển thị menu tương ứng
        else:
            st.write(f"Chào mừng, **{st.session_state.user_info['full_name']}**!")
            
            # Menu cho quản trị viên
            if st.session_state.user_role == "admin":
                page = st.radio(
                    "Chọn chức năng:",
                    ["Quản lý câu hỏi", "Báo cáo & thống kê", "Quản trị hệ thống"]
                )
                        
            # Menu cho học viên
            else:
                page = st.radio(
                    "Chọn chức năng:",
                    ["Làm bài khảo sát"]
                )
            
            # Nút đăng xuất
            if st.button("Đăng xuất"):
                st.session_state.user_role = None
                st.session_state.user_info = None
                st.rerun()
    
    # Hiển thị nội dung tương ứng
    if "user_role" in st.session_state and st.session_state.user_role:
        if st.session_state.user_role == "admin":
            if page == "Quản lý câu hỏi":
                manage_questions()
            elif page == "Báo cáo & thống kê":
                stats_dashboard()
            elif page == "Quản trị hệ thống":
                report.view_statistics()
        else:
            if page == "Làm bài khảo sát":
                survey_form(
                    st.session_state.user_info["email"], 
                    st.session_state.user_info["full_name"], 
                    st.session_state.user_info["class_name"]
                )
    else:
        # Màn hình chào mừng
        st.header("Chào mừng các Bạn học viên !")
        
        st.markdown("""
        ### Tính năng chính:
        
        **Dành cho học viên:**
        - Làm bài khảo sát với nhiều loại câu hỏi trắc nghiệm và tự luận
        - Xem lịch sử làm bài và kết quả
        - Theo dõi tiến độ cải thiện
        
        **Dành cho quản trị viên:**
        - Quản lý câu hỏi: Thêm, sửa, xóa câu hỏi
        - Báo cáo & thống kê: Phân tích kết quả, xem báo cáo chi tiết
        - Quản trị hệ thống: Quản lý học viên, xuất dữ liệu
        
        Vui lòng đăng nhập ở thanh bên trái để sử dụng hệ thống.
        """)
        
        # Hiển thị một số thông tin demo
        with st.expander("Thông tin App kiểm tra sau Đào tạo Đánh giá viên nội bộ ISO 50001:2018"):
            st.write("""
            **Đây là phiên bản App Ver 1.0 do Team ISO 50001 TUV phát triển**
            
            Để đăng nhập với tư cách học viên, hãy chọn "Học viên" trong form đăng nhập.
            
            Để đăng nhập với tư cách quản trị viên, hãy chọn "Quản trị viên" trong form đăng nhập.
            
            Chú ý: Đây chỉ là bản dành cho kiểm tra học viên, không yêu cầu mật khẩu thực.
            """)

def setup_environment_variables():
    """Form thiết lập biến môi trường"""
    st.header("Thiết lập kết nối Supabase")
    
    # Tabs cho các phương pháp thiết lập khác nhau
    tab1, tab2 = st.tabs(["Thiết lập trực tiếp", "Hướng dẫn"])
    
    with tab1:
        st.subheader("Thiết lập biến môi trường")
        st.warning("Chú ý: Phương pháp này chỉ lưu biến môi trường trong phiên hiện tại. Khi khởi động lại ứng dụng, bạn sẽ cần thiết lập lại.")
        
        with st.form("env_setup_form"):
            current_url = os.environ.get("SUPABASE_URL", "")
            current_key = os.environ.get("SUPABASE_KEY", "")
            
            supabase_url = st.text_input("URL (Project URL)", value=current_url, placeholder="https://your-project-id.supabase.co")
            supabase_key = st.text_input("API Key (anon/public)", value=current_key, type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            
            st.info("Bạn có thể tìm thấy URL và API Key trong dashboard của Supabase: Cài đặt > API")
            
            submit = st.form_submit_button("Lưu cấu hình")
            
            if submit:
                if not supabase_url or not supabase_key:
                    st.error("Vui lòng nhập đầy đủ URL và API Key.")
                elif not supabase_url.startswith("https://"):
                    st.error("URL không hợp lệ. URL phải bắt đầu bằng https://")
                else:
                    os.environ["SUPABASE_URL"] = supabase_url
                    os.environ["SUPABASE_KEY"] = supabase_key
                    st.success("Đã thiết lập biến môi trường thành công!")
                    st.button("Tiếp tục", on_click=lambda: st.rerun())
    
    with tab2:
        st.subheader("Hướng dẫn thiết lập App")
        
        st.markdown("""
        ### Thiết lập theo sự hướng dẫn của Admin App ISO 50001:2018        
        
        """)
        
        st.info("Sau khi thiết lập biến môi trường bằng một trong các phương pháp trên, hãy khởi động lại ứng dụng.")

if __name__ == "__main__":
    main()
