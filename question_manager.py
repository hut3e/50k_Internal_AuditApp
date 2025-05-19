import streamlit as st
from database_helper import save_question, get_all_questions, get_question_by_id, update_question, delete_question
import json

def manage_questions():
    st.title("Quản lý câu hỏi")
    
    # Khi bấm Tab này, tải câu hỏi từ database
    if "db_questions" not in st.session_state:
        st.session_state.db_questions = get_all_questions()
    
    # Khởi tạo biến câu hỏi mới trong session state
    if "new_question" not in st.session_state:
        st.session_state.new_question = {
            "question": "",
            "type": "Checkbox",
            "answers": [],
            "correct": [],
            "score": 1
        }
    
    # Khởi tạo biến chỉnh sửa
    if "editing_question" not in st.session_state:
        st.session_state.editing_question = None
    
    # Khởi tạo biến xác nhận xóa
    if "question_to_delete" not in st.session_state:
        st.session_state.question_to_delete = None

    # Ba tab: Thêm câu hỏi mới, Danh sách câu hỏi, và Chỉnh sửa câu hỏi
    tabs = ["Thêm câu hỏi mới", "Danh sách câu hỏi"]
    
    # Nếu đang chỉnh sửa câu hỏi, thêm tab chỉnh sửa
    if st.session_state.editing_question:
        tabs.append(f"Chỉnh sửa câu hỏi #{st.session_state.editing_question['id']}")
    
    # Tạo tabs
    selected_tab = st.tabs(tabs)
    
    # Tab thêm câu hỏi mới
    with selected_tab[0]:
        add_new_question()
    
    # Tab danh sách câu hỏi
    with selected_tab[1]:
        list_questions()
    
    # Tab chỉnh sửa câu hỏi (nếu có)
    if st.session_state.editing_question and len(selected_tab) > 2:
        with selected_tab[2]:
            edit_question()

def add_new_question():
    q = st.session_state.new_question
    q["question"] = st.text_input("Nội dung câu hỏi", value=q["question"], key="new_question_content")
    q["type"] = st.selectbox("Loại câu hỏi", ["Checkbox", "Combobox"], 
                          index=["Checkbox", "Combobox"].index(q["type"]),
                          key="new_question_type")
    q["score"] = st.number_input("Số điểm", min_value=1, value=q["score"], key="new_question_score")

    # Quản lý danh sách đáp án
    st.subheader("Danh sách đáp án")
    new_ans = st.text_input("Thêm đáp án mới", key="new_answer_input")
    if st.button("➕ Thêm đáp án", key="add_answer_btn"):
        if new_ans:
            q["answers"].append(new_ans)
            
    # Hiển thị các đáp án hiện có
    for idx, ans in enumerate(q["answers"]):
        col1, col2 = st.columns([5, 1])
        col1.write(f"{idx + 1}. {ans}")
        if col2.button("🗑️", key=f"del_ans_new_{idx}"):
            q["answers"].pop(idx)
            st.rerun()

    # Đáp án đúng
    correct_ans = st.text_input("Đáp án đúng (STT, phân cách bằng dấu phẩy)", 
                              value=",".join(map(str, q["correct"])),
                              key="new_correct_answers")
    if correct_ans:
        try:
            q["correct"] = list(map(int, correct_ans.split(",")))
        except:
            st.warning("Đáp án phải là số, phân cách bằng dấu phẩy")

    # Lưu câu hỏi vào database
    if st.button("🧠 Lưu câu hỏi", key="save_question_btn"):
        if not q["question"]:
            st.error("Vui lòng nhập nội dung câu hỏi")
        elif not q["answers"]:
            st.error("Vui lòng thêm ít nhất một đáp án")
        elif not q["correct"]:
            st.error("Vui lòng chỉ định ít nhất một đáp án đúng")
        else:
            # Lưu vào database
            if save_question(q):
                # Làm mới danh sách câu hỏi
                st.session_state.db_questions = get_all_questions()
                # Làm mới form
                st.session_state.new_question = {
                    "question": "",
                    "type": "Checkbox",
                    "answers": [],
                    "correct": [],
                    "score": 1
                }
                st.success("✅ Đã lưu câu hỏi vào hệ thống!")
                st.rerun()

