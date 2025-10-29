import os
import json
import uuid
import streamlit as st
from datetime import datetime
from supabase import create_client
import supabase
import traceback

def check_supabase_config():
    """Kiểm tra cấu hình Supabase"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        return False, "SUPABASE_URL và SUPABASE_KEY chưa được thiết lập."
    
    if not supabase_url.startswith("https://"):
        return False, "SUPABASE_URL không hợp lệ. URL phải bắt đầu bằng https://"
    
    return True, "Cấu hình Supabase hợp lệ."

def get_supabase_client():
    """Tạo và trả về Supabase client"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    # Kiểm tra biến môi trường đã được thiết lập
    if not supabase_url or not supabase_key:
        st.error("Biến môi trường SUPABASE_URL và SUPABASE_KEY chưa được thiết lập.")
        return None
    
    try:
        # Tạo Supabase client
        supabase = create_client(supabase_url, supabase_key)
        return supabase
    except Exception as e:
        st.error(f"Không thể kết nối đến Supabase: {e}")
        return None

def test_supabase_connection():
    """Kiểm tra kết nối với Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "Không thể tạo kết nối Supabase."
    
    try:
        # Thử thực hiện một truy vấn đơn giản
        result = supabase.table("questions").select("count", count="exact").execute()
        return True, f"Kết nối thành công. Số lượng câu hỏi: {result.count or 0}"
    except Exception as e:
        return False, f"Lỗi khi truy vấn: {str(e)}"

def get_all_questions():
    """Lấy tất cả câu hỏi từ database"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
            
        result = supabase.table("questions").select("*").order("id").execute()
        if result.data:
            # Đảm bảo dữ liệu được trả về đúng định dạng
            for q in result.data:
                # Kiểm tra và chuyển đổi dữ liệu answers
                if isinstance(q["answers"], str):
                    try:
                        q["answers"] = json.loads(q["answers"])
                    except:
                        q["answers"] = [q["answers"]]
                
                # Kiểm tra và chuyển đổi dữ liệu correct
                if isinstance(q["correct"], str):
                    try:
                        q["correct"] = json.loads(q["correct"])
                    except:
                        try:
                            q["correct"] = [int(x.strip()) for x in q["correct"].split(",")]
                        except:
                            q["correct"] = []
            return result.data
        return []
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách câu hỏi: {e}")
        return []

def get_question_by_id(question_id):
    """Lấy thông tin câu hỏi theo ID"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
            
        result = supabase.table("questions").select("*").eq("id", question_id).execute()
        if result.data:
            q = result.data[0]
            # Kiểm tra và chuyển đổi dữ liệu answers
            if isinstance(q["answers"], str):
                try:
                    q["answers"] = json.loads(q["answers"])
                except:
                    q["answers"] = [q["answers"]]
            
            # Kiểm tra và chuyển đổi dữ liệu correct
            if isinstance(q["correct"], str):
                try:
                    q["correct"] = json.loads(q["correct"])
                except:
                    try:
                        q["correct"] = [int(x.strip()) for x in q["correct"].split(",")]
                    except:
                        q["correct"] = []
            return q
        return None
    except Exception as e:
        st.error(f"Lỗi khi lấy câu hỏi: {e}")
        return None

def save_question(question_data):
    """Lưu câu hỏi mới vào database"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return False
            
        # Kiểm tra định dạng dữ liệu trước khi lưu
        data_to_save = question_data.copy()
        
        # Chuyển đổi answers thành JSON nếu cần
        if isinstance(data_to_save["answers"], list):
            data_to_save["answers"] = json.dumps(data_to_save["answers"])
        
        # Chuyển đổi correct thành JSON nếu cần
        if isinstance(data_to_save["correct"], list):
            data_to_save["correct"] = json.dumps(data_to_save["correct"])
        
        # Thêm vào database
        result = supabase.table("questions").insert(data_to_save).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"Lỗi khi lưu câu hỏi: {e}")
        return False

