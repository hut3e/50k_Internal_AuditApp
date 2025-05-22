import streamlit as st
import json
from datetime import datetime
import pandas as pd
import report  # Thêm import này

# Import từ các module khác
from database_helper import get_all_questions, get_user_submissions, get_submission_statistics, check_answer_correctness
# Thêm các import từ report.py
from report import get_download_link_docx, get_download_link_pdf, create_student_report_docx, create_student_report_pdf_fpdf
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

def display_student_tab(submissions=None, students=None, questions=None, max_possible=0):
    """Hiển thị tab theo học viên"""
    if submissions is None:
        submissions = []
    if students is None:
        students = []
    if questions is None:
        questions = []
        
    st.subheader("Chi tiết theo học viên")
    
    # Tạo DataFrame từ dữ liệu
    user_data = []
    for s in submissions:
        try:
            # Tìm thông tin học viên
            student_info = next((student for student in students if student.get("email") == s.get("user_email")), None)
            full_name = student_info.get("full_name", "Không xác định") if student_info else "Không xác định"
            class_name = student_info.get("class", "Không xác định") if student_info else "Không xác định"
            
            # Xử lý timestamp
            submission_time = "Không xác định"
            try:
                if isinstance(s.get("timestamp"), (int, float)):
                    submission_time = datetime.fromtimestamp(s.get("timestamp")).strftime("%H:%M:%S %d/%m/%Y")
                else:
                    dt = datetime.fromisoformat(s.get("timestamp", "").replace("Z", "+00:00"))
                    submission_time = dt.strftime("%H:%M:%S %d/%m/%Y")
            except:
                pass
            
            user_data.append({
                "email": s.get("user_email", ""),
                "full_name": full_name,
                "class": class_name,
                "submission_id": s.get("id", ""),
                "timestamp": submission_time,
                "score": s.get("score", 0),
                "max_score": max_possible,
                "percent": f"{(s.get('score', 0)/max_possible*100):.1f}%" if max_possible > 0 else "N/A"
            })
        except Exception as e:
            st.error(f"Lỗi khi xử lý dữ liệu học viên: {str(e)}")
    
    if user_data:
        df_users = pd.DataFrame(user_data)
        
        # Lọc theo email hoặc lớp
        col1, col2 = st.columns(2)
        with col1:
            user_filter = st.selectbox(
                "Chọn học viên để xem chi tiết:",
                options=["Tất cả"] + sorted(list(set([u.get("email", "") for u in user_data]))),
                key="user_filter_tab2"
            )
        
        with col2:
            unique_classes = [u.get("class", "") for u in user_data if u.get("class") != "Không xác định"]
            class_filter = st.selectbox(
                "Lọc theo lớp:",
                options=["Tất cả"] + sorted(list(set(unique_classes))),
                key="class_filter_tab2"
            )
        
        # Áp dụng bộ lọc
        df_filtered = df_users
        
        if user_filter != "Tất cả":
            df_filtered = df_filtered[df_filtered["email"] == user_filter]
        
        if class_filter != "Tất cả":
            df_filtered = df_filtered[df_filtered["class"] == class_filter]
        
        # Hiển thị bảng
        st.dataframe(
            df_filtered.sort_values(by="timestamp", ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        # Xem chi tiết một bài nộp cụ thể
        if user_filter != "Tất cả":
            submission_ids = df_filtered["submission_id"].tolist()
            if submission_ids:
                selected_submission = st.selectbox(
                    "Chọn bài nộp để xem chi tiết:",
                    options=submission_ids,
                    key="submission_id_select"
                )
                
                # Tìm bài nộp được chọn
                submission = next((s for s in submissions if str(s.get("id", "")) == str(selected_submission)), None)
                if submission:
                    st.subheader(f"Chi tiết bài nộp #{selected_submission}")
                    
                    total_correct = 0
                    total_questions = len(questions)
                    student_detail_data = []
                    
                    # Đảm bảo responses đúng định dạng
                    responses = submission.get("responses", {})
                    if isinstance(responses, str):
                        try:
                            responses = json.loads(responses)
                        except:
                            responses = {}
                    
                    # Hiển thị câu trả lời chi tiết
                    for q in questions:
                        q_id = str(q.get("id", ""))
                        st.write(f"**Câu {q.get('id', '')}: {q.get('question', '')}**")
                        
                        # Đáp án người dùng
                        user_ans = responses.get(q_id, [])
                        
                        # Kiểm tra đúng/sai
                        is_correct = check_answer_correctness(user_ans, q)
                        if is_correct:
                            total_correct += 1
                        
                        # Hiển thị dựa trên loại câu hỏi
                        if q.get("type") == "Essay":
                            st.write("Câu trả lời của học viên:")
                            essay_answer = user_ans[0] if user_ans else "Không có câu trả lời"
                            st.text_area("", value=essay_answer, height=100, disabled=True,
                                        key=f"detail_essay_{q_id}")
                            
                            # Thu thập dữ liệu chi tiết
                            student_detail_data.append({
                                "Câu hỏi": f"Câu {q.get('id', '')}: {q.get('question', '')}",
                                "Đáp án của học viên": essay_answer,
                                "Đáp án đúng": "Câu hỏi tự luận",
                                "Kết quả": "Đã trả lời" if is_correct else "Không trả lời",
                                "Điểm": q.get("score", 0) if is_correct else 0
                            })
                            
                            # Hiển thị kết quả
                            if is_correct:
                                st.success(f"✅ Đã trả lời (+{q.get('score', 0)} điểm)")
                            else:
                                st.error("❌ Không trả lời (0 điểm)")
                        else:
                            # Đối với câu hỏi trắc nghiệm
                            # Chuẩn bị dữ liệu đáp án đúng
                            q_correct = q.get("correct", [])
                            q_answers = q.get("answers", [])
                            
                            if isinstance(q_correct, str):
                                try:
                                    q_correct = json.loads(q_correct)
                                except:
                                    try:
                                        q_correct = [int(x.strip()) for x in q_correct.split(",")]
                                    except:
                                        q_correct = []
                            
                            if isinstance(q_answers, str):
                                try:
                                    q_answers = json.loads(q_answers)
                                except:
                                    q_answers = [q_answers]
                            
                            try:
                                expected = [q_answers[i - 1] for i in q_correct]
                            except (IndexError, TypeError):
                                expected = ["Lỗi đáp án"]
                            
                            # Thu thập dữ liệu chi tiết
                            student_detail_data.append({
                                "Câu hỏi": f"Câu {q.get('id', '')}: {q.get('question', '')}",
                                "Đáp án của học viên": ", ".join([str(a) for a in user_ans]) if user_ans else "Không trả lời",
                                "Đáp án đúng": ", ".join([str(a) for a in expected]),
                                "Kết quả": "Đúng" if is_correct else "Sai",
                                "Điểm": q.get("score", 0) if is_correct else 0
                            })
                            
                            # Hiển thị đáp án của người dùng
                            st.write("Đáp án của học viên:")
                            if not user_ans:
                                st.write("- Không trả lời")
                            else:
                                for ans in user_ans:
                                    st.write(f"- {ans}")
                            
                            # Hiển thị kết quả
                            if is_correct:
                                st.success(f"✅ Đúng (+{q.get('score', 0)} điểm)")
                            else:
                                st.error("❌ Sai (0 điểm)")
                                st.write("Đáp án đúng:")
                                for ans in expected:
                                    st.write(f"- {ans}")
                        
                        st.divider()
                    
                    # Hiển thị thống kê tổng hợp
                    st.subheader("Tổng kết")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Số câu đúng", f"{total_correct}/{total_questions}")
                    col2.metric("Điểm số", f"{submission.get('score', 0)}/{max_possible}")
                    col3.metric("Tỷ lệ đúng", f"{(total_correct/total_questions*100):.1f}%" if total_questions > 0 else "0%")
                    
                    # Tạo DataFrame chi tiết
                    df_student_detail = pd.DataFrame(student_detail_data)
                    
                    # Xuất báo cáo chi tiết
                    st.write("### Xuất báo cáo chi tiết")
                    
                    # Người dùng và thông tin
                    student_info = next((student for student in students if student.get("email") == submission.get("user_email")), None)
                    student_name = student_info.get("full_name", "Không xác định") if student_info else "Không xác định"
                    student_class = student_info.get("class", "Không xác định") if student_info else "Không xác định"
                    
                    # Tạo báo cáo chi tiết
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Tạo báo cáo dạng DOCX
                        try:
                            docx_buffer = create_student_report_docx(
                                student_name,
                                submission.get("user_email", ""),
                                student_class,
                                submission,
                                questions,
                                max_possible
                            )
                            
                            st.markdown(
                                get_download_link_docx(docx_buffer, 
                                                    f"bao_cao_{student_name.replace(' ', '_')}_{submission.get('id', '')}.docx", 
                                                    "Tải xuống báo cáo chi tiết (DOCX)"), 
                                unsafe_allow_html=True
                            )
                        except Exception as e:
                            st.error(f"Không thể tạo báo cáo DOCX: {str(e)}")
                    
                    with col2:
                        # Tạo báo cáo dạng PDF
                        try:
                            pdf_buffer = create_student_report_pdf_fpdf(
                                student_name,
                                submission.get("user_email", ""),
                                student_class,
                                submission,
                                questions,
                                max_possible
                            )
                            
                            st.markdown(
                                get_download_link_pdf(pdf_buffer, 
                                                    f"bao_cao_{student_name.replace(' ', '_')}_{submission.get('id', '')}.pdf", 
                                                    "Tải xuống báo cáo chi tiết (PDF)"), 
                                unsafe_allow_html=True
                            )
                        except Exception as e:
                            st.error(f"Không thể tạo báo cáo PDF: {str(e)}")
    else:
        st.info("Không có dữ liệu học viên để hiển thị.")
