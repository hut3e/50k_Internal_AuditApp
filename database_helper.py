import os
import json
import uuid
import streamlit as st
from datetime import datetime
from supabase import create_client
import supabase

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

def get_user(email, password, role=None):
    """Kiểm tra đăng nhập và trả về thông tin người dùng"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            print("DEBUG: Không thể kết nối đến Supabase")
            return None
        
        print(f"DEBUG: Đang thử đăng nhập - Email: {email}, Role: {role}")
        
        # Tạo query cơ bản
        query = supabase.table('users').select('*').eq('email', email).eq('password', password)
        
        # Thêm điều kiện role nếu có
        if role:
            query = query.eq('role', role)
        
        response = query.execute()
        
        print(f"DEBUG: Kết quả truy vấn: {len(response.data)} users found")
        
        if response.data:
            user = response.data[0]
            print(f"DEBUG: User found - {user['email']} ({user['role']})")
            
            # Cập nhật first_login nếu đây là lần đăng nhập đầu tiên
            if user.get('first_login', True):
                try:
                    supabase.table('users').update({'first_login': False}).eq('email', email).execute()
                    print(f"DEBUG: Đã cập nhật first_login = False cho {email}")
                except Exception as e:
                    print(f"DEBUG: Lỗi khi cập nhật first_login: {e}")
            
            return {
                "email": user["email"],
                "role": user["role"],
                "first_login": user.get("first_login", False),
                "full_name": user.get("full_name", ""),
                "class": user.get("class", "")
            }
        else:
            print("DEBUG: Không tìm thấy user phù hợp")
            
            # Debug thêm - kiểm tra xem có user nào với email này không
            email_check = supabase.table('users').select('*').eq('email', email).execute()
            if email_check.data:
                print(f"DEBUG: Tìm thấy user với email {email} nhưng:")
                for u in email_check.data:
                    print(f"  - Password match: {u['password'] == password}")
                    print(f"  - Role: {u['role']} (looking for: {role})")
                    print(f"  - Role match: {not role or u['role'] == role}")
            else:
                print(f"DEBUG: Không có user nào với email {email}")
            
            return None
            
    except Exception as e:
        print(f"DEBUG ERROR: {type(e).__name__}: {str(e)}")
        st.error(f"Lỗi khi đăng nhập: {e}")
        return None

def create_user_if_not_exists(email, full_name="", class_name="", role="student", password="default123"):
    """Tạo người dùng nếu chưa tồn tại trong bảng users"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            print("DEBUG: Không thể kết nối đến Supabase")
            return False
            
        # Kiểm tra xem user đã tồn tại chưa
        result = supabase.table("users").select("*").eq("email", email).execute()
        
        if result.data:
            print(f"DEBUG: User {email} đã tồn tại")
            return False
        
        # Tạo timestamp
        current_time = datetime.now().isoformat()
        
        # Tạo user mới với cấu trúc database đúng
        user_data = {
            "email": email,
            "password": password,
            "role": role,
            "first_login": True,  # Đánh dấu là lần đăng nhập đầu tiên
            "full_name": full_name,
            "class": class_name,
            "registration_date": current_time
        }
        
        print(f"DEBUG: Đang tạo user mới: {user_data}")
        
        # Thêm vào database
        result = supabase.table("users").insert(user_data).execute()
        
        if result.data:
            print(f"DEBUG: Tạo user thành công: {result.data}")
            return True
        else:
            print("DEBUG: Tạo user thất bại - không có dữ liệu trả về")
            return False
            
    except Exception as e:
        print(f"DEBUG ERROR khi tạo user: {type(e).__name__}: {str(e)}")
        st.error(f"Lỗi khi tạo người dùng: {e}")
        return False

def get_all_users(role=None):
    """Lấy danh sách tất cả người dùng, có thể lọc theo vai trò"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
            
        if role:
            response = supabase.table('users').select('*').eq('role', role).execute()
        else:
            response = supabase.table('users').select('*').execute()
        
        users = []
        for user in response.data:
            users.append({
                "email": user["email"],
                "role": user["role"],
                "first_login": user.get("first_login", False),
                "full_name": user.get("full_name", ""),
                "class": user.get("class", ""),
                "registration_date": user.get("registration_date")
            })
        return users
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách người dùng: {e}")
        return []

def debug_users_table():
    """Function debug để kiểm tra bảng users"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return "Không thể kết nối đến Supabase"
        
        # Lấy tất cả users
        result = supabase.table("users").select("*").execute()
        
        if result.data:
            return f"Tìm thấy {len(result.data)} users: {result.data}"
        else:
            return "Không có users nào trong database"
            
    except Exception as e:
        return f"Lỗi khi debug: {e}"