def update_question(question_id, updated_data):
    """Cập nhật thông tin câu hỏi theo ID"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return False
            
        # Kiểm tra định dạng dữ liệu trước khi lưu
        data_to_save = updated_data.copy()
        
        # Chuyển đổi answers thành JSON nếu cần
        if isinstance(data_to_save["answers"], list):
            data_to_save["answers"] = json.dumps(data_to_save["answers"])
        
        # Chuyển đổi correct thành JSON nếu cần
        if isinstance(data_to_save["correct"], list):
            data_to_save["correct"] = json.dumps(data_to_save["correct"])
        
        # Cập nhật vào database
        result = supabase.table("questions").update(data_to_save).eq("id", question_id).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"Lỗi khi cập nhật câu hỏi: {e}")
        return False

def delete_question(question_id):
    """Xóa câu hỏi theo ID"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return False
            
        result = supabase.table("questions").delete().eq("id", question_id).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"Lỗi khi xóa câu hỏi: {e}")
        return False

def save_submission(email, responses):
    """Lưu bài làm của học viên và tính điểm"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return None
            
        # Lấy danh sách câu hỏi
        questions = get_all_questions()
        
        # Tính điểm dựa trên câu trả lời
        score = calculate_score(responses, questions)
        
        # Tìm id lớn nhất hiện tại
        try:
            max_id_result = supabase.table("submissions").select("id").order("id", desc=True).limit(1).execute()
            if max_id_result.data:
                new_id = max_id_result.data[0]["id"] + 1
            else:
                new_id = 1
        except Exception as e:
            st.error(f"Lỗi khi tìm id lớn nhất: {e}")
            new_id = 1
        
        # Tạo timestamp đúng định dạng ISO cho PostgreSQL
        current_time = datetime.now().isoformat()
        
        # Dữ liệu cần lưu
        submission_data = {
            "id": new_id,
            "user_email": email,
            "responses": json.dumps(responses),
            "score": score,
            "timestamp": current_time  # Sử dụng ISO format thay vì Unix timestamp
        }
        
        # Lưu vào database
        result = supabase.table("submissions").insert(submission_data).execute()
        
        if result.data:
            # Trả về kết quả bài làm
            return {
                "id": new_id,
                "email": email,
                "responses": responses,
                "score": score,
                "timestamp": current_time
            }
        
        return None
    except Exception as e:
        st.error(f"Lỗi khi lưu bài làm: {e}")
        return None

def calculate_score(responses, questions):
    """Tính điểm dựa trên đáp án và câu trả lời"""
    total_score = 0
    
    for q in questions:
        q_id = str(q["id"])
        
        # Lấy câu trả lời của học viên
        student_answers = responses.get(q_id, [])
        
        # Kiểm tra đáp án
        if check_answer_correctness(student_answers, q):
            total_score += q["score"]
    
    return total_score

def check_answer_correctness(student_answers, question):
    """Kiểm tra đáp án có đúng không.
    - Checkbox: so khớp tập chỉ số đáp án
    - Combobox: so khớp một đáp án
    - Essay: tính là đúng nếu có nội dung (không rỗng)
    """
    if not student_answers:
        return False

    q_type = question.get("type")

    # Tự luận: chỉ cần có nội dung
    if q_type == "Essay":
        return bool(student_answers) and isinstance(student_answers[0], str) and student_answers[0].strip() != ""

    # Combobox: chọn một
    if q_type == "Combobox":
        if len(student_answers) == 1:
            answer_text = student_answers[0]
            answers = question.get("answers", [])
            correct = question.get("correct", [])
            answer_index = answers.index(answer_text) + 1 if answer_text in answers else -1
            return answer_index in correct
        return False

    # Checkbox: nhiều lựa chọn
    if q_type == "Checkbox":
        answers = question.get("answers", [])
        correct = set(question.get("correct", []))
        selected_indices = []
        for ans in student_answers:
            if ans in answers:
                selected_indices.append(answers.index(ans) + 1)
        return set(selected_indices) == correct

    return False

# mới thêm code here
def get_user(email, password):
    """Kiểm tra đăng nhập và trả về thông tin người dùng"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return None
        
        # Kiểm tra đăng nhập: email và password phải khớp
        response = supabase.table('users').select('*').eq('email', email).eq('password', password).execute()
        
        if response.data:
            user = response.data[0]
            return {
                "email": user["email"],
                "role": user["role"],
                "first_login": user.get("first_login", False),
                "full_name": user.get("full_name", ""),
                "class": user.get("class", "")
            }
        return None
    except Exception as e:
        print(f"Lỗi khi đăng nhập: {type(e).__name__}: {str(e)}")
        return None
    
