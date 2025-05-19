import streamlit as st
import json
from datetime import datetime
import pandas as pd

# Import từ các module khác
from database_helper import get_all_questions, get_user_submissions, get_submission_statistics

def admin_dashboard():
    """Bảng điều khiển quản trị viên"""
    st.title("Bảng điều khiển quản trị")
    
    # Lấy dữ liệu thống kê
    stats = get_submission_statistics()
    
    if not stats:
        st.error("Không thể lấy dữ liệu thống kê. Vui lòng thử lại sau.")
        return
    
    # Hiển thị các chỉ số quan trọng
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng số câu hỏi", len(get_all_questions()))
    col2.metric("Tổng số bài nộp", stats["total_submissions"])
    col3.metric("Số học viên", stats["student_count"])
    col4.metric("Điểm trung bình", f"{stats['avg_score']:.1f}/{stats['total_possible_score']}")
    
    # Các tab chức năng
    tab1, tab2, tab3 = st.tabs(["Tổng quan hệ thống", "Danh sách học viên", "Xuất dữ liệu"])
    
    with tab1:
        system_overview()
    
    with tab2:
        students_list()
    
    with tab3:
        export_data()

def system_overview():
    """Hiển thị tổng quan về hệ thống khảo sát"""
    st.subheader("Tổng quan hệ thống")
    
    # Lấy dữ liệu
    questions = get_all_questions()
    stats = get_submission_statistics()
    
    if not questions or not stats:
        st.warning("Không thể lấy đầy đủ dữ liệu hệ thống.")
        return
    
    # Phân tích cấu trúc câu hỏi
    checkbox_count = sum(1 for q in questions if q.get("type") == "Checkbox")
    combobox_count = sum(1 for q in questions if q.get("type") == "Combobox")
    
    # Hiển thị phân bố loại câu hỏi
    st.write("### Phân bố loại câu hỏi")
    
    # Tạo dữ liệu cho biểu đồ
    question_type_data = pd.DataFrame({
        'Loại câu hỏi': ['Checkbox (Nhiều lựa chọn)', 'Combobox (Một lựa chọn)'],
        'Số lượng': [checkbox_count, combobox_count]
    })
    
    # Hiển thị dạng bảng
    st.dataframe(question_type_data, use_container_width=True)
    
    # Hiển thị thống kê điểm số
    st.write("### Thống kê điểm số")
    
    total_score = sum(q.get("score", 0) for q in questions)
    avg_question_score = total_score / len(questions) if questions else 0
    max_question_score = max(q.get("score", 0) for q in questions) if questions else 0
    min_question_score = min(q.get("score", 0) for q in questions) if questions else 0
    
    score_cols = st.columns(4)
    score_cols[0].metric("Tổng điểm bài khảo sát", total_score)
    score_cols[1].metric("Điểm trung bình/câu hỏi", f"{avg_question_score:.1f}")
    score_cols[2].metric("Điểm cao nhất/câu hỏi", max_question_score)
    score_cols[3].metric("Điểm thấp nhất/câu hỏi", min_question_score)
    
    # Thống kê thời gian làm bài
    st.write("### Thống kê thời gian")
    
    if stats["total_submissions"] > 0:
        daily_counts = stats["daily_counts"]
        dates = sorted(daily_counts.keys())
        
        if dates:
            first_submission = dates[0]
            last_submission = dates[-1]
            active_days = len(dates)
            
            time_cols = st.columns(3)
            time_cols[0].metric("Ngày bắt đầu có bài nộp", first_submission)
            time_cols[1].metric("Ngày mới nhất có bài nộp", last_submission)
            time_cols[2].metric("Số ngày có bài nộp", active_days)
            
            # Mức độ hoạt động
            avg_submissions_per_day = stats["total_submissions"] / active_days
            st.metric("Số bài nộp trung bình mỗi ngày", f"{avg_submissions_per_day:.1f}")
    else:
        st.info("Chưa có dữ liệu bài nộp để thống kê thời gian.")
    
    # Hiển thị hoạt động gần đây
    st.write("### Hoạt động gần đây")
    st.info("Đây là phần tóm tắt hoạt động gần đây, có thể kết nối với cơ sở dữ liệu để hiển thị dữ liệu thời gian thực.")