def list_questions():
    # Hiển thị danh sách câu hỏi từ database
    questions = st.session_state.db_questions
    
    if not questions:
        st.info("Chưa có câu hỏi nào trong hệ thống")
    else:
        st.subheader(f"Đã có {len(questions)} câu hỏi")
        
        # Hộp xác nhận xóa (nếu có)
        if st.session_state.question_to_delete:
            delete_confirmation()
        
        for i, q in enumerate(questions):
            with st.expander(f"Câu {i + 1}: {q['question']}"):
                st.write(f"**ID:** {q['id']}")
                st.write(f"**Loại câu hỏi:** {q['type']}")
                st.write(f"**Điểm:** {q['score']}")
                
                st.write("**Các đáp án:**")
                # Đảm bảo answers là list
                answers = q["answers"]
                if isinstance(answers, str):
                    try:
                        answers = json.loads(answers)
                    except:
                        answers = [answers]
                
                # Đảm bảo correct là list
                correct = q["correct"]
                if isinstance(correct, str):
                    try:
                        correct = json.loads(correct)
                    except:
                        try:
                            correct = [int(x.strip()) for x in correct.split(",")]
                        except:
                            correct = []
                
                for j, ans in enumerate(answers):
                    is_correct = (j + 1) in correct
                    st.write(f"- {j + 1}. {ans} {' ✅' if is_correct else ''}")
                
                # Thêm nút sửa và xóa
                col1, col2 = st.columns(2)
                
                if col1.button("✏️ Sửa", key=f"edit_q_{q['id']}"):
                    # Lấy dữ liệu câu hỏi từ database
                    question_data = get_question_by_id(q['id'])
                    if question_data:
                        st.session_state.editing_question = question_data
                        st.rerun()
                
                if col2.button("🗑️ Xóa", key=f"del_q_{q['id']}"):
                    st.session_state.question_to_delete = q
                    st.rerun()
                    
        if st.button("🔄 Làm mới danh sách", key="refresh_question_list"):
            st.session_state.db_questions = get_all_questions()
            st.rerun()

def edit_question():
    """Chức năng chỉnh sửa câu hỏi"""
    q = st.session_state.editing_question
    q_id = q['id']  # Lấy ID câu hỏi để tạo key duy nhất
    
    st.subheader(f"Chỉnh sửa câu hỏi #{q_id}")
    
    # Form chỉnh sửa câu hỏi
    edited_question = st.text_input("Nội dung câu hỏi", value=q["question"], key=f"edit_question_content_{q_id}")
    edited_type = st.selectbox("Loại câu hỏi", ["Checkbox", "Combobox"], 
                             index=["Checkbox", "Combobox"].index(q["type"]),
                             key=f"edit_question_type_{q_id}")
    edited_score = st.number_input("Số điểm", min_value=1, value=q["score"], key=f"edit_question_score_{q_id}")
    
    # Sao chép danh sách đáp án để có thể chỉnh sửa
    if "edited_answers" not in st.session_state:
        # Đảm bảo q["answers"] là danh sách
        if isinstance(q["answers"], str):
            try:
                # Nếu là JSON string, thử chuyển đổi thành list
                answers_list = json.loads(q["answers"])
                st.session_state.edited_answers = answers_list
            except:
                # Nếu không thể parse JSON, tạo list từ string
                st.session_state.edited_answers = [q["answers"]]
        else:
            # Nếu đã là list, sao chép nó
            st.session_state.edited_answers = list(q["answers"])
    
    # Sao chép đáp án đúng
    if "edited_correct" not in st.session_state:
        # Đảm bảo q["correct"] là danh sách
        if isinstance(q["correct"], str):
            try:
                # Nếu là JSON string, thử chuyển đổi thành list
                correct_list = json.loads(q["correct"])
                st.session_state.edited_correct = correct_list
            except:
                # Nếu không thể parse JSON, thử chuyển đổi từ dạng "1,2,3" thành [1,2,3]
                try:
                    st.session_state.edited_correct = [int(x.strip()) for x in q["correct"].split(",")]
                except:
                    st.session_state.edited_correct = []
        else:
            # Nếu đã là list, sao chép nó
            st.session_state.edited_correct = list(q["correct"])
    
    # Quản lý danh sách đáp án
    st.subheader("Danh sách đáp án")
    new_ans = st.text_input("Thêm đáp án mới", key=f"edit_new_ans_{q_id}")
    if st.button("➕ Thêm đáp án", key=f"edit_add_ans_{q_id}"):
        if new_ans:
            st.session_state.edited_answers.append(new_ans)
            st.rerun()
    
    # Hiển thị các đáp án hiện có
    for idx, ans in enumerate(st.session_state.edited_answers):
        col1, col2, col3 = st.columns([4, 1, 1])
        
        # Trường nhập liệu để sửa đáp án
        edited_ans = col1.text_input(f"Đáp án {idx+1}", value=ans, key=f"edit_ans_{q_id}_{idx}")
        st.session_state.edited_answers[idx] = edited_ans
        
        # Checkbox để đánh dấu đáp án đúng
        is_correct = (idx + 1) in st.session_state.edited_correct
        if col2.checkbox("✓", value=is_correct, key=f"edit_correct_{q_id}_{idx}"):
            if (idx + 1) not in st.session_state.edited_correct:
                st.session_state.edited_correct.append(idx + 1)
        else:
            if (idx + 1) in q["correct"]:
                q["correct"].remove(idx + 1)
        
        # Nút xóa đáp án
        if col3.button("🗑️", key=f"del_ans_new_{idx}"):
            q["answers"].pop(idx)
            # Cập nhật lại đáp án đúng
            q["correct"] = [c for c in q["correct"] if c != idx + 1]
            # Điều chỉnh lại các đáp án đúng có số thứ tự lớn hơn
            q["correct"] = [c - 1 if c > idx + 1 else c for c in q["correct"]]
            st.rerun()

    # Hiển thị mô tả về đáp án đúng
    st.info(f"""
    **Hướng dẫn chọn đáp án đúng:**
    - Đối với câu hỏi Checkbox: Có thể chọn nhiều đáp án đúng.
    - Đối với câu hỏi Combobox: Chỉ nên chọn một đáp án đúng.
    - Đánh dấu ✓ cho các đáp án đúng.
    """)

    # Lưu câu hỏi vào database
    if st.button("🧠 Lưu câu hỏi", key="save_question_btn"):
        if not q["question"]:
            st.error("Vui lòng nhập nội dung câu hỏi")
        elif not q["answers"]:
            st.error("Vui lòng thêm ít nhất một đáp án")
        elif not q["correct"]:
            st.error("Vui lòng chỉ định ít nhất một đáp án đúng")
        elif q["type"] == "Combobox" and len(q["correct"]) > 1:
            st.warning("Câu hỏi Combobox nên chỉ có 1 đáp án đúng. Hãy xem xét lại hoặc đổi thành Checkbox.")
            if st.button("Vẫn muốn lưu", key="force_save_btn"):
                if save_question(q):
                    reset_new_question_form()
            
        else:
            # Lưu vào database
            if save_question(q):
                reset_new_question_form()