def get_user_submissions(email):
    """Lấy tất cả bài làm của một học viên theo email"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return []
            
        # Sửa từ "email" thành "user_email"
        result = supabase.table("submissions").select("*").eq("user_email", email).order("timestamp", desc=True).execute()
        
        if result.data:
            submissions = []
            for s in result.data:
                # Chuyển đổi responses từ JSON string thành dict
                if isinstance(s["responses"], str):
                    try:
                        s["responses"] = json.loads(s["responses"])
                    except:
                        s["responses"] = {}
                
                submissions.append(s)
            
            return submissions
        
        return []
    except Exception as e:
        st.error(f"Lỗi khi lấy bài làm của học viên: {e}")
        return []

def get_all_submissions():
    """Lấy tất cả bài làm từ tất cả học viên"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return []
        
        # Lấy tất cả bài nộp
        result = supabase.table("submissions").select("*").order("timestamp", desc=True).execute()
        
        if result.data:
            submissions = []
            for s in result.data:
                # Chuyển đổi responses từ JSON string thành dict
                if isinstance(s["responses"], str):
                    try:
                        s["responses"] = json.loads(s["responses"])
                    except:
                        s["responses"] = {}
                
                submissions.append(s)
            
            return submissions
        
        return []
    except Exception as e:
        st.error(f"Lỗi khi lấy tất cả bài làm: {e}")
        print(f"Chi tiết lỗi: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return []

def get_submission_statistics():
    """Lấy thống kê về các bài nộp"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return None
            
        # Lấy tất cả bài nộp
        submissions_result = supabase.table("submissions").select("*").execute()
        submissions = submissions_result.data if submissions_result.data else []
        
        # Lấy danh sách câu hỏi
        questions = get_all_questions()
        
        # Tính số lượng bài nộp
        total_submissions = len(submissions)
        
        if total_submissions == 0:
            return {
                "total_submissions": 0,
                "student_count": 0,
                "avg_score": 0,
                "avg_percentage": 0,
                "total_possible_score": sum(q["score"] for q in questions),
                "question_stats": {},
                "daily_counts": {}
            }
        
        # Tính điểm trung bình
        total_possible_score = sum(q["score"] for q in questions)
        avg_score = sum(s["score"] for s in submissions) / total_submissions if total_submissions > 0 else 0
        avg_percentage = (avg_score / total_possible_score * 100) if total_possible_score > 0 else 0
        
        # Tính số lượng học viên đã nộp bài
        # Sửa từ "email" thành "user_email"
        unique_students = set(s["user_email"] for s in submissions)
        student_count = len(unique_students)
        
        # Tính tỷ lệ đúng sai cho từng câu hỏi
        question_stats = {}
        for q in questions:
            q_id = str(q["id"])
            correct_count = 0
            total_answers = 0
            
            for s in submissions:
                # Chuyển đổi responses từ JSON string thành dict nếu cần
                if isinstance(s["responses"], str):
                    try:
                        responses = json.loads(s["responses"])
                    except:
                        responses = {}
                else:
                    responses = s["responses"]
                
                if q_id in responses:
                    total_answers += 1
                    student_answers = responses[q_id]
                    if check_answer_correctness(student_answers, q):
                        correct_count += 1
            
            correct_percentage = (correct_count / total_answers * 100) if total_answers > 0 else 0
            
            question_stats[q_id] = {
                "question": q["question"],
                "total_answers": total_answers,
                "correct_count": correct_count,
                "correct_percentage": correct_percentage
            }
        
        # Thống kê theo thời gian
        # Chuyển đổi timestamp sang datetime cho dễ đọc
        for s in submissions:
            # Nếu timestamp đã ở dạng datetime (từ PostgreSQL)
            if isinstance(s["timestamp"], (str, datetime)):
                if isinstance(s["timestamp"], str):
                    try:
                        s["datetime"] = datetime.fromisoformat(s["timestamp"].replace("Z", "+00:00"))
                    except:
                        s["datetime"] = datetime.now()  # Giá trị mặc định nếu không thể parse
                else:
                    s["datetime"] = s["timestamp"]
            else:
                # Nếu vẫn còn lưu dạng Unix timestamp (dữ liệu cũ)
                try:
                    s["datetime"] = datetime.fromtimestamp(s["timestamp"])
                except:
                    s["datetime"] = datetime.now()
        
        # Nhóm theo ngày
        submissions_by_date = {}
        for s in submissions:
            date_str = s["datetime"].strftime("%Y-%m-%d")
            if date_str not in submissions_by_date:
                submissions_by_date[date_str] = []
            submissions_by_date[date_str].append(s)
        
        # Tính số lượng bài nộp theo ngày
        daily_counts = {date: len(subs) for date, subs in submissions_by_date.items()}
        
        # Kết quả thống kê
        stats = {
            "total_submissions": total_submissions,
            "student_count": student_count,
            "avg_score": avg_score,
            "avg_percentage": avg_percentage,
            "total_possible_score": total_possible_score,
            "question_stats": question_stats,
            "daily_counts": daily_counts
        }
        
        return stats
    except Exception as e:
        st.error(f"Lỗi khi lấy thống kê bài nộp: {e}")
        return None
    
def get_all_users(role=None):
    """Lấy danh sách tất cả người dùng, có thể lọc theo vai trò
    
    Args:
        role: None để lấy tất cả, string cho một role, hoặc list cho nhiều roles
              Các role hợp lệ: "Học viên", "student", "admin", "admin"
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return []
        
        # Lấy tất cả users từ database
        try:
            if role is None:
                # Lấy tất cả users
                response = supabase.table('users').select('*').execute()
            elif isinstance(role, list):
                # Lọc theo nhiều roles (OR condition)
                if len(role) == 1:
                    response = supabase.table('users').select('*').eq('role', role[0]).execute()
                else:
                    # Sử dụng .in_() nếu có nhiều roles, nếu không hỗ trợ thì query từng cái
                    query = supabase.table('users').select('*')
                    # Thử dùng .in_() nếu có, nếu không thì query riêng rồi merge
                    try:
                        response = query.in_('role', role).execute()
                    except:
                        # Fallback: query từng role rồi merge
                        all_data = []
                        for r in role:
                            try:
                                result = supabase.table('users').select('*').eq('role', r).execute()
                                if result.data:
                                    all_data.extend(result.data)
                            except:
                                pass
                        # Loại bỏ duplicate theo email
                        seen_emails = set()
                        unique_data = []
                        for item in all_data:
                            email = item.get('email')
                            if email and email not in seen_emails:
                                seen_emails.add(email)
                                unique_data.append(item)
                        response = type('obj', (object,), {'data': unique_data})()
            else:
                # Lọc theo một role
                response = supabase.table('users').select('*').eq('role', role).execute()
        except Exception as query_error:
            print(f"Lỗi query Supabase: {query_error}")
            st.error(f"Lỗi khi truy vấn bảng 'users': {str(query_error)}")
            return []
        
        if not response.data:
            print(f"Không có dữ liệu users trong database (role={role})")
            return []
        
        users = []
        for user in response.data:
            try:
                users.append({
                    "email": user.get("email", ""),
                    "role": user.get("role", ""),
                    "full_name": user.get("full_name", "") or user.get("fullname", "") or "",
                    "class": user.get("class", "") or user.get("class_name", "") or "",
                    "registration_date": user.get("registration_date") or user.get("created_at")
                })
            except Exception as user_error:
                print(f"Lỗi khi xử lý user {user.get('email', 'N/A')}: {user_error}")
                continue
        
        print(f"Đã load {len(users)} users từ database (role={role})")
        return users
    except Exception as e:
        print(f"Error getting users: {e}")
        import traceback
        traceback.print_exc()
        st.error(f"Lỗi khi lấy danh sách người dùng: {e}")
        return []

def get_all_students():
    """Lấy tất cả users có role là "Học viên", "student", hoặc "admin" để hiển thị trong báo cáo"""
    return get_all_users(role=["Học viên", "student", "admin"])

def create_user_if_not_exists(email, password, full_name="", role="Học viên", class_name=""):
    """Tạo người dùng mới nếu chưa tồn tại. Trả về True nếu tạo thành công, False nếu lỗi"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return False
        
        # Kiểm tra xem user đã tồn tại chưa
        existing_user = supabase.table('users').select('email').eq('email', email).execute()
        
        if existing_user.data:
            # Người dùng đã tồn tại
            return False  # Trả về False để báo đã tồn tại
        
        # Tạo người dùng mới
        user_data = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
            "class": class_name,
            "registration_date": datetime.now().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            return True
        return False
    except Exception as e:
        st.error(f"Lỗi khi tạo người dùng: {e}")
        return False
