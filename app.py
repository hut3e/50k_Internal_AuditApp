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
from database_helper import get_supabase_client, check_supabase_config, create_user_if_not_exists, get_user
from PIL import Image, UnidentifiedImageError

# ------------ Cấu hình logo 2×3 cm ~ 76×113 px ------------
LOGO_WIDTH, LOGO_HEIGHT = 150, 150
SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "gif")

# Đường dẫn thư mục chứa logo
LOGO_DIR = "assets/logos"  # Thư mục chứa logo

def initialize_session_state():
    """Khởi tạo tất cả session state variables cần thiết"""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'page_selection' not in st.session_state:
        st.session_state.page_selection = None
    
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

def ensure_logo_directory():
    """Đảm bảo thư mục logo tồn tại"""
    if not os.path.exists(LOGO_DIR):
        try:
            os.makedirs(LOGO_DIR, exist_ok=True)
            print(f"Đã tạo thư mục {LOGO_DIR}")
        except Exception as e:
            st.error(f"Không thể tạo thư mục logo: {e}")
            print(f"Lỗi: {e}")

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
        st.title("ISO 50001:2018 TRAINING APP")
    
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

def create_default_admin():
    """Tạo tài khoản admin mặc định"""
    try:
        return create_user_if_not_exists(
            email="admin@tuvnord.com",
            full_name="Administrator",
            class_name="Admin",
            role="admin",
            password="admintuv123"
        )
    except Exception as e:
        st.error(f"Lỗi khi tạo admin: {e}")
        return False

def handle_login():
    """Xử lý form đăng nhập - ĐÃ SỬA"""
    with st.form("login_form"):
        st.subheader("Đăng nhập")
        
        # Input fields
        email = st.text_input("Email", placeholder="Nhập email của bạn")
        password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
        
        # QUAN TRỌNG: Selectbox vai trò đăng nhập
        user_role = st.selectbox(
            "Chọn vai trò đăng nhập:",
            options=["student", "admin"],
            format_func=lambda x: "👨‍🎓 Học viên" if x == "student" else "👨‍💼 Quản trị viên",
            help="Chọn vai trò phù hợp với tài khoản của bạn"
        )
        
        # Submit button
        submit_button = st.form_submit_button("🔐 Đăng nhập", use_container_width=True)
        
        if submit_button:
            if email and password:
                # Debug info
                st.write(f"**Debug:** Đang thử đăng nhập với Email: {email}, Role: {user_role}")
                
                # Thử đăng nhập với database
                user = get_user(email, password, user_role)
                
                if user:
                    # Lưu thông tin vào session state
                    st.session_state.user_role = user["role"]
                    st.session_state.user_info = {
                        "email": user["email"],
                        "full_name": user["full_name"],
                        "class_name": user["class"]
                    }
                    st.session_state.authenticated = True
                    
                    # Hiển thị thông báo đăng nhập
                    if user.get("first_login", False):
                        st.success("🎉 Chào mừng bạn đăng nhập lần đầu tiên!")
                        st.info("Hãy khám phá các tính năng của hệ thống.")
                    else:
                        st.success("✅ Đăng nhập thành công!")
                    
                    # Debug: Hiển thị thông tin đã lưu
                    #st.write(f"**Debug:** Đã lưu user_role = {st.session_state.user_role}")
                    #st.write(f"**Debug:** Authenticated = {st.session_state.authenticated}")
                    
                    # Delay để user đọc thông báo
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Email, mật khẩu hoặc vai trò không đúng!")
                    
                    # Debug info
                    #with st.expander("🔍 Thông tin debug"):
                        #st.write(f"**Email nhập:** {email}")
                        #st.write(f"**Role yêu cầu:** {user_role}")
                        
                        # Kiểm tra users trong database
                    supabase = get_supabase_client()
                    if supabase:
                        try:
                            all_users = supabase.table('users').select('email, role, first_login').execute()
                            if all_users.data:
                                st.write("**Danh sách users trong database:**")
                                for u in all_users.data:
                                    first_login_status = "✨ Lần đầu" if u.get('first_login', False) else "🔄 Đã từng đăng nhập"
                                    st.write(f"- {u['email']} ({u['role']}) - {first_login_status}")
                            else:
                                st.write("**Không có user nào trong database**")
                        except Exception as e:
                            st.write(f"Lỗi khi lấy danh sách users: {e}")
            else:
                st.error("⚠️ Vui lòng nhập đầy đủ email và mật khẩu!")
    
    # Section tạo admin mặc định
    with st.expander("🔧 Tạo tài khoản admin mặc định"):
        st.write("Nếu bạn chưa có tài khoản admin, hãy tạo tài khoản admin mặc định:")
        
        if st.button("➕ Tạo Admin mặc định", use_container_width=True):
            success = create_default_admin()
            if success:
                st.success("✅ Đã tạo tài khoản admin mặc định!")
                st.info("""
                **📋 Thông tin đăng nhập admin:**
                - **Email:** admin@tuvnord.com
                - **Mật khẩu:** mã hóa HAS256
                - **Vai trò:** Quản trị viên
                - **Trạng thái:** Lần đăng nhập đầu tiên
                """)
            else:
                st.warning("⚠️ Admin đã tồn tại hoặc có lỗi khi tạo!")
    
    # Nút đăng ký
    st.divider()
    if st.button("📝 Chưa có tài khoản? Đăng ký ngay", use_container_width=True):
        st.session_state.show_register = True
        st.rerun()