def update_user_first_login(email, first_login=False):
    """Cập nhật trạng thái first_login của user"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        result = supabase.table("users").update({"first_login": first_login}).eq("email", email).execute()
        return True if result.data else False
    except Exception as e:
        print(f"Lỗi khi cập nhật first_login: {e}")
        return False

# [Giữ nguyên các function khác như get_all_questions, save_submission, etc...]

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

def update_submission(submission_id, update_data):
    """Cập nhật thông tin bài nộp"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        result = supabase.table("submissions").update(update_data).eq("id", submission_id).execute()
        return True if result.data else False
    except Exception as e:
        print(f"Lỗi khi cập nhật submission: {str(e)}")
        return False

def calculate_score(responses, questions, essay_grades=None):
    """Tính điểm dựa trên đáp án và câu trả lời, bao gồm điểm câu hỏi tự luận"""
    total_score = 0
    
    for q in questions:
        q_id = str(q["id"])
        
        # Nếu là câu hỏi tự luận và có điểm đã chấm
        if q["type"] == "Essay" and essay_grades and q_id in essay_grades:
            # Lấy điểm từ essay_grades
            total_score += essay_grades[q_id]
        else:
            # Lấy câu trả lời của học viên
            student_answers = responses.get(q_id, [])
            
            # Kiểm tra đáp án
            if check_answer_correctness(student_answers, q):
                total_score += q["score"]
    
    return total_score

def calculate_total_score(submission, questions):
    """Tính tổng điểm cho một bài nộp - ĐÃ SỬA LỖI KIỂU DỮ LIỆU"""
    
    total_score = 0.0  # Bắt đầu với float
    
    # Xử lý responses
    responses = submission.get("responses", {})
    if isinstance(responses, str):
        try:
            responses = json.loads(responses)
        except:
            responses = {}
    
    # Xử lý essay_grades
    essay_grades = submission.get("essay_grades", {})
    if isinstance(essay_grades, str):
        try:
            essay_grades = json.loads(essay_grades)
        except:
            essay_grades = {}
    
    print(f"🔍 DEBUG - Tính điểm cho submission {submission.get('id', 'N/A')}")
    print(f"📝 Essay grades: {essay_grades}")
    
    # Tính điểm từng câu hỏi
    for q in questions:
        q_id = str(q.get("id", ""))
        q_type = q.get("type", "")
        q_score = q.get("score", 0)
        
        if q_type == "Essay":
            # ✅ Đối với câu tự luận: LẤY ĐIỂM TỪ essay_grades
            essay_score = essay_grades.get(q_id, 0)
            # 🔧 SỬA: Đảm bảo là số
            try:
                essay_score = float(essay_score)
            except (ValueError, TypeError):
                essay_score = 0.0
            
            total_score += essay_score
            print(f"📝 Câu {q_id} (Essay): {essay_score} điểm")
            
        else:
            # ✅ Đối với câu trắc nghiệm: KIỂM TRA ĐÚNG/SAI
            student_answers = responses.get(q_id, [])
            if check_answer_correctness(student_answers, q):
                total_score += float(q_score)  # 🔧 Convert sang float
                print(f"✅ Câu {q_id} ({q_type}): {q_score} điểm (ĐÚNG)")
            else:
                print(f"❌ Câu {q_id} ({q_type}): 0 điểm (SAI)")
    
    # 🔧 SỬA: CONVERT SANG INTEGER TRƯỚC KHI TRẢ VỀ
    final_score = int(round(total_score))  # Làm tròn và convert sang int
    print(f"🎯 TỔNG ĐIỂM CUỐI CÙNG: {total_score} → {final_score} (integer)")
    
    return final_score