def reset_new_question_form():
    """Reset form câu hỏi mới sau khi lưu thành công"""
    # Làm mới danh sách câu hỏi
    st.session_state.db_questions = get_all_questions()
    # Làm mới form
    st.session_state.new_question = {
        "question": "",
        "type": "Checkbox",
        "answers": [],
        "correct": [],
        "score": 1
    }
    st.success("✅ Đã lưu câu hỏi vào hệ thống!")
    st.rerun()

def list_questions():
    # Hiển thị danh sách câu hỏi từ database
    questions = st.session_state.db_questions
    
    if not questions:
        st.info("Chưa có câu hỏi nào trong hệ thống")
    else:
        st.subheader(f"Đã có {len(questions)} câu hỏi")
        
        # Hộp xác nhận xóa (nếu có)
        if st.session_state.question_to_delete:
            delete_confirmation()
        
        # Tính tổng điểm toàn bộ câu hỏi
        total_score = sum(q.get("score", 0) for q in questions)
        st.write(f"**Tổng điểm:** {total_score}")
        
        # Bộ lọc loại câu hỏi
        question_types = ["Tất cả", "Checkbox", "Combobox"]
        selected_type = st.selectbox("Lọc theo loại câu hỏi:", question_types, key="filter_question_type")
        
        # Đếm số câu hỏi theo loại
        checkbox_count = sum(1 for q in questions if q.get("type") == "Checkbox")
        combobox_count = sum(1 for q in questions if q.get("type") == "Combobox")
        
        # Hiển thị thống kê
        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng số câu hỏi", len(questions))
        col2.metric("Câu hỏi Checkbox", checkbox_count)
        col3.metric("Câu hỏi Combobox", combobox_count)
        
        # Lọc câu hỏi theo loại
        filtered_questions = questions
        if selected_type != "Tất cả":
            filtered_questions = [q for q in questions if q.get("type") == selected_type]
        
        for i, q in enumerate(filtered_questions):
            with st.expander(f"Câu {i + 1}: {q['question']}"):
                st.write(f"**ID:** {q['id']}")
                st.write(f"**Loại câu hỏi:** {q['type']}")
                st.write(f"**Điểm:** {q['score']}")
                
                st.write("**Các đáp án:**")
                # Đảm bảo answers là list
                answers = q["answers"]
                if isinstance(answers, str):
                    try:
                        answers = json.loads(answers)
                    except:
                        answers = [answers]
                
                # Đảm bảo correct là list
                correct = q["correct"]
                if isinstance(correct, str):
                    try:
                        correct = json.loads(correct)
                    except:
                        try:
                            correct = [int(x.strip()) for x in correct.split(",")]
                        except:
                            correct = []
                
                for j, ans in enumerate(answers):
                    is_correct = (j + 1) in correct
                    st.write(f"- {j + 1}. {ans} {' ✅' if is_correct else ''}")
                
                # Thêm nút sửa và xóa
                col1, col2 = st.columns(2)
                
                if col1.button("✏️ Sửa", key=f"edit_q_{q['id']}"):
                    # Lấy dữ liệu câu hỏi từ database
                    question_data = get_question_by_id(q['id'])
                    if question_data:
                        st.session_state.editing_question = question_data
                        st.rerun()
                
                if col2.button("🗑️ Xóa", key=f"del_q_{q['id']}"):
                    st.session_state.question_to_delete = q
                    st.rerun()
                    
        if st.button("🔄 Làm mới danh sách", key="refresh_question_list"):
            st.session_state.db_questions = get_all_questions()
            st.rerun()

