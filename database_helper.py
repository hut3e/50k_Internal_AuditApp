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

def get_user(email, password):
    """Kiểm tra đăng nhập và trả về thông tin người dùng"""
    try:
        # Sửa lỗi: Lấy client Supabase đúng cách
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return None
            
        # Print debug info to Streamlit log
        st.write(f"DEBUG: Attempting login for: {email} with password: {password}")
        print(f"DEBUG: Attempting login for: {email} with password: {password}")
        
        # First check if any users exist
        all_users = supabase.table('users').select('*').execute()
        st.write(f"DEBUG: Total users in database: {len(all_users.data)}")
        print(f"DEBUG: Total users in database: {len(all_users.data)}")
        for u in all_users.data:
            st.write(f"DEBUG: Found user: {u['email']} with role {u['role']}")
            print(f"DEBUG: Found user: {u['email']} with role {u['role']}")
        
        # Now try to log in
        response = supabase.table('users').select('*').eq('email', email).eq('password', password).execute()
        st.write(f"DEBUG: Login query returned {len(response.data)} results")
        print(f"DEBUG: Login query returned {len(response.data)} results")
        
        if response.data:
            user = response.data[0]
            st.write(f"DEBUG: User found: {user['email']} with role {user['role']}")
            print(f"DEBUG: User found: {user['email']} with role {user['role']}")
            return {
                "email": user["email"],
                "role": user["role"],
                "first_login": user.get("first_login", False),
                "full_name": user.get("full_name", ""),
                "class": user.get("class", "")
            }
        else:
            # Just check if user exists
            user_check = supabase.table('users').select('*').eq('email', email).execute()
            if user_check.data:
                st.write(f"DEBUG: User exists but password is wrong. Should be: {user_check.data[0]['password']}")
                print(f"DEBUG: User exists but password is wrong. Should be: {user_check.data[0]['password']}")
            else:
                st.write(f"DEBUG: No user found with email: {email}")
                print(f"DEBUG: No user found with email: {email}")
            return None
    except Exception as e:
        st.write(f"DEBUG ERROR: {type(e).__name__}: {str(e)}")
        print(f"DEBUG ERROR: {type(e).__name__}: {str(e)}")
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
    """Lấy danh sách tất cả người dùng, có thể lọc theo vai trò"""
    try:
        # Sửa lỗi: Lấy client Supabase đúng cách
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
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
                "full_name": user.get("full_name", ""),
                "class": user.get("class", ""),
                "registration_date": user.get("registration_date")
            })
        return users
    except Exception as e:
        print(f"Error getting users: {e}")
        st.error(f"Lỗi khi lấy danh sách người dùng: {e}")
        return []

def register_user(email, password, full_name, class_name, role="student"):
    """Đăng ký người dùng mới"""
    try:
        # Lấy Supabase client
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return False, "Không thể kết nối đến cơ sở dữ liệu."
        
        # Kiểm tra xem email đã tồn tại chưa
        user_check = supabase.table('users').select('*').eq('email', email).execute()
        if user_check.data:
            return False, "Email này đã được sử dụng. Vui lòng chọn email khác hoặc đăng nhập."
        
        # Tạo timestamp đúng định dạng ISO cho PostgreSQL
        registration_date = datetime.now().isoformat()
        
        # Chuẩn bị dữ liệu người dùng
        user_data = {
            "email": email,
            "password": password,  # Lưu ý: trong ứng dụng thực tế, nên mã hóa mật khẩu trước khi lưu
            "full_name": full_name,
            "class": class_name,
            "role": role,
            "first_login": True,
            "registration_date": registration_date
        }
        
        # Lưu vào database
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            return True, "Đăng ký thành công. Bạn có thể đăng nhập ngay bây giờ."
        else:
            return False, "Có lỗi xảy ra khi đăng ký. Vui lòng thử lại sau."
    except Exception as e:
        print(f"Lỗi đăng ký người dùng: {e}")
        st.error(f"Lỗi đăng ký người dùng: {e}")
        return False, f"Lỗi: {str(e)}"

def update_password(email, old_password, new_password):
    """Cập nhật mật khẩu người dùng"""
    try:
        # Lấy Supabase client
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return False, "Không thể kết nối đến cơ sở dữ liệu."
        
        # Kiểm tra xem email và mật khẩu cũ có đúng không
        user_check = supabase.table('users').select('*').eq('email', email).eq('password', old_password).execute()
        if not user_check.data:
            return False, "Mật khẩu cũ không đúng."
        
        # Cập nhật mật khẩu mới
        result = supabase.table('users').update({"password": new_password}).eq('email', email).execute()
        
        if result.data:
            return True, "Cập nhật mật khẩu thành công."
        else:
            return False, "Có lỗi xảy ra khi cập nhật mật khẩu. Vui lòng thử lại sau."
    except Exception as e:
        print(f"Lỗi cập nhật mật khẩu: {e}")
        st.error(f"Lỗi cập nhật mật khẩu: {e}")
        return False, f"Lỗi: {str(e)}"

def update_user_profile(email, full_name=None, class_name=None):
    """Cập nhật thông tin cá nhân của người dùng"""
    try:
        # Lấy Supabase client
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return False, "Không thể kết nối đến cơ sở dữ liệu."
        
        # Chuẩn bị dữ liệu cần cập nhật
        update_data = {}
        if full_name:
            update_data["full_name"] = full_name
        if class_name:
            update_data["class"] = class_name
        
        # Nếu không có dữ liệu cần cập nhật
        if not update_data:
            return False, "Không có thông tin mới để cập nhật."
        
        # Cập nhật thông tin
        result = supabase.table('users').update(update_data).eq('email', email).execute()
        
        if result.data:
            return True, "Cập nhật thông tin thành công."
        else:
            return False, "Có lỗi xảy ra khi cập nhật thông tin. Vui lòng thử lại sau."
    except Exception as e:
        print(f"Lỗi cập nhật thông tin: {e}")
        st.error(f"Lỗi cập nhật thông tin: {e}")
        return False, f"Lỗi: {str(e)}"

def check_email_exists(email):
    """Kiểm tra xem email đã tồn tại trong hệ thống hay chưa"""
    try:
        # Lấy Supabase client
        supabase = get_supabase_client()
        if not supabase:
            st.error("Không thể kết nối đến Supabase.")
            return True, "Không thể kết nối đến cơ sở dữ liệu."
        
        # Kiểm tra email
        result = supabase.table('users').select('*').eq('email', email).execute()
        
        # Trả về True nếu email đã tồn tại
        return len(result.data) > 0, "Email đã tồn tại" if len(result.data) > 0 else "Email chưa tồn tại"
    except Exception as e:
        print(f"Lỗi kiểm tra email: {e}")
        st.error(f"Lỗi kiểm tra email: {e}")
        return True, f"Lỗi: {str(e)}"  # Trả về True để ngăn đăng ký trong trường hợp có lỗi