def check_answer_correctness(student_answers, question):
    """Kiểm tra đáp án có đúng không - đã sửa lỗi xử lý dữ liệu"""
    
    # Nếu câu trả lời trống, không đúng
    if not student_answers:
        return False
    
    # Đảm bảo question["answers"] là list
    q_answers = question.get("answers", [])
    if isinstance(q_answers, str):
        try:
            q_answers = json.loads(q_answers)
        except:
            q_answers = [q_answers]
    
    # Đảm bảo question["correct"] là list
    q_correct = question.get("correct", [])
    if isinstance(q_correct, str):
        try:
            q_correct = json.loads(q_correct)
        except:
            try:
                q_correct = [int(x.strip()) for x in q_correct.split(",")]
            except:
                q_correct = []
    
    # Đối với câu hỏi Essay
    if question.get("type") == "Essay":
        return bool(student_answers and student_answers[0].strip())
    
    # Đối với câu hỏi Combobox (chỉ chọn một)
    elif question.get("type") == "Combobox":
        if len(student_answers) == 1:
            answer_text = student_answers[0]
            try:
                answer_index = q_answers.index(answer_text) + 1
                return answer_index in q_correct
            except (ValueError, IndexError):
                return False
        return False
    
    # Đối với câu hỏi Checkbox (nhiều lựa chọn)
    elif question.get("type") == "Checkbox":
        selected_indices = []
        for ans in student_answers:
            try:
                answer_index = q_answers.index(ans) + 1
                selected_indices.append(answer_index)
            except (ValueError, IndexError):
                continue
        
        return set(selected_indices) == set(q_correct)
    
    return False

def get_user_submissions(email):
    """Lấy tất cả bài làm của một học viên theo email"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
            
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

def get_submission_statistics():
    """Lấy thống kê về các bài nộp"""
    try:
        supabase = get_supabase_client()
        if not supabase:
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

def save_submission(email, responses):
    """Lưu bài làm của học viên và tính điểm"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
            
        # Lấy danh sách câu hỏi
        questions = get_all_questions()
        
        # Tính điểm dựa trên câu trả lời (không tính điểm câu tự luận lúc này)
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
            "timestamp": current_time,
            "essay_grades": json.dumps({}),  # Thêm trường lưu điểm câu hỏi tự luận
            "essay_comments": json.dumps({})  # Thêm trường lưu nhận xét câu hỏi tự luận
        }
        
        # Lưu vào database
        result = supabase.table("submissions").insert(submission_data).execute()
        
        if result.data:
            # Trả về kết quả bài làm
            return {
                "id": new_id,
                "user_email": email,
                "responses": responses,
                "score": score,
                "timestamp": current_time,
                "essay_grades": {},
                "essay_comments": {}
            }
        
        return None
    except Exception as e:
        st.error(f"Lỗi khi lưu bài làm: {e}")
        return None

def save_question(question_data):
    """Lưu câu hỏi mới vào database"""
    try:
        supabase = get_supabase_client()
        if not supabase:
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
            return False
            
        result = supabase.table("questions").delete().eq("id", question_id).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"Lỗi khi xóa câu hỏi: {e}")
        return False
    
def get_all_users(role=None):
    """Lấy tất cả users từ database với role cụ thể"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        if role:
            result = supabase.table("users").select("*").eq("role", role).execute()
        else:
            result = supabase.table("users").select("*").execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Lỗi khi lấy users: {str(e)}")
        return []

def get_user_submissions(email):
    """Lấy tất cả bài nộp của một user"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        result = supabase.table("submissions").select("*").eq("user_email", email).order("timestamp", desc=True).execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Lỗi khi lấy submissions của {email}: {str(e)}")
        return []

def get_all_questions():
    """Lấy tất cả câu hỏi từ database"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        result = supabase.table("questions").select("*").order("id").execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Lỗi khi lấy questions: {str(e)}")
        return []


def debug_scoring_system():
    """Hàm debug để kiểm tra hệ thống tính điểm"""
    print("=== KIỂM TRA HỆ THỐNG TÍNH ĐIỂM ===")
    
    # Test data
    test_question_mc = {
        "id": 1,
        "type": "Checkbox",
        "answers": ["A", "B", "C", "D"],
        "correct": [1, 3],
        "score": 5
    }
    
    test_question_essay = {
        "id": 2,
        "type": "Essay",
        "score": 15
    }
    
    test_submission = {
        "id": "test_001",
        "responses": {
            "1": ["A", "C"],  # Đúng
            "2": ["Câu trả lời tự luận"]
        },
        "essay_grades": {
            "2": 10  # 10/15 điểm
        }
    }
    
    questions = [test_question_mc, test_question_essay]
    total = calculate_total_score(test_submission, questions)
    expected = 5 + 10  # 15 điểm
    
    print(f"Kết quả: {total}, Mong đợi: {expected}")
    print(f"Status: {'✅ PASS' if total == expected else '❌ FAIL'}")
    print("=== KẾT THÚC KIỂM TRA ===")


if __name__ == "__main__":
    debug_scoring_system()