def edit_question():
    """Chức năng chỉnh sửa câu hỏi"""
    q = st.session_state.editing_question
    q_id = q['id']  # Lấy ID câu hỏi để tạo key duy nhất
    
    st.subheader(f"Chỉnh sửa câu hỏi #{q_id}")
    
    # Form chỉnh sửa câu hỏi
    edited_question = st.text_input("Nội dung câu hỏi", value=q["question"], key=f"edit_question_content_{q_id}")
    edited_type = st.selectbox("Loại câu hỏi", ["Checkbox", "Combobox"], 
                             index=["Checkbox", "Combobox"].index(q["type"]),
                             key=f"edit_question_type_{q_id}")
    edited_score = st.number_input("Số điểm", min_value=1, value=q["score"], key=f"edit_question_score_{q_id}")
    
    # Sao chép danh sách đáp án để có thể chỉnh sửa
    if "edited_answers" not in st.session_state:
        # Đảm bảo q["answers"] là danh sách
        if isinstance(q["answers"], str):
            try:
                # Nếu là JSON string, thử chuyển đổi thành list
                answers_list = json.loads(q["answers"])
                st.session_state.edited_answers = answers_list
            except:
                # Nếu không thể parse JSON, tạo list từ string
                st.session_state.edited_answers = [q["answers"]]
        else:
            # Nếu đã là list, sao chép nó
            st.session_state.edited_answers = list(q["answers"])
    
    # Sao chép đáp án đúng
    if "edited_correct" not in st.session_state:
        # Đảm bảo q["correct"] là danh sách
        if isinstance(q["correct"], str):
            try:
                # Nếu là JSON string, thử chuyển đổi thành list
                correct_list = json.loads(q["correct"])
                st.session_state.edited_correct = correct_list
            except:
                # Nếu không thể parse JSON, thử chuyển đổi từ dạng "1,2,3" thành [1,2,3]
                try:
                    st.session_state.edited_correct = [int(x.strip()) for x in q["correct"].split(",")]
                except:
                    st.session_state.edited_correct = []
        else:
            # Nếu đã là list, sao chép nó
            st.session_state.edited_correct = list(q["correct"])
    
    # Quản lý danh sách đáp án
    st.subheader("Danh sách đáp án")
    new_ans = st.text_input("Thêm đáp án mới", key=f"edit_new_ans_{q_id}")
    if st.button("➕ Thêm đáp án", key=f"edit_add_ans_{q_id}"):
        if new_ans:
            st.session_state.edited_answers.append(new_ans)
            st.rerun()
    
    # Hiển thị các đáp án hiện có
    for idx, ans in enumerate(st.session_state.edited_answers):
        col1, col2, col3 = st.columns([4, 1, 1])
        
        # Trường nhập liệu để sửa đáp án
        edited_ans = col1.text_input(f"Đáp án {idx+1}", value=ans, key=f"edit_ans_{q_id}_{idx}")
        st.session_state.edited_answers[idx] = edited_ans
        
        # Checkbox để đánh dấu đáp án đúng
        is_correct = (idx + 1) in st.session_state.edited_correct
        if col2.checkbox("✓", value=is_correct, key=f"edit_correct_{q_id}_{idx}"):
            if (idx + 1) not in st.session_state.edited_correct:
                st.session_state.edited_correct.append(idx + 1)
        else:
            if (idx + 1) in st.session_state.edited_correct:
                st.session_state.edited_correct.remove(idx + 1)
        
        # Nút xóa đáp án
        if col3.button("🗑️", key=f"edit_del_ans_{q_id}_{idx}"):
            st.session_state.edited_answers.pop(idx)
            # Cập nhật lại danh sách đáp án đúng
            st.session_state.edited_correct = [c for c in st.session_state.edited_correct if c != idx + 1]
            # Điều chỉnh lại các đáp án đúng có số thứ tự lớn hơn
            st.session_state.edited_correct = [c - 1 if c > idx + 1 else c for c in st.session_state.edited_correct]
            st.rerun()
    
    # Hiển thị mô tả về đáp án đúng 
    st.info(f"""
    **Hướng dẫn chọn đáp án đúng:**
    - Đối với câu hỏi Checkbox: Có thể chọn nhiều đáp án đúng.
    - Đối với câu hỏi Combobox: Chỉ nên chọn một đáp án đúng.
    - Đánh dấu ✓ cho các đáp án đúng.
    """)
    
    # Nút lưu và hủy
    col1, col2 = st.columns(2)
    
    if col1.button("💾 Lưu thay đổi", use_container_width=True, key=f"save_edit_{q_id}"):
        if not edited_question:
            st.error("Vui lòng nhập nội dung câu hỏi")
        elif not st.session_state.edited_answers:
            st.error("Vui lòng thêm ít nhất một đáp án")
        elif not st.session_state.edited_correct:
            st.error("Vui lòng chỉ định ít nhất một đáp án đúng")
        elif edited_type == "Combobox" and len(st.session_state.edited_correct) > 1:
            st.warning("Câu hỏi Combobox nên chỉ có 1 đáp án đúng. Hãy xem xét lại hoặc đổi thành Checkbox.")
            if st.button("Vẫn muốn lưu", key=f"force_save_edit_{q_id}"):
                save_edited_question(q_id, edited_question, edited_type, edited_score)
        else:
            save_edited_question(q_id, edited_question, edited_type, edited_score)
    
    if col2.button("❌ Hủy", use_container_width=True, key=f"cancel_edit_{q_id}"):
        # Xóa dữ liệu chỉnh sửa
        st.session_state.editing_question = None
        if "edited_answers" in st.session_state:
            del st.session_state.edited_answers
        if "edited_correct" in st.session_state:
            del st.session_state.edited_correct
        st.rerun()

