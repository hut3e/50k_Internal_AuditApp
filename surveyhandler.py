import json
import streamlit as st
from datetime import datetime

# Import từ các module khác
from database_helper import get_all_questions, save_submission, get_user_submissions

def survey_form(email, full_name, class_name):
    st.title("Làm bài khảo sát đánh giá viên nội bộ ISO 50001:2018")
    
    # Hiển thị thông tin người dùng
    st.write(f"**Người làm bài:** {full_name}")
    st.write(f"**Lớp:** {class_name}")
    st.write(f"**Email:** {email}")
    
    # Lấy danh sách câu hỏi từ database
    questions = get_all_questions()
    
    if not questions:
        st.info("Chưa có câu hỏi nào trong hệ thống.")
        return
    
    # Đảm bảo định dạng dữ liệu câu hỏi đúng
    for q in questions:
        # Đảm bảo answers là list
        if isinstance(q["answers"], str):
            try:
                q["answers"] = json.loads(q["answers"])
            except:
                q["answers"] = [q["answers"]]
        
        # Đảm bảo correct là list
        if isinstance(q["correct"], str):
            try:
                q["correct"] = json.loads(q["correct"])
            except:
                try:
                    q["correct"] = [int(x.strip()) for x in q["correct"].split(",")]
                except:
                    q["correct"] = []
    
    # Lấy lịch sử bài làm của học viên này
    user_submissions = get_user_submissions(email)
    
    # Đếm số lần đã làm bài
    submission_count = len(user_submissions)
    
    # Kiểm tra giới hạn làm bài (tối đa 3 lần)
    MAX_ATTEMPTS = 3
    remaining_attempts = MAX_ATTEMPTS - submission_count
    
    # Hiển thị số lần làm bài và giới hạn
    if submission_count > 0:
        st.write(f"**Số lần đã làm bài:** {submission_count}/{MAX_ATTEMPTS}")
        
        # Hiển thị điểm cao nhất đã đạt được
        max_score = max([s["score"] for s in user_submissions])
        max_possible = sum([q["score"] for q in questions])
        
        st.write(f"**Điểm cao nhất đã đạt được:** {max_score}/{max_possible} ({(max_score/max_possible*100):.1f}%)")
    else:
        st.write(f"**Đây là lần làm bài đầu tiên của bạn**")
    
    # Hiển thị số lượng câu hỏi và điểm tối đa
    total_questions = len(questions)
    max_score = sum([q["score"] for q in questions])
    st.write(f"**Tổng số câu hỏi:** {total_questions}")
    st.write(f"**Điểm tối đa:** {max_score}")
    
    # Kiểm tra nếu đã đạt đến giới hạn làm bài
    if remaining_attempts <= 0:
        st.error("⚠️ Bạn đã sử dụng hết số lần làm bài cho phép (tối đa 3 lần).")
        
        # Hiển thị các lần làm bài trước đó
        if st.checkbox("Xem lịch sử các lần làm bài", key="view_history_checkbox"):
            display_submission_history(user_submissions, questions, max_score)
        
        return
    
    # Thông báo số lần còn lại
    if 0 < remaining_attempts < MAX_ATTEMPTS:
        st.warning(f"⚠️ Bạn còn {remaining_attempts} lần làm bài.")
    
    # Khởi tạo biến theo dõi trạng thái nộp bài
    if "submission_result" not in st.session_state:
        st.session_state.submission_result = None
    
    # Nếu chưa nộp bài hoặc muốn làm lại
    if st.session_state.submission_result is None:
        # Tạo form để lưu trữ câu trả lời
        with st.form(key="survey_form"):
            st.subheader("Câu hỏi")
            
            # Lưu trữ câu trả lời tạm thời
            responses = {}
            
            for q in questions:
                q_id = q["id"]
                st.markdown(f"**Câu {q_id}: {q['question']}** *(Điểm: {q['score']})*")
                
                if q["type"] == "Checkbox":
                    responses[str(q_id)] = st.multiselect(
                        "Chọn đáp án", 
                        options=q["answers"], 
                        key=f"q_{q_id}"
                    )
                elif q["type"] == "Combobox":
                    selected = st.selectbox(
                        "Chọn 1 đáp án", 
                        options=[""] + q["answers"], 
                        key=f"q_{q_id}"
                    )
                    responses[str(q_id)] = [selected] if selected else []
                
                st.divider()
            
            # Nút gửi đáp án (trong form)
            submit_button = st.form_submit_button(label="📨 Gửi đáp án", use_container_width=True)
            
            if submit_button:
                # Kiểm tra lại số lần làm bài (để đảm bảo không vượt quá giới hạn)
                latest_submissions = get_user_submissions(email)
                if len(latest_submissions) >= MAX_ATTEMPTS:
                    st.error("Bạn đã sử dụng hết số lần làm bài cho phép!")
                    st.session_state.submission_result = None
                else:
                    # Lưu câu trả lời vào database với ID duy nhất
                    result = save_submission(email, responses)
                    
                    if result:
                        st.session_state.submission_result = result
                        st.session_state.max_score = max_score
                        st.rerun()  # Làm mới trang để hiển thị kết quả
                    else:
                        st.error("❌ Có lỗi xảy ra khi gửi đáp án, vui lòng thử lại!")
    
    # Hiển thị kết quả sau khi nộp bài
    else:
        result = st.session_state.submission_result
        max_score = st.session_state.max_score
        
        st.success(f"✅ Đã ghi nhận bài làm của bạn! (Mã nộp: {result['id']})")
        
        # Hiển thị thông tin chi tiết về kết quả
        display_submission_details(result, questions, max_score)
        
        # Cập nhật lại số lần làm bài sau khi nộp thành công
        updated_submissions = get_user_submissions(email)
        updated_count = len(updated_submissions)
        remaining = MAX_ATTEMPTS - updated_count
        
        # Nút làm bài lại (nếu còn lượt)
        if remaining > 0:
            if st.button("🔄 Làm bài lại", use_container_width=True, key="retry_button"):
                st.session_state.submission_result = None
                st.rerun()
        else:
            st.warning("⚠️ Bạn đã sử dụng hết số lần làm bài cho phép.")

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