def handle_register():
    """Xử lý form đăng ký học viên"""
    st.subheader("📝 Đăng ký tài khoản học viên lớp đào tạo ISO 50001")
    
    with st.form("register_form"):
        st.write("Vui lòng điền thông tin để đăng ký tài khoản học viên:")
        
        email = st.text_input("Email", placeholder="Nhập email của bạn")
        full_name = st.text_input("Họ và tên", placeholder="Nhập họ và tên đầy đủ")
        class_name = st.text_input("Lớp", placeholder="Nhập lớp của bạn")
        password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu (tối thiểu 6 ký tự)")
        confirm_password = st.text_input("Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu")
        
        register_button = st.form_submit_button("📝 Đăng ký tài khoản", use_container_width=True)
        
        if register_button:
            # Validate form
            if not email or not full_name or not class_name or not password:
                st.error("⚠️ Vui lòng điền đầy đủ thông tin!")
                return
            
            if password != confirm_password:
                st.error("❌ Mật khẩu không khớp!")
                return
            
            if "@" not in email:
                st.error("❌ Email không hợp lệ!")
                return
            
            if len(password) < 6:
                st.error("❌ Mật khẩu phải có ít nhất 6 ký tự!")
                return
            
            # Tạo tài khoản mới
            success = create_user_if_not_exists(email, full_name, class_name, "student", password)
            
            if success:
                st.success("✅ Đăng ký thành công! Bây giờ bạn có thể đăng nhập.")
                st.info(f"""
                **📋 Thông tin đăng nhập của bạn:**
                - **Email:** {email}
                - **Mật khẩu:** .......
                - **Vai trò:** Học viên
                - **Trạng thái:** Tài khoản mới (lần đăng nhập đầu tiên)
                """)
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error("❌ Đăng ký thất bại. Email có thể đã được sử dụng hoặc có lỗi hệ thống.")
    
    # Nút quay lại đăng nhập
    if st.button("⬅️ Quay lại đăng nhập", use_container_width=True):
        st.session_state.show_register = False
        st.rerun()

