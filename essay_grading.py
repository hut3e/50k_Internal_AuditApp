import streamlit as st
import json
from datetime import datetime
from database_helper import (
    get_supabase_client, 
    get_all_questions, 
    get_all_users,
    update_submission
)

def essay_grading_interface():
    """Interface cho giảng viên chấm điểm câu hỏi tự luận"""
    st.title("🎯 Chấm điểm câu hỏi tự luận")
    
    # Lấy dữ liệu
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến database")
            return
            
        # Lấy tất cả bài nộp có câu hỏi tự luận
        submissions_result = supabase.table("submissions").select("*").execute()
        submissions = submissions_result.data if submissions_result.data else []
        
        questions = get_all_questions()
        students = get_all_users(role="student")
        
        # Lọc các câu hỏi tự luận
        essay_questions = [q for q in questions if q.get("type") == "Essay"]
        
        if not essay_questions:
            st.info("Không có câu hỏi tự luận nào trong hệ thống.")
            return
            
        if not submissions:
            st.info("Chưa có bài nộp nào để chấm.")
            return
            
        # Hiển thị thống kê
        st.subheader("Thống kê chấm điểm")
        
        total_essays = 0
        graded_essays = 0
        
        for submission in submissions:
            essay_grades = submission.get("essay_grades", {})
            if isinstance(essay_grades, str):
                try:
                    essay_grades = json.loads(essay_grades)
                except:
                    essay_grades = {}
                    
            responses = submission.get("responses", {})
            if isinstance(responses, str):
                try:
                    responses = json.loads(responses)
                except:
                    responses = {}
            
            for eq in essay_questions:
                eq_id = str(eq.get("id"))
                if eq_id in responses and responses[eq_id]:
                    total_essays += 1
                    if eq_id in essay_grades:
                        graded_essays += 1
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng số bài tự luận", total_essays)
        col2.metric("Đã chấm điểm", graded_essays)
        col3.metric("Chưa chấm", total_essays - graded_essays)
        
        # Bộ lọc
        st.subheader("Bộ lọc")
        
        col1, col2 = st.columns(2)
        with col1:
            filter_status = st.selectbox(
                "Trạng thái chấm điểm:",
                ["Tất cả", "Chưa chấm", "Đã chấm"]
            )
            
        with col2:
            filter_question = st.selectbox(
                "Câu hỏi:",
                ["Tất cả"] + [f"Câu {q['id']}: {q['question'][:50]}..." for q in essay_questions]
            )
        
        # Lọc và hiển thị bài nộp
        filtered_submissions = []
        
        for submission in submissions:
            essay_grades = submission.get("essay_grades", {})
            if isinstance(essay_grades, str):
                try:
                    essay_grades = json.loads(essay_grades)
                except:
                    essay_grades = {}
                    
            responses = submission.get("responses", {})
            if isinstance(responses, str):
                try:
                    responses = json.loads(responses)
                except:
                    responses = {}
            
            for eq in essay_questions:
                eq_id = str(eq.get("id"))
                if eq_id in responses and responses[eq_id]:
                    # Áp dụng bộ lọc
                    if filter_status == "Chưa chấm" and eq_id in essay_grades:
                        continue
                    if filter_status == "Đã chấm" and eq_id not in essay_grades:
                        continue
                    if filter_question != "Tất cả" and not filter_question.startswith(f"Câu {eq['id']}"):
                        continue
                        
                    filtered_submissions.append({
                        "submission": submission,
                        "question": eq,
                        "is_graded": eq_id in essay_grades,
                        "current_grade": essay_grades.get(eq_id, 0)
                    })
        
        # Hiển thị danh sách bài cần chấm
        st.subheader("Danh sách bài cần chấm")
        
        if not filtered_submissions:
            st.info("Không có bài nào phù hợp với bộ lọc.")
            return
            
        for idx, item in enumerate(filtered_submissions):
            submission = item["submission"]
            question = item["question"]
            is_graded = item["is_graded"]
            current_grade = item["current_grade"]
            
            # Tìm thông tin học viên
            student_info = next(
                (s for s in students if s.get("email") == submission.get("user_email")), 
                None
            )
            student_name = student_info.get("full_name", "Không xác định") if student_info else "Không xác định"
            
            # Hiển thị bài làm
            with st.expander(
                f"{'✅' if is_graded else '⏳'} {student_name} - Câu {question['id']} - "
                f"{'Đã chấm' if is_graded else 'Chưa chấm'}"
            ):
                # Thông tin bài nộp
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Học viên:** {student_name}")
                    st.write(f"**Email:** {submission.get('user_email')}")
                    
                with col2:
                    # Xử lý timestamp
                    timestamp = submission.get("timestamp", "")
                    if isinstance(timestamp, str):
                        try:
                            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            submit_time = dt.strftime("%H:%M:%S %d/%m/%Y")
                        except:
                            submit_time = "Không xác định"
                    else:
                        try:
                            submit_time = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S %d/%m/%Y")
                        except:
                            submit_time = "Không xác định"
                    
                    st.write(f"**Thời gian nộp:** {submit_time}")
                    st.write(f"**ID bài nộp:** {submission.get('id')}")
                
                # Hiển thị câu hỏi và câu trả lời
                st.write(f"**Câu hỏi:** {question['question']}")
                st.write(f"**Điểm tối đa:** {question.get('score', 0)}")
                
                # Lấy câu trả lời
                responses = submission.get("responses", {})
                if isinstance(responses, str):
                    try:
                        responses = json.loads(responses)
                    except:
                        responses = {}
                
                q_id = str(question["id"])
                essay_answer = responses.get(q_id, [""])[0] if responses.get(q_id) else ""
                
                st.write("**Câu trả lời của học viên:**")
                st.text_area(
                    "", 
                    value=essay_answer, 
                    height=200, 
                    disabled=True,
                    key=f"answer_{submission['id']}_{q_id}"
                )
                
                # Form chấm điểm
                with st.form(key=f"grading_form_{submission['id']}_{q_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        grade = st.number_input(
                            "Điểm số:",
                            min_value=0.0,
                            max_value=float(question.get('score', 0)),
                            value=float(current_grade),
                            step=0.5,
                            key=f"grade_{submission['id']}_{q_id}"
                        )
                    
                    with col2:
                        # Lấy nhận xét hiện tại
                        essay_comments = submission.get("essay_comments", {})
                        if isinstance(essay_comments, str):
                            try:
                                essay_comments = json.loads(essay_comments)
                            except:
                                essay_comments = {}
                        
                        current_comment = essay_comments.get(q_id, "")
                        
                        comment = st.text_area(
                            "Nhận xét:",
                            value=current_comment,
                            height=100,
                            key=f"comment_{submission['id']}_{q_id}"
                        )
                    
                    submit_grade = st.form_submit_button("💾 Lưu điểm")
                    
                    if submit_grade:
                        # Cập nhật điểm và nhận xét
                        if update_essay_grade(submission["id"], q_id, grade, comment):
                            st.success("✅ Đã lưu điểm thành công!")
                            st.rerun()
                        else:
                            st.error("❌ Có lỗi khi lưu điểm!")
                
                # Hiển thị trạng thái hiện tại
                if is_graded:
                    st.success(f"✅ Đã chấm điểm: {current_grade}/{question.get('score', 0)}")
                else:
                    st.warning("⏳ Chưa chấm điểm")
                    
    except Exception as e:
        st.error(f"Có lỗi xảy ra: {str(e)}")