def save_edited_question(q_id, edited_question, edited_type, edited_score):
    """Hàm hỗ trợ lưu câu hỏi đã chỉnh sửa"""
    # Cập nhật dữ liệu câu hỏi
    updated_data = {
        "question": edited_question,
        "type": edited_type,
        "score": edited_score,
        "answers": st.session_state.edited_answers,
        "correct": st.session_state.edited_correct
    }
    
    # Lưu thay đổi vào database
    if update_question(q_id, updated_data):
        # Xóa dữ liệu chỉnh sửa
        st.session_state.editing_question = None
        if "edited_answers" in st.session_state:
            del st.session_state.edited_answers
        if "edited_correct" in st.session_state:
            del st.session_state.edited_correct
        
        # Làm mới danh sách câu hỏi
        st.session_state.db_questions = get_all_questions()
        st.success("✅ Đã cập nhật câu hỏi thành công!")
        st.rerun()
    else:
        st.error("❌ Có lỗi xảy ra khi cập nhật câu hỏi!")

def delete_confirmation():
    """Hiển thị hộp xác nhận xóa câu hỏi"""
    q = st.session_state.question_to_delete
    q_id = q['id']
    
    st.warning(f"Bạn có chắc chắn muốn xóa câu hỏi sau đây?")
    st.info(f"Câu hỏi #{q_id}: {q['question']}")
    
    col1, col2 = st.columns(2)
    
    if col1.button("✅ Xác nhận xóa", use_container_width=True, key=f"confirm_delete_{q_id}"):
        if delete_question(q_id):
            # Làm mới danh sách câu hỏi
            st.session_state.db_questions = get_all_questions()
            st.session_state.question_to_delete = None
            st.success("✅ Đã xóa câu hỏi thành công!")
            st.rerun()
        else:
            st.error("❌ Có lỗi xảy ra khi xóa câu hỏi!")
    
    if col2.button("❌ Hủy", use_container_width=True, key=f"cancel_delete_{q_id}"):
        st.session_state.question_to_delete = None
        st.rerun()