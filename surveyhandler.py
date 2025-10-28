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
    
    # Quản lý trạng thái số lần làm và xác nhận hoàn thành
    MAX_ATTEMPTS = 3
    submission_count = len(user_submissions)
    if "attempt_index" not in st.session_state:
        # Lần tiếp theo theo DB, giới hạn tối đa 3
        st.session_state.attempt_index = min(MAX_ATTEMPTS, submission_count + 1)
    if "completed_attempts" not in st.session_state:
        st.session_state.completed_attempts = False  # Đã xác nhận hoàn thành hay chưa
    if "await_continue_confirm" not in st.session_state:
        st.session_state.await_continue_confirm = False  # Đang yêu cầu xác nhận tiếp tục hay kết thúc
    if "last_submission" not in st.session_state:
        st.session_state.last_submission = None  # Lưu lần nộp gần nhất để hiển thị khi hoàn tất
    if "last_max_score" not in st.session_state:
        st.session_state.last_max_score = None
    
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
    
    # Nếu đã hết lượt theo DB
    if remaining_attempts <= 0 and not st.session_state.completed_attempts:
        # Bắt buộc xác nhận hoàn thành để xem kết quả
        st.warning("Bạn đã đạt tối đa 3 lần. Hãy xác nhận hoàn thành để xem kết quả.")
        if st.button("✅ Xác nhận hoàn thành và xem kết quả", use_container_width=True, key="confirm_complete_full"):
            st.session_state.completed_attempts = True
            st.rerun()
        return
    
    # Thông báo số lần còn lại
    if 0 < remaining_attempts < MAX_ATTEMPTS:
        st.warning(f"⚠️ Bạn còn {remaining_attempts} lần làm bài.")
    
    # Khởi tạo biến theo dõi trạng thái nộp bài (trong một attempt)
    if "submission_result" not in st.session_state:
        st.session_state.submission_result = None

    # Nếu đã xác nhận hoàn thành -> hiển thị kết quả (lịch sử + chi tiết lần gần nhất)
    if st.session_state.completed_attempts:
        st.success("Bạn đã hoàn thành. Dưới đây là kết quả các lần làm bài.")
        display_submission_history(get_user_submissions(email), questions, max_score)
        # Nếu có lần nộp cuối cùng trong phiên, hiển thị chi tiết
        if st.session_state.last_submission is not None:
            st.divider()
            st.subheader("Chi tiết lần nộp cuối cùng")
            display_submission_details(st.session_state.last_submission, questions, st.session_state.last_max_score or max_score)
        return

    # Nếu chưa nộp bài hoặc đang trong quá trình xác nhận tiếp tục/kết thúc
    if st.session_state.submission_result is None and not st.session_state.await_continue_confirm:
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
                        key=f"attempt_{st.session_state.attempt_index}_q_{q_id}"
                    )
                elif q["type"] == "Combobox":
                    selected = st.selectbox(
                        "Chọn 1 đáp án", 
                        options=[""] + q["answers"], 
                        key=f"attempt_{st.session_state.attempt_index}_q_{q_id}"
                    )
                    responses[str(q_id)] = [selected] if selected else []
                elif q["type"] == "Essay":
                    # Hiển thị mẫu câu trả lời nếu có
                    if q.get("answer_template"):
                        st.info(f"Gợi ý: {q.get('answer_template')}")
                    
                    # Sử dụng text_area để cho phép nhập text tự do
                    essay_answer = st.text_area(
                        "Nhập câu trả lời",
                        height=150,
                        key=f"attempt_{st.session_state.attempt_index}_q_{q_id}"
                    )
                    responses[str(q_id)] = [essay_answer] if essay_answer else []
                
                st.divider()
            
            # Nút gửi đáp án (trong form)
            submit_button = st.form_submit_button(label=f"📨 Gửi đáp án (lần {st.session_state.attempt_index})", use_container_width=True)
            
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
                        # Không hiển thị kết quả ngay; yêu cầu xác nhận tiếp tục/kết thúc
                        st.session_state.submission_result = result
                        st.session_state.max_score = max_score
                        st.session_state.last_submission = result
                        st.session_state.last_max_score = max_score
                        st.session_state.await_continue_confirm = True
                        st.rerun()
                    else:
                        st.error("❌ Có lỗi xảy ra khi gửi đáp án, vui lòng thử lại!")

    # Sau khi nộp, yêu cầu xác nhận tiếp tục/kết thúc
    if st.session_state.await_continue_confirm and st.session_state.submission_result is not None:
        result = st.session_state.submission_result
        st.success(f"✅ Đã ghi nhận bài làm lần {st.session_state.attempt_index}! (Mã nộp: {result['id']})")
        col1, col2 = st.columns(2)
        with col1:
            can_continue = (submission_count + 1) < MAX_ATTEMPTS
            if can_continue:
                if st.button(f"➡️ Tiếp tục làm lần {st.session_state.attempt_index + 1}", use_container_width=True, key="confirm_continue"):
                    # Tăng attempt, chuẩn bị form mới với key độc lập
                    st.session_state.attempt_index = min(MAX_ATTEMPTS, st.session_state.attempt_index + 1)
                    st.session_state.submission_result = None
                    st.session_state.await_continue_confirm = False
                    st.rerun()
            else:
                st.info("Đã đạt tối đa 3 lần. Vui lòng xác nhận hoàn thành để xem kết quả.")
        with col2:
            if st.button("✅ Hoàn thành và xem kết quả", use_container_width=True, key="confirm_finish"):
                st.session_state.completed_attempts = True
                st.session_state.await_continue_confirm = False
                st.rerun()