def display_user_menu():
    """Hiển thị menu cho người dùng đã đăng nhập - ĐÃ SỬA"""
    # Kiểm tra an toàn session state
    if not st.session_state.get('user_info'):
        st.error("❌ Thông tin người dùng không hợp lệ. Vui lòng đăng nhập lại.")
        return None
    
    user_info = st.session_state.user_info
    user_role = st.session_state.get('user_role')
    
    # Hiển thị thông tin người dùng
    st.write(f"👋 Chào mừng, **{user_info.get('full_name', 'Unknown User')}**!")
    st.write(f"📧 **Email:** {user_info.get('email', '')}")
    st.write(f"🎯 **Vai trò:** {'👨‍💼 Quản trị viên' if user_role == 'admin' else '👨‍🎓 Học viên'}")
    
    st.divider()
    
    # Menu cho quản trị viên
    if user_role == "admin":
        st.write("### 👨‍💼 Menu Quản trị viên")
        page = st.radio(
            "Chọn chức năng:",
            [
                "Quản lý câu hỏi", 
                "Báo cáo & thống kê", 
                "Quản trị hệ thống", 
                "Chấm điểm tự luận"
            ],
            key="admin_menu",
            format_func=lambda x: {
                "Quản lý câu hỏi": "📝 Quản lý câu hỏi",
                "Báo cáo & thống kê": "📊 Báo cáo & thống kê", 
                "Quản trị hệ thống": "⚙️ Quản trị hệ thống",
                "Chấm điểm tự luận": "✍️ Chấm điểm tự luận"
            }[x]
        )
    # Menu cho học viên
    else:
        st.write("### 👨‍🎓 Menu Học viên")
        page = st.radio(
            "Chọn chức năng:",
            ["Làm bài khảo sát"],
            key="student_menu",
            format_func=lambda x: "📋 Làm bài khảo sát"
        )
    
    st.divider()
    
    # Nút đăng xuất
    if st.button("🚪 Đăng xuất", use_container_width=True, type="secondary"):
        # Reset tất cả session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        initialize_session_state()
        st.success("👋 Đã đăng xuất thành công!")
        st.rerun()
    
    return page

def display_main_content(page):
    """Hiển thị nội dung chính dựa trên trang được chọn - ĐÃ SỬA"""
    try:
        user_role = st.session_state.get('user_role')
        user_info = st.session_state.get('user_info', {})
        
        # Debug info
        #st.write(f"**Debug Main Content:** user_role = {user_role}, page = {page}")
        
        if user_role == "admin":
            st.write("### 👨‍💼 Chế độ Quản trị viên")
            
            if page == "Quản lý câu hỏi":
                manage_questions()
            elif page == "Báo cáo & thống kê":
                stats_dashboard()
            elif page == "Quản trị hệ thống":
                report.view_statistics()
            elif page == "Chấm điểm tự luận":
                essay_grading_interface()
            else:
                st.error(f"❌ Chức năng '{page}' chưa được implement!")
                
        elif user_role == "student":
            st.write("### 👨‍🎓 Chế độ Học viên")
            
            if page == "Làm bài khảo sát":
                survey_form(
                    user_info.get("email", ""), 
                    user_info.get("full_name", ""), 
                    user_info.get("class_name", "")
                )
            else:
                st.error(f"❌ Chức năng '{page}' không khả dụng cho học viên!")
        else:
            st.error("❌ Vai trò người dùng không hợp lệ!")
            
    except Exception as e:
        st.error(f"❌ Lỗi khi hiển thị nội dung: {str(e)}")
        st.write("Vui lòng thử lại hoặc liên hệ với quản trị viên.")
        
        # Hiển thị debug info
        if st.checkbox("🔍 Hiển thị thông tin debug"):
            st.exception(e)