def students_list():
    """Hiển thị danh sách học viên đã làm bài"""
    st.subheader("Danh sách học viên")
    
    # Lấy dữ liệu từ Supabase
    # Đây là hàm giả định - trong triển khai thực tế cần lấy dữ liệu từ table submissions
    stats = get_submission_statistics()
    
    if not stats or stats["total_submissions"] == 0:
        st.info("Chưa có học viên nào làm bài.")
        return
    
    # Hiển thị form tìm kiếm
    with st.form("admin_student_search"):
        search_email = st.text_input("Tìm kiếm theo email:")
        search_button = st.form_submit_button("Tìm kiếm")
    
    if search_button and search_email:
        # Tìm kiếm học viên cụ thể
        student_submissions = get_user_submissions(search_email)
        
        if student_submissions:
            st.success(f"Đã tìm thấy {len(student_submissions)} bài làm của học viên {search_email}")
            
            # Lấy danh sách câu hỏi để tính điểm tối đa
            questions = get_all_questions()
            max_score = sum([q["score"] for q in questions])
            
            # Hiển thị thông tin tổng quan
            st.write("### Thông tin tổng quan")
            
            # Tính điểm cao nhất
            max_student_score = max([s["score"] for s in student_submissions])
            max_percentage = (max_student_score / max_score) * 100 if max_score > 0 else 0
            
            col1, col2 = st.columns(2)
            col1.metric("Số lần làm bài", len(student_submissions))
            col2.metric("Điểm cao nhất", f"{max_student_score}/{max_score} ({max_percentage:.1f}%)")
            
            # Hiển thị chi tiết từng lần làm
            st.write("### Chi tiết các lần làm")
            
            for idx, s in enumerate(student_submissions):
                if isinstance(s["timestamp"], (int, float)):
                    # Trường hợp timestamp là số (dữ liệu cũ)
                    try:
                        submission_time = datetime.fromtimestamp(s["timestamp"]).strftime("%H:%M:%S %d/%m/%Y")
                    except:
                        submission_time = "Không xác định"
                else:
                    # Trường hợp timestamp là chuỗi ISO (dữ liệu mới)
                    try:
                        # Chuyển từ chuỗi ISO sang đối tượng datetime
                        dt = datetime.fromisoformat(s["timestamp"].replace("Z", "+00:00"))
                        submission_time = dt.strftime("%H:%M:%S %d/%m/%Y")
                    except Exception as e:
                        # Trong trường hợp không thể parse được timestamp
                        submission_time = "Không xác định"
                        print(f"Lỗi parse timestamp: {e}, giá trị: {s['timestamp']}")
                        
                score_percent = (s["score"] / max_score) * 100
                
                with st.expander(f"Lần {idx + 1}: {submission_time} - Điểm: {s['score']}/{max_score} ({score_percent:.1f}%)"):
                    # Hiển thị ID bài nộp
                    st.write(f"**ID bài nộp:** {s['id']}")
                    
                    # Hiển thị thời gian làm bài
                    st.write(f"**Thời gian nộp bài:** {submission_time}")
                    
                    # Hiển thị chi tiết câu trả lời
                    st.write("**Chi tiết câu trả lời:**")
                    
                    for q in questions:
                        q_id = str(q["id"])
                        
                        # Đảm bảo định dạng dữ liệu đúng
                        if isinstance(q["answers"], str):
                            try:
                                q["answers"] = json.loads(q["answers"])
                            except:
                                q["answers"] = [q["answers"]]
                        
                        if isinstance(q["correct"], str):
                            try:
                                q["correct"] = json.loads(q["correct"])
                            except:
                                try:
                                    q["correct"] = [int(x.strip()) for x in q["correct"].split(",")]
                                except:
                                    q["correct"] = []
                        
                        # Lấy câu trả lời của học viên
                        student_answers = s["responses"].get(q_id, [])
                        
                        # Kiểm tra đáp án
                        is_correct = check_answer_correctness(student_answers, q)
                        
                        # Hiển thị thông tin câu hỏi
                        st.write(f"**Câu {q['id']}:** {q['question']}")
                        
                        # Hiển thị câu trả lời của học viên
                        st.write("Đáp án đã chọn:")
                        if not student_answers:
                            st.write("- Không trả lời")
                        else:
                            for ans in student_answers:
                                st.write(f"- {ans}")
                        
                        # Hiển thị kết quả
                        if is_correct:
                            st.success(f"✅ Đúng (+{q['score']} điểm)")
                        else:
                            st.error("❌ Sai (0 điểm)")
                            expected_indices = q["correct"]
                            expected_answers = [q["answers"][i - 1] for i in expected_indices]
                            st.write("Đáp án đúng:")
                            for ans in expected_answers:
                                st.write(f"- {ans}")
                        
                        st.divider()
        else:
            st.error(f"Không tìm thấy học viên với email: {search_email}")
    else:
        st.info("Nhập email học viên và nhấn Tìm kiếm để xem chi tiết.")
        
        # Hiển thị số liệu tổng quan về học viên
        st.write(f"**Tổng số học viên đã làm bài:** {stats['student_count']}")
        st.write(f"**Tổng số bài nộp:** {stats['total_submissions']}")
        st.write(f"**Trung bình số lần làm bài/học viên:** {stats['total_submissions'] / stats['student_count']:.1f}")