def check_answer_correctness(student_answers, question):
    """Kiểm tra đáp án có đúng không, hỗ trợ chọn nhiều đáp án và câu hỏi tự luận."""
    # Nếu câu trả lời trống, không đúng
    if not student_answers:
        return False
        
    # Đối với câu hỏi tự luận (Essay), luôn đánh giá là đúng nếu có trả lời
    if question["type"] == "Essay":
        # Chỉ cần học viên nhập nội dung vào ô text là tính đúng
        return len(student_answers) > 0 and student_answers[0].strip() != ""
        
    # Đối với câu hỏi combobox (chỉ chọn một)
    elif question["type"] == "Combobox":
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
                
                # Hiển thị khác nhau dựa trên loại câu hỏi
                if q["type"] == "Essay":
                    # Hiển thị câu trả lời tự luận
                    st.write("Câu trả lời của bạn:")
                    essay_answer = student_answers[0] if student_answers else "Không có câu trả lời"
                    st.text_area("", value=essay_answer, height=100, disabled=True,
                                key=f"display_essay_{q_id}")
                    
                    # Đối với câu hỏi tự luận, luôn tính là đúng nếu có trả lời
                    if is_correct:
                        st.success(f"✅ Đã trả lời (+{q['score']} điểm)")
                    else:
                        st.error("❌ Không trả lời (0 điểm)")
                else:
                    # Đối với câu hỏi trắc nghiệm, hiển thị các đáp án
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
                
                if q["type"] == "Essay":
                    # Hiển thị câu trả lời tự luận
                    st.write("Câu trả lời của bạn:")
                    essay_answer = student_answers[0] if student_answers else "Không có câu trả lời"
                    st.text_area("", value=essay_answer, height=100, disabled=True,
                                key=f"history_essay_{q_id}_{idx}")
                    
                    # Đối với câu hỏi tự luận, luôn tính là đúng nếu có trả lời
                    if is_correct:
                        st.success(f"✅ Đã trả lời (+{q['score']} điểm)")
                    else:
                        st.error("❌ Không trả lời (0 điểm)")
                else:
                    # Hiển thị đáp án của câu hỏi trắc nghiệm
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