# Thay thế hàm update_essay_grade hiện tại:

def update_essay_grade(submission_id, question_id, grade, comment):
    """Cập nhật điểm và nhận xét cho câu hỏi tự luận - ĐÃ SỬA LỖI KIỂU DỮ LIỆU"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
            
        print(f"🔄 Bắt đầu cập nhật điểm cho submission {submission_id}, câu {question_id}")
        
        # Lấy thông tin bài nộp hiện tại
        result = supabase.table("submissions").select("*").eq("id", submission_id).execute()
        if not result.data:
            print("❌ Không tìm thấy submission")
            return False
            
        submission = result.data[0]
        print(f"📊 Điểm hiện tại: {submission.get('score', 0)}")
        
        # Cập nhật essay_grades
        essay_grades = submission.get("essay_grades", {})
        if isinstance(essay_grades, str):
            try:
                essay_grades = json.loads(essay_grades)
            except:
                essay_grades = {}
        
        # 🔧 SỬA: Đảm bảo grade là số và lưu dưới dạng number trong JSON
        try:
            grade_number = float(grade)
        except (ValueError, TypeError):
            grade_number = 0.0
        
        # Lưu điểm cũ để debug
        old_grade = essay_grades.get(question_id, 0)
        essay_grades[question_id] = grade_number  # 🔧 Lưu dưới dạng number, không phải string
        print(f"📝 Cập nhật điểm câu {question_id}: {old_grade} → {grade_number}")
        
        # Cập nhật essay_comments
        essay_comments = submission.get("essay_comments", {})
        if isinstance(essay_comments, str):
            try:
                essay_comments = json.loads(essay_comments)
            except:
                essay_comments = {}
        
        essay_comments[question_id] = str(comment)
        
        # ✅ TÍNH LẠI TỔNG ĐIỂM BẰNG HÀM calculate_total_score
        questions = get_all_questions()
        
        # Tạo submission mới với essay_grades đã cập nhật
        updated_submission = submission.copy()
        updated_submission["essay_grades"] = essay_grades
        
        # Import và tính lại tổng điểm
        from database_helper import calculate_total_score
        new_total_score = calculate_total_score(updated_submission, questions)
        
        print(f"🎯 Tổng điểm mới: {new_total_score} (type: {type(new_total_score)})")
        
        # 🔧 SỬA: Đảm bảo new_total_score là INTEGER
        if not isinstance(new_total_score, int):
            new_total_score = int(round(float(new_total_score)))
            print(f"🔧 Converted to integer: {new_total_score}")
        
        # Cập nhật vào database
        update_data = {
            "essay_grades": json.dumps(essay_grades),
            "essay_comments": json.dumps(essay_comments),
            "score": new_total_score  # ✅ ĐẢM BẢO LÀ INTEGER
        }
        
        print(f"📤 Dữ liệu cập nhật: {update_data}")
        
        result = supabase.table("submissions").update(update_data).eq("id", submission_id).execute()
        
        if result.data:
            print(f"✅ Cập nhật thành công! Điểm mới: {new_total_score}")
            return True
        else:
            print("❌ Lỗi khi cập nhật database")
            return False
        
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật điểm: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