def export_data():
    """Xuất dữ liệu báo cáo"""
    st.subheader("Xuất dữ liệu")
    
    # Chọn loại dữ liệu cần xuất
    export_type = st.selectbox(
        "Chọn loại dữ liệu cần xuất:",
        ["Danh sách câu hỏi", "Dữ liệu bài nộp", "Thống kê tổng hợp"]
    )
    
    if export_type == "Danh sách câu hỏi":
        export_questions()
    elif export_type == "Dữ liệu bài nộp":
        export_submissions()
    else:
        export_statistics()

def export_questions():
    """Xuất danh sách câu hỏi ra CSV"""
    questions = get_all_questions()
    
    if not questions:
        st.info("Chưa có câu hỏi nào trong hệ thống.")
        return
    
    # Chuẩn bị dữ liệu
    data = []
    for q in questions:
        # Đảm bảo định dạng dữ liệu đúng
        if isinstance(q["answers"], str):
            try:
                answers = json.loads(q["answers"])
            except:
                answers = [q["answers"]]
        else:
            answers = q["answers"]
        
        if isinstance(q["correct"], str):
            try:
                correct = json.loads(q["correct"])
            except:
                try:
                    correct = [int(x.strip()) for x in q["correct"].split(",")]
                except:
                    correct = []
        else:
            correct = q["correct"]
        
        # Chuyển đáp án và đáp án đúng thành chuỗi dễ đọc
        answers_str = ", ".join(answers)
        correct_answers = [answers[i-1] for i in correct if 0 < i <= len(answers)]
        correct_str = ", ".join(correct_answers)
        
        data.append({
            "ID": q["id"],
            "Câu hỏi": q["question"],
            "Loại": q["type"],
            "Điểm": q["score"],
            "Các đáp án": answers_str,
            "Đáp án đúng": correct_str
        })
    
    # Tạo DataFrame
    df = pd.DataFrame(data)
    
    # Hiển thị preview
    st.write("### Xem trước dữ liệu")
    st.dataframe(df)
    
    # Tạo nút tải xuống
    csv = df.to_csv(index=False)
    file_name = f"danh_sach_cau_hoi_{datetime.now().strftime('%Y%m%d')}.csv"
    
    st.download_button(
        label="Tải xuống CSV",
        data=csv,
        file_name=file_name,
        mime="text/csv",
    )

def export_submissions():
    """Xuất dữ liệu bài nộp ra CSV"""
    # Lấy dữ liệu bài nộp
    # Đây là hàm giả định, cần truy vấn từ database
    stats = get_submission_statistics()
    
    if not stats or stats["total_submissions"] == 0:
        st.info("Chưa có bài nộp nào trong hệ thống.")
        return
    
    st.info("Tính năng xuất dữ liệu bài nộp đang được phát triển.")
    st.info("Trong triển khai thực tế, tính năng này sẽ cho phép xuất toàn bộ dữ liệu bài nộp ra file CSV.")

def export_statistics():
    """Xuất dữ liệu thống kê tổng hợp"""
    stats = get_submission_statistics()
    
    if not stats:
        st.info("Chưa có dữ liệu thống kê.")
        return
    
    st.info("Tính năng xuất thống kê tổng hợp đang được phát triển.")
    st.info("Trong triển khai thực tế, tính năng này sẽ cho phép xuất báo cáo tổng hợp bao gồm các biểu đồ và phân tích.")

def check_answer_correctness(student_answers, question):
    """Kiểm tra đáp án có đúng không, hỗ trợ chọn nhiều đáp án."""
    # Nếu câu trả lời trống, không đúng
    if not student_answers:
        return False
        
    # Đối với câu hỏi combobox (chỉ chọn một)
    if question["type"] == "Combobox":
        # Nếu có một đáp án và đáp án đó ở vị trí nằm trong danh sách đáp án đúng
        if len(student_answers) == 1:
            answer_text = student_answers[0]
            answer_index = question["answers"].index(answer_text) + 1 if answer_text in question["answers"] else -1
            return answer_index in question["correct"]
        return False
    
    # Đối với câu hỏi checkbox (nhiều lựa chọn)
    elif question["type"] == "Checkbox":
        # Tìm index (vị trí) của các đáp án học viên đã chọn
        selected_indices = []
        for ans in student_answers:
            if ans in question["answers"]:
                selected_indices.append(question["answers"].index(ans) + 1)
        
        # So sánh với danh sách đáp án đúng
        return set(selected_indices) == set(question["correct"])
    
    return False