def display_submission_details(submission, questions, max_score):
    """Hiển thị chi tiết về bài nộp, bao gồm thông tin điểm và câu trả lời."""
    
    # Hiển thị thông tin về lần nộp này
    if isinstance(submission["timestamp"], str):
        # Nếu timestamp là chuỗi ISO (sau khi bạn sửa code trước đó)
        try:
            # Chuyển từ chuỗi ISO sang đối tượng datetime
            dt = datetime.fromisoformat(submission["timestamp"].replace("Z", "+00:00"))
            submit_time = dt.strftime("%H:%M:%S %d/%m/%Y")
        except:
            # Xử lý trường hợp không thể parse được
            submit_time = "Không xác định"
    else:
        # Trường hợp vẫn còn dữ liệu cũ dạng Unix timestamp
        try:
            submit_time = datetime.fromtimestamp(submission["timestamp"]).strftime("%H:%M:%S %d/%m/%Y")
        except:
            submit_time = "Không xác định"
    
    # Tạo tab hiển thị tổng quan và chi tiết
    tab_summary, tab_details = st.tabs(["Tổng quan kết quả đợt kiểm tra", "Chi tiết câu trả lời"])
    
    with tab_summary:
        # Hiển thị kết quả trong một container màu xanh
        with st.container():
            st.markdown(f"""
            <div style="padding: 20px; background-color: #e6f7f2; border-radius: 10px; margin: 10px 0;">
                <h3 style="color: #2e7d64;">Thông tin bài nộp</h3>
                <p><b>Thời gian nộp:</b> {submit_time}</p>
                <p><b>Điểm số:</b> {submission['score']}/{max_score}</p>
                <p><b>Tỷ lệ đúng:</b> {(submission['score']/max_score*100):.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Hiển thị biểu đồ kết quả
        correct_count = sum(1 for q in questions if check_correct_for_report(submission, q))
        incorrect_count = len(questions) - correct_count
        
        # Hiển thị dạng biểu đồ đơn giản
        st.subheader("Thống kê kết quả")
        
        col1, col2 = st.columns(2)
        col1.metric("Câu trả lời đúng", f"{correct_count}/{len(questions)}")
        col2.metric("Câu trả lời sai", f"{incorrect_count}/{len(questions)}")
        
        # Tạo progress bar hiển thị tỷ lệ đúng/sai
        st.progress(correct_count / len(questions))
        st.caption(f"Tỷ lệ câu trả lời đúng: {(correct_count / len(questions) * 100):.1f}%")
    
    with tab_details:
        st.subheader("Chi tiết câu trả lời")
        
        # Hiển thị chi tiết từng câu hỏi
        for q in questions:
            q_id = str(q["id"])
            
            # Lấy câu trả lời của học viên
            student_answers = submission["responses"].get(q_id, [])
            
            # Kiểm tra tính đúng đắn
            is_correct = check_answer_correctness(student_answers, q)
            
            # Hiển thị với nền màu khác nhau tùy theo đúng/sai
            background_color = "#e6f7f2" if is_correct else "#ffebee"
            text_color = "#2e7d64" if is_correct else "#d32f2f"
            
            with st.container():
                st.markdown(f"""
                <div style="padding: 15px; background-color: {background_color}; border-radius: 8px; margin: 8px 0;">
                    <h4 style="color: {text_color};">Câu {q['id']}: {q['question']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Đáp án đúng
                expected_indices = q["correct"]
                expected_answers = [q["answers"][i - 1] for i in expected_indices]
                
                # Hiển thị đáp án người dùng đã chọn
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
                    st.write("Đáp án đúng:")
                    for ans in expected_answers:
                        st.write(f"- {ans}")
                
                st.divider()

def check_correct_for_report(submission, question):
    """Kiểm tra xem câu trả lời có đúng không để hiển thị trong báo cáo."""
    q_id = str(question["id"])
    student_answers = submission["responses"].get(q_id, [])
    return check_answer_correctness(student_answers, question)

def display_submission_history(submissions, questions, max_score):
    """Hiển thị lịch sử các lần nộp bài."""
    st.subheader("Lịch sử làm bài")
    
    # Tạo biểu đồ tiến độ điểm số
    scores = [s["score"] for s in submissions]
    attempts = [f"Lần {i+1}" for i in range(len(submissions))]
    
    # Hiển thị dạng bảng so sánh
    st.subheader("So sánh điểm số các lần làm bài")
    
    # Tạo dữ liệu cho bảng
    data = []
    for idx, s in enumerate(submissions):
        if isinstance(s["timestamp"], (int, float)):
            # Trường hợp timestamp là số (dữ liệu cũ)
            submission_time = datetime.fromtimestamp(s["timestamp"]).strftime("%H:%M:%S %d/%m/%Y")
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
        data.append({
            "Lần": idx + 1,
            "Thời gian": submission_time,
            "Điểm số": f"{s['score']}/{max_score}",
            "Tỷ lệ": f"{score_percent:.1f}%"
        })
    
    # Hiển thị bảng
    for item in data:
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        col1.write(f"**{item['Lần']}**")
        col2.write(item["Thời gian"])
        col3.write(item["Điểm số"])
        col4.write(item["Tỷ lệ"])
        st.divider()
    
    # Hiển thị chi tiết từng lần làm
    for idx, s in enumerate(submissions):
        if isinstance(s["timestamp"], (int, float)):
            # Trường hợp timestamp là số (dữ liệu cũ)
            submission_time = datetime.fromtimestamp(s["timestamp"]).strftime("%H:%M:%S %d/%m/%Y")
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
        with st.expander(f"Lần {idx + 1}: Ngày {submission_time} - Điểm: {s['score']}/{max_score}"):
            # Hiển thị chi tiết kết quả như trong hàm display_submission_details
            # Đơn giản hóa hiển thị để tránh quá nhiều thông tin
            correct_count = sum(1 for q in questions if check_correct_for_report(s, q))
            
            # Hiển thị tỷ lệ đúng/sai
            st.progress(correct_count / len(questions))
            st.caption(f"Tỷ lệ câu trả lời đúng: {(correct_count / len(questions) * 100):.1f}%")
            
            # Hiển thị chi tiết từng câu hỏi
            for q in questions:
                q_id = str(q["id"])
                
                # Lấy câu trả lời của học viên
                student_answers = s["responses"].get(q_id, [])
                
                # Kiểm tra tính đúng đắn
                is_correct = check_answer_correctness(student_answers, q)
                
                # Hiển thị đáp án người dùng đã chọn
                st.write(f"**Câu {q['id']}: {q['question']}**")
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