def recalculate_submission_score(submission_id):
    """Tính lại điểm cho một bài nộp cụ thể - ĐÃ SỬA LỖI KIỂU DỮ LIỆU"""
    try:
        from database_helper import get_supabase_client, get_all_questions, calculate_total_score
        
        print(f"🔄 Tính lại điểm cho submission {submission_id}")
        
        supabase = get_supabase_client()
        if not supabase:
            return False
            
        # Lấy thông tin bài nộp
        result = supabase.table("submissions").select("*").eq("id", submission_id).execute()
        if not result.data:
            print("❌ Không tìm thấy submission")
            return False
            
        submission = result.data[0]
        questions = get_all_questions()
        
        print(f"📊 Điểm cũ: {submission.get('score', 0)}")
        
        # ✅ TÍNH LẠI TỔNG ĐIỂM BẰNG HÀM calculate_total_score
        new_total_score = calculate_total_score(submission, questions)
        
        print(f"🎯 Điểm mới: {new_total_score} (type: {type(new_total_score)})")
        
        # 🔧 SỬA: Đảm bảo là INTEGER trước khi lưu database
        if not isinstance(new_total_score, int):
            new_total_score = int(round(float(new_total_score)))
            print(f"🔧 Converted to integer: {new_total_score}")
        
        # Cập nhật điểm mới
        update_result = supabase.table("submissions").update({
            "score": new_total_score  # ✅ ĐẢM BẢO LÀ INTEGER
        }).eq("id", submission_id).execute()
        
        if update_result.data:
            print(f"✅ Cập nhật thành công!")
            return True
        else:
            print("❌ Lỗi cập nhật")
            return False
        
    except Exception as e:
        print(f"❌ Lỗi khi tính lại điểm: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def essay_grading_interface():
    """Interface chấm điểm tự luận cho admin - ĐÃ SỬA VÀ CẢI THIỆN"""
    from database_helper import get_supabase_client, get_all_questions, update_submission
    import json
    
    st.title("✍️ Chấm điểm câu hỏi tự luận")
    
    # ✅ THÊM SECTION DEBUG
    #with st.expander("🔍 Debug & Kiểm tra hệ thống"):
        #if st.button("🧪 Test hệ thống tính điểm"):
            #from database_helper import debug_scoring_system
            #debug_scoring_system()
            #st.success("Đã chạy test! Kiểm tra console/logs.")

    # Lấy danh sách câu hỏi tự luận
    questions = get_all_questions()
    essay_questions = [q for q in questions if q.get("type") == "Essay"]
    
    if not essay_questions:
        st.info("ℹ️ Không có câu hỏi tự luận nào trong hệ thống.")
        return
    
    # Lấy tất cả bài nộp có câu hỏi tự luận
    supabase = get_supabase_client()
    if not supabase:
        st.error("❌ Không thể kết nối đến Supabase.")
        return
    
    try:
        # Lấy tất cả bài nộp
        submissions_result = supabase.table("submissions").select("*").order("timestamp", desc=True).execute()
        submissions = submissions_result.data if submissions_result.data else []
        
        # Lọc các bài nộp có câu hỏi tự luận
        essay_submissions = []
        for submission in submissions:
            responses = submission.get("responses", {})
            if isinstance(responses, str):
                try:
                    responses = json.loads(responses)
                except:
                    responses = {}
            
            # Kiểm tra xem có câu hỏi tự luận nào được trả lời không
            has_essay = False
            for eq in essay_questions:
                eq_id = str(eq["id"])
                if eq_id in responses and responses[eq_id]:
                    has_essay = True
                    break
            
            if has_essay:
                essay_submissions.append(submission)
        
        if not essay_submissions:
            st.info("ℹ️ Không có bài nộp nào có câu hỏi tự luận.")
            return
        
        st.write(f"📊 **Tìm thấy {len(essay_submissions)} bài nộp có câu hỏi tự luận**")
        
        # Tạo filter theo trạng thái chấm điểm
        status_filter = st.selectbox(
            "🔍 Lọc theo trạng thái:",
            ["Tất cả", "Chưa chấm", "Đã chấm"],
            help="Chọn trạng thái để lọc danh sách bài nộp"
        )
        
        # Nút tính lại tất cả điểm
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Tính lại tất cả điểm", type="secondary", use_container_width=True):
                progress_bar = st.progress(0)
                success_count = 0
                # Hiển thị log debug
                debug_container = st.empty()

                for i, submission in enumerate(essay_submissions):
                    debug_container.write(f"🔄 Đang xử lý submission #{submission['id']}")
                    if recalculate_submission_score(submission['id']):
                        success_count += 1
                        debug_container.write(f"✅ Thành công: #{submission['id']}")
                    else:
                        debug_container.write(f"❌ Lỗi: #{submission['id']}")

                    progress_bar.progress((i + 1) / len(essay_submissions))
                
                if success_count == len(essay_submissions):
                    st.success(f"✅ Đã tính lại điểm thành công cho {success_count} bài nộp!")
                else:
                    st.warning(f"⚠️ Tính lại thành công {success_count}/{len(essay_submissions)} bài nộp!")
                st.rerun()
        
        with col2:
            st.info(f"📋 **Thống kê:** {len(essay_submissions)} bài nộp cần xem xét")
        
        st.divider()
        
        # Hiển thị danh sách bài nộp
        for submission in essay_submissions:
            # Lấy essay_grades
            essay_grades = submission.get("essay_grades", {})
            if isinstance(essay_grades, str):
                try:
                    essay_grades = json.loads(essay_grades)
                except:
                    essay_grades = {}
            
            # Kiểm tra trạng thái chấm điểm
            is_graded = any(str(eq["id"]) in essay_grades for eq in essay_questions)
            
            # Áp dụng filter
            if status_filter == "Chưa chấm" and is_graded:
                continue
            elif status_filter == "Đã chấm" and not is_graded:
                continue
            
            # Hiển thị thông tin bài nộp
            status_icon = "✅" if is_graded else "⏳"
            status_text = "Đã chấm" if is_graded else "Chưa chấm"
            
            with st.expander(f"{status_icon} Bài nộp #{submission['id']} - {submission['user_email']} - {status_text}"):
                # Hiển thị thông tin chung
                timestamp = submission.get("timestamp", "")
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        formatted_time = dt.strftime("%H:%M:%S %d/%m/%Y")
                    except:
                        formatted_time = timestamp
                else:
                    try:
                        formatted_time = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S %d/%m/%Y")
                    except:
                        formatted_time = "Không xác định"
                        
                score_percent = (submission.get('score', 0) / sum(q.get('score', 0) for q in questions) * 100) if questions else 0
                
                # Thông tin tổng quan
                info_col1, info_col2, info_col3 = st.columns(3)
                info_col1.metric("⏰ Thời gian nộp", formatted_time)
                info_col2.metric("🎯 Điểm hiện tại", f"{submission.get('score', 0)}")
                info_col3.metric("📊 Tỷ lệ", f"{score_percent:.1f}%")
                
                st.divider()
                
                # Lấy responses
                responses = submission.get("responses", {})
                if isinstance(responses, str):
                    try:
                        responses = json.loads(responses)
                    except:
                        responses = {}
                
                # Lấy essay_comments
                essay_comments = submission.get("essay_comments", {})
                if isinstance(essay_comments, str):
                    try:
                        essay_comments = json.loads(essay_comments)
                    except:
                        essay_comments = {}
                
                # Hiển thị từng câu hỏi tự luận
                updated_grades = essay_grades.copy()
                updated_comments = essay_comments.copy()
                has_changes = False
                
                for eq in essay_questions:
                    eq_id = str(eq["id"])
                    
                    if eq_id in responses and responses[eq_id]:
                        st.write(f"**📝 Câu {eq['id']}: {eq['question']}** *(Điểm tối đa: {eq['score']})*")
                        
                        # Hiển thị câu trả lời của học viên
                        student_answer = responses[eq_id][0] if responses[eq_id] else ""
                        st.text_area(
                            "📖 Câu trả lời của học viên:",
                            value=student_answer,
                            height=150,
                            disabled=True,
                            key=f"answer_{submission['id']}_{eq_id}"
                        )
                        
                        # Form chấm điểm
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            current_score = updated_grades.get(eq_id, 0)
                            new_score = st.number_input(
                                f"🎯 Điểm (0-{eq['score']}):",
                                min_value=0,
                                max_value=eq['score'],
                                value=current_score,
                                key=f"score_{submission['id']}_{eq_id}"
                            )
                            
                            if new_score != current_score:
                                updated_grades[eq_id] = new_score
                                has_changes = True
                        
                        with col2:
                            current_comment = updated_comments.get(eq_id, "")
                            new_comment = st.text_area(
                                "💭 Nhận xét:",
                                value=current_comment,
                                height=100,
                                key=f"comment_{submission['id']}_{eq_id}",
                                help="Nhận xét sẽ được hiển thị cho học viên"
                            )
                            
                            if new_comment != current_comment:
                                updated_comments[eq_id] = new_comment
                                has_changes = True
                        
                        st.divider()
                
                # Nút lưu và tính lại điểm
                button_col1, button_col2, button_col3 = st.columns(3)
                
                with button_col1:
                    if st.button(f"💾 Lưu điểm", key=f"save_{submission['id']}", 
                                use_container_width=True, type="primary"):
                        # Cập nhật essay_grades và essay_comments
                        update_data = {
                            "essay_grades": json.dumps(updated_grades),
                            "essay_comments": json.dumps(updated_comments)
                        }
                        
                        success = update_submission(submission['id'], update_data)
                        
                        if success:
                            st.success("✅ Đã lưu điểm và nhận xét!")
                            # Tự động tính lại tổng điểm
                            if recalculate_submission_score(submission['id']):
                                st.success("🔄 Đã tự động cập nhật tổng điểm!")
                            st.rerun()
                        else:
                            st.error("❌ Lỗi khi lưu điểm!")
                
                with button_col2:
                    if st.button(f"🔄 Tính lại tổng điểm", key=f"recalc_{submission['id']}", 
                                use_container_width=True, type="secondary"):
                        if recalculate_submission_score(submission['id']):
                            st.success("✅ Đã tính lại tổng điểm thành công!")
                            st.rerun()
                        else:
                            st.error("❌ Lỗi khi tính lại điểm!")
                
                with button_col3:
                    # Hiển thị trạng thái
                    if is_graded:
                        st.success("✅ Đã chấm điểm")
                    else:
                        st.warning("⏳ Chưa chấm điểm")
    
    except Exception as e:
        st.error(f"❌ Lỗi khi tải dữ liệu: {str(e)}")
        st.exception(e)

def display_welcome_screen():
    """Hiển thị màn hình chào mừng"""
    st.header("🎯 Chào mừng Học viên Tổng Công ty Giấy tham gia khóa Đào tạo nhận thức ISO 50001:2018!")
    
    st.markdown("""
    ### 🚀 Tính năng chính:
    
    **👨‍🎓 Dành cho học viên:**
    - 📝 Đăng ký tài khoản và đăng nhập với lựa chọn vai trò
    - 📋 Làm bài khảo sát với nhiều loại câu hỏi trắc nghiệm và tự luận
    - 📊 Xem lịch sử làm bài và kết quả chi tiết
    - 📈 Theo dõi tiến độ cải thiện qua thời gian
    
    **👨‍💼 Dành cho quản trị viên:**
    - 📝 Quản lý câu hỏi: Thêm, sửa, xóa câu hỏi (trắc nghiệm & tự luận)
    - ✍️ Chấm điểm tự luận cho học viên với nhận xét chi tiết
    - 📊 Báo cáo & thống kê: Phân tích kết quả, xem báo cáo chi tiết
    - ⚙️ Quản trị hệ thống: Quản lý học viên, xuất dữ liệu
    
    👈 **Vui lòng đăng nhập hoặc đăng ký tài khoản ở thanh bên trái để sử dụng hệ thống.**
    """)
    
    # Hiển thị một số thông tin demo
    with st.expander("ℹ️ Thông tin App kiểm tra sau Đào tạo ISO 50001:2018"):
        st.write("""
        **🎯 Đây là phiên bản App Ver 2.0 của Team ISO 50001**
        
        **📊 Cấu trúc Database:**
        - email (PRIMARY KEY)
        - password  
        - role (student/admin)
        - first_login (TRUE/FALSE)
        - full_name
        - class
        - registration_date
        
               
        **📋 Hướng dẫn sử dụng:**
        1. **Học viên:** Đăng ký tài khoản → Đăng nhập (chọn vai trò "👨‍🎓 Học viên") → Làm bài khảo sát
        2. **Admin:** Đăng nhập với tài khoản admin (chọn vai trò "👨‍💼 Quản trị viên") → Quản lý hệ thống
        
        **🔐 Tài khoản admin mặc định:**
        - **Email:** admin@test.com
        - **Mật khẩu:** Mã hóa HAS256
        - **Vai trò:** 👨‍💼 Quản trị viên
        - **First Login:** TRUE (sẽ chuyển thành FALSE sau lần đăng nhập đầu tiên)
        """)
    
    # Thêm debug section
    #with st.expander("🔧 Debug & Troubleshooting"):
        #debug_database()

def setup_sidebar():
    """Thiết lập sidebar với menu điều hướng"""
    with st.sidebar:
        st.title("🎯 Hệ thống kiểm tra sau Đào tạo ISO 50001:2018")
        
        # Kiểm tra cấu hình Supabase
        is_valid, message = check_supabase_config()
        
        if is_valid:
            st.success("✅ Đã kết nối thành công đến Supabase!")
            
            # Hiển thị thông tin để ẩn (ẩn key)
            with st.expander("ℹ️ Thông tin kết nối"):
                st.write(f"**URL:** {os.environ.get('SUPABASE_URL')}")
                api_key = os.environ.get('SUPABASE_KEY', '')
                masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "Chưa thiết lập"
                st.write(f"**API Key:** {masked_key}")
        else:
            st.error(f"❌ {message}")
        
        # Xử lý authentication
        if not st.session_state.get('authenticated', False):
            if st.session_state.get('show_register', False):
                handle_register()
            else:
                handle_login()
            return None
        else:
            return display_user_menu()

def setup_environment_variables():
    """Form thiết lập biến môi trường"""
    st.header("⚙️ Thiết lập kết nối Supabase")
    
    # Tabs cho các phương pháp thiết lập khác nhau
    tab1, tab2 = st.tabs(["Thiết lập trực tiếp", "Hướng dẫn"])
    
    with tab1:
        st.subheader("🔧 Thiết lập biến môi trường")
        st.warning("⚠️ Chú ý: Phương pháp này chỉ lưu biến môi trường trong phiên hiện tại. Khi khởi động lại ứng dụng, bạn sẽ cần thiết lập lại.")
        
        with st.form("env_setup_form"):
            current_url = os.environ.get("SUPABASE_URL", "")
            current_key = os.environ.get("SUPABASE_KEY", "")
            
            supabase_url = st.text_input("URL (Project URL)", value=current_url, placeholder="https://your-project-id.supabase.co")
            supabase_key = st.text_input("API Key (anon/public)", value=current_key, type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            
            st.info("ℹ️ Bạn có thể tìm thấy URL và API Key trong dashboard của Supabase: Cài đặt > API")
            
            submit = st.form_submit_button("💾 Lưu cấu hình")
            
            if submit:
                if not supabase_url or not supabase_key:
                    st.error("❌ Vui lòng nhập đầy đủ URL và API Key.")
                elif not supabase_url.startswith("https://"):
                    st.error("❌ URL không hợp lệ. URL phải bắt đầu bằng https://")
                else:
                    os.environ["SUPABASE_URL"] = supabase_url
                    os.environ["SUPABASE_KEY"] = supabase_key
                    st.success("✅ Đã thiết lập biến môi trường thành công!")
                    st.button("➡️ Tiếp tục", on_click=lambda: st.rerun())
    
    with tab2:
        st.subheader("📚 Hướng dẫn thiết lập App")
        
        st.markdown("""
        ### 🔧 Thiết lập theo sự hướng dẫn của Admin quản trị App Khóa đào tạo ISO 50001:2018         
        
        """)
        
        st.info("ℹ️ Sau khi thiết lập biến môi trường bằng một trong các phương pháp trên, hãy khởi động lại ứng dụng.")

def main():
    """Hàm main chính của ứng dụng"""
    # Cấu hình trang
    st.set_page_config(
        page_title="Hệ thống kiểm tra học viên sau Đào tạo tiêu chuẩn ISO 50001:2018",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Khởi tạo session state
    initialize_session_state()
    
    # Hiển thị logo trước khi bất kỳ nội dung nào khác
    display_logos()
    
    try:
        # Kiểm tra cấu hình Supabase
        is_valid, message = check_supabase_config()
        
        # Nếu chưa thiết lập biến môi trường
        if not is_valid:
            st.error(f"❌ {message}")
            setup_environment_variables()
            return  # Dừng ứng dụng cho đến khi thiết lập biến môi trường
        
        # Thiết lập Supabase client
        supabase = get_supabase_client()
        if not supabase:
            st.error("❌ Không thể kết nối đến Supabase. Vui lòng kiểm tra lại cấu hình.")
            setup_environment_variables()
            return
        
        # Thiết lập sidebar và lấy page selection
        page = setup_sidebar()
        
        # Debug info về session state
        #with st.expander("🔍 Debug Session State"):
            #st.write(f"**Authenticated:** {st.session_state.get('authenticated', False)}")
            #st.write(f"**User Role:** {st.session_state.get('user_role', 'None')}")
            #st.write(f"**User Info:** {st.session_state.get('user_info', 'None')}")
            #st.write(f"**Selected Page:** {page}")
        
        # Hiển thị nội dung chính
        if st.session_state.get('authenticated', False) and page:
            display_main_content(page)
        elif not st.session_state.get('authenticated', False):
            display_welcome_screen()
            
    except Exception as e:
        st.error(f"❌ Lỗi không mong muốn: {str(e)}")
        st.write("Vui lòng tải lại trang hoặc liên hệ với quản trị viên.")
        
        # Hiển thị thông tin debug nếu cần
        #if st.checkbox("🔍 Hiển thị thông tin debug chi tiết"):
            #st.exception(e)

if __name__ == "__main__":
    main()
