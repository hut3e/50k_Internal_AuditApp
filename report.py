import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import numpy as np
import json
import sys
import traceback
import os

from docx.shared import Inches
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

# Thêm vào đầu file - Thay đổi sang fpdf2 thay vì fpdf
from fpdf import FPDF
# Thêm thư viện để hỗ trợ Unicode
import pkg_resources

from database_helper import get_supabase_client

# Nhập các thư viện cho xuất file
try:
    from docx import Document
    from docx.shared import Pt, RGBColor
except ImportError:
    # Hiển thị thông báo chỉ khi đang chạy trong Streamlit
    if 'streamlit' in sys.modules:
        st.warning("Module python-docx không được cài đặt. Tính năng xuất DOCX sẽ không hoạt động.")

# Sử dụng WD_ALIGN_PARAGRAPH nếu có thể, nếu không tạo class thay thế
try:
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    class WD_ALIGN_PARAGRAPH:
        CENTER = 1
        RIGHT = 2
        LEFT = 0

# Hỗ trợ xuất PDF với reportlab nếu cần
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    # Hiển thị thông báo chỉ khi đang chạy trong Streamlit
    if 'streamlit' in sys.modules:
        st.warning("Module reportlab không được cài đặt. Tính năng xuất PDF sẽ bị hạn chế.")

# ===============================
# CÁC HÀM KẾT NỐI DATABASE
# ===============================

def check_answer_correctness(user_ans, q):
    """Kiểm tra đáp án có đúng không - HOÀN THIỆN"""
    try:
        # Nếu câu trả lời trống, không đúng
        if not user_ans:
            return False
        
        # Đảm bảo q["answers"] là list
        q_answers = q.get("answers", [])
        if isinstance(q_answers, str):
            try:
                q_answers = json.loads(q_answers)
            except:
                q_answers = [q_answers]
        
        # Đảm bảo q["correct"] là list
        q_correct = q.get("correct", [])
        if isinstance(q_correct, str):
            try:
                q_correct = json.loads(q_correct)
            except:
                try:
                    q_correct = [int(x.strip()) for x in q_correct.split(",")]
                except:
                    q_correct = []
        
        # Đối với câu hỏi Essay
        if q.get("type") == "Essay":
            # Essay được coi là đúng nếu có trả lời (không rỗng)
            if isinstance(user_ans, list) and len(user_ans) > 0:
                return bool(user_ans[0] and str(user_ans[0]).strip())
            return bool(user_ans and str(user_ans).strip())
        
        # Đối với câu hỏi Combobox (chỉ chọn một)
        elif q.get("type") == "Combobox":
            if len(user_ans) == 1:
                answer_text = user_ans[0]
                try:
                    answer_index = q_answers.index(answer_text) + 1
                    return answer_index in q_correct
                except (ValueError, IndexError):
                    return False
            return False
        
        # Đối với câu hỏi Checkbox (nhiều lựa chọn)
        elif q.get("type") == "Checkbox":
            selected_indices = []
            for ans in user_ans:
                try:
                    answer_index = q_answers.index(ans) + 1
                    selected_indices.append(answer_index)
                except (ValueError, IndexError):
                    continue
            
            # So sánh tập hợp để không phụ thuộc thứ tự
            return set(selected_indices) == set(q_correct)
        
        return False
        
    except Exception as e:
        print(f"Lỗi check_answer_correctness: {str(e)}")
        return False

def get_all_questions():
    """Lấy tất cả câu hỏi từ database - HOÀN THIỆN"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            #print("❌ Không thể kết nối Supabase trong get_all_questions")
            return []
        
        # Lấy tất cả câu hỏi, sắp xếp theo ID
        result = supabase.table("questions").select("*").order("id").execute()
        
        if result.data:
            #print(f"✅ Đã lấy {len(result.data)} câu hỏi từ database")
            
            # Xử lý dữ liệu để đảm bảo format đúng
            processed_questions = []
            for q in result.data:
                try:
                    # Đảm bảo answers là list
                    if isinstance(q.get("answers"), str):
                        try:
                            q["answers"] = json.loads(q["answers"])
                        except:
                            q["answers"] = [q["answers"]]
                    
                    # Đảm bảo correct là list
                    if isinstance(q.get("correct"), str):
                        try:
                            q["correct"] = json.loads(q["correct"])
                        except:
                            try:
                                q["correct"] = [int(x.strip()) for x in q["correct"].split(",")]
                            except:
                                q["correct"] = []
                    
                    # Đảm bảo score là số
                    if isinstance(q.get("score"), str):
                        try:
                            q["score"] = int(q["score"])
                        except:
                            q["score"] = 0
                    
                    processed_questions.append(q)
                    
                except Exception as e:
                    print(f"Lỗi xử lý câu hỏi ID {q.get('id', 'N/A')}: {str(e)}")
                    continue
            
            return processed_questions
        else:
            print("⚠️ Không có câu hỏi nào trong database")
            return []
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy questions: {str(e)}")
        traceback.print_exc()
        return []

def get_all_users(role=None):
    """Lấy tất cả users từ database với role cụ thể - HOÀN THIỆN"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            print("❌ Không thể kết nối Supabase trong get_all_users")
            return []
        
        # Tạo query với hoặc không có filter role
        if role:
            result = supabase.table("users").select("*").eq("role", role).execute()
            print(f"🔍 Đang tìm users với role: {role}")
        else:
            result = supabase.table("users").select("*").execute()
            print("🔍 Đang lấy tất cả users")
        
        if result.data:
            print(f"✅ Đã lấy {len(result.data)} users từ database")
            
            # Log thông tin users để debug  
            for user in result.data[:3]:  # Chỉ log 3 user đầu
                print(f"   - {user.get('email', 'N/A')} ({user.get('role', 'N/A')}) - {user.get('full_name', 'N/A')}")
            
            return result.data
        else:
            print(f"⚠️ Không tìm thấy users nào" + (f" với role {role}" if role else ""))
            return []
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy users: {str(e)}")
        traceback.print_exc()
        return []

def get_user_submissions(email):
    """Lấy tất cả bài nộp của một user - HOÀN THIỆN"""
    try:
        if not email:
            print("❌ Email không hợp lệ trong get_user_submissions")
            return []
            
        supabase = get_supabase_client()
        if not supabase:
            print("❌ Không thể kết nối Supabase trong get_user_submissions")
            return []
        
        print(f"🔍 Đang tìm submissions của user: {email}")
        
        # Lấy tất cả bài nộp của user, sắp xếp theo thời gian mới nhất
        result = supabase.table("submissions").select("*").eq("user_email", email).order("timestamp", desc=True).execute()
        
        if result.data:
            print(f"✅ Đã lấy {len(result.data)} submissions của {email}")
            
            # Xử lý dữ liệu để đảm bảo format đúng
            processed_submissions = []
            for s in result.data:
                try:
                    # Xử lý responses JSON
                    if isinstance(s.get("responses"), str):
                        try:
                            s["responses"] = json.loads(s["responses"])
                        except:
                            s["responses"] = {}
                    
                    # Xử lý essay_grades JSON
                    if isinstance(s.get("essay_grades"), str):
                        try:
                            s["essay_grades"] = json.loads(s["essay_grades"])
                        except:
                            s["essay_grades"] = {}
                    
                    # Xử lý essay_comments JSON
                    if isinstance(s.get("essay_comments"), str):
                        try:
                            s["essay_comments"] = json.loads(s["essay_comments"])
                        except:
                            s["essay_comments"] = {}
                    
                    # Đảm bảo score là số
                    if isinstance(s.get("score"), str):
                        try:
                            s["score"] = int(s["score"])
                        except:
                            s["score"] = 0
                    
                    processed_submissions.append(s)
                    
                except Exception as e:
                    print(f"Lỗi xử lý submission ID {s.get('id', 'N/A')}: {str(e)}")
                    continue
            
            return processed_submissions
        else:
            print(f"⚠️ Không tìm thấy submissions nào của {email}")
            return []
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy submissions của {email}: {str(e)}")
        traceback.print_exc()
        return []

def get_all_submissions():
    """Lấy tất cả bài nộp từ database - HÀM MỚI"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            print("❌ Không thể kết nối Supabase trong get_all_submissions")
            return []
        
        print("🔍 Đang lấy tất cả submissions...")
        
        # Lấy tất cả bài nộp, sắp xếp theo thời gian mới nhất
        result = supabase.table("submissions").select("*").order("timestamp", desc=True).execute()
        
        if result.data:
            print(f"✅ Đã lấy {len(result.data)} submissions từ database")
            
            # Xử lý dữ liệu để đảm bảo format đúng
            processed_submissions = []
            for s in result.data:
                try:
                    # Xử lý responses JSON
                    if isinstance(s.get("responses"), str):
                        try:
                            s["responses"] = json.loads(s["responses"])
                        except:
                            s["responses"] = {}
                    
                    # Xử lý essay_grades JSON
                    if isinstance(s.get("essay_grades"), str):
                        try:
                            s["essay_grades"] = json.loads(s["essay_grades"])
                        except:
                            s["essay_grades"] = {}
                    
                    # Xử lý essay_comments JSON
                    if isinstance(s.get("essay_comments"), str):
                        try:
                            s["essay_comments"] = json.loads(s["essay_comments"])
                        except:
                            s["essay_comments"] = {}
                    
                    # Đảm bảo score là số
                    if isinstance(s.get("score"), str):
                        try:
                            s["score"] = int(s["score"])
                        except:
                            s["score"] = 0
                    
                    processed_submissions.append(s)
                    
                except Exception as e:
                    print(f"Lỗi xử lý submission ID {s.get('id', 'N/A')}: {str(e)}")
                    continue
            
            return processed_submissions
        else:
            print("⚠️ Không có submissions nào trong database")
            return []
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy all submissions: {str(e)}")
        traceback.print_exc()
        return []

def test_database_connection():
    """Kiểm tra kết nối database và các bảng - HÀM MỚI"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False, "Không thể kết nối Supabase"
        
        # Test từng bảng
        results = {}
        
        # Test bảng questions
        try:
            questions_result = supabase.table("questions").select("count", count="exact").execute()
            results["questions"] = questions_result.count
        except Exception as e:
            results["questions"] = f"Lỗi: {str(e)}"
        
        # Test bảng users
        try:
            users_result = supabase.table("users").select("count", count="exact").execute()
            results["users"] = users_result.count
        except Exception as e:
            results["users"] = f"Lỗi: {str(e)}"
        
        # Test bảng submissions
        try:
            submissions_result = supabase.table("submissions").select("count", count="exact").execute()
            results["submissions"] = submissions_result.count
        except Exception as e:
            results["submissions"] = f"Lỗi: {str(e)}"
        
        return True, results
        
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"

# ===============================
# CÁC HÀM HELPER
# ===============================

def format_timestamp(timestamp):
    """Format timestamp thành chuỗi đọc được"""
    if not timestamp:
        return "Không xác định"
    
    try:
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
        else:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y %H:%M:%S")
    except:
        return "Không xác định"

def get_correct_answers(question):
    """Lấy danh sách đáp án đúng của câu hỏi"""
    try:
        q_correct = question.get("correct", [])
        q_answers = question.get("answers", [])
        
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
        
        return [q_answers[i - 1] for i in q_correct if 0 < i <= len(q_answers)]
        
    except (IndexError, TypeError):
        return ["Lỗi đáp án"]

def prepare_submission_data(submissions, students, questions, max_possible):
    """Chuẩn bị dữ liệu submission cho báo cáo"""
    all_submission_data = []
    
    for s in submissions:
        try:
            # Tìm thông tin học viên
            student_info = next((student for student in students if student.get("email") == s.get("user_email")), None)
            full_name = student_info.get("full_name", "Không xác định") if student_info else "Không xác định"
            class_name = student_info.get("class", "Không xác định") if student_info else "Không xác định"
            
            # Chuyển đổi timestamp sang định dạng đọc được
            submission_time = format_timestamp(s.get("timestamp"))
            
            # Thêm thông tin cơ bản
            submission_data = {
                "ID": s.get("id", ""),
                "Email": s.get("user_email", ""),
                "Họ và tên": full_name,
                "Lớp": class_name,
                "Thời gian nộp": submission_time,
                "Điểm số": s.get("score", 0),
                "Điểm tối đa": max_possible,
                "Tỷ lệ đúng": f"{(s.get('score', 0)/max_possible*100):.1f}%" if max_possible > 0 else "N/A"
            }
            
            # Chuyển đổi responses từ JSON string thành dict nếu cần
            responses = s.get("responses", {})
            if isinstance(responses, str):
                try:
                    responses = json.loads(responses)
                except:
                    responses = {}
            
            # Thêm câu trả lời của từng câu hỏi
            for q in questions:
                q_id = str(q.get("id", ""))
                user_ans = responses.get(q_id, [])
                
                # Chuẩn bị đáp án đúng
                expected_answers = get_correct_answers(q)
                is_correct = check_answer_correctness(user_ans, q)
                
                # Thêm thông tin câu hỏi
                submission_data[f"Câu {q_id}: {q.get('question', '')}"] = ", ".join([str(a) for a in user_ans]) if user_ans else "Không trả lời"
                submission_data[f"Câu {q_id} - Đúng/Sai"] = "Đúng" if is_correct else "Sai"
            
            all_submission_data.append(submission_data)
            
        except Exception as e:
            print(f"Lỗi khi xử lý submission ID {s.get('id', '')}: {str(e)}")
            continue
    
    return all_submission_data

# ===============================
# CÁC HÀM HIỂN THỊ TAB
# ===============================

def display_overview_tab(submissions=None, students=None, questions=None, max_possible=0):
    """Hiển thị tab tổng quan"""
    if submissions is None:
        submissions = []
    if students is None:
        students = []
    if questions is None:
        questions = []
        
    st.subheader("📊 Tổng quan kết quả")
    
    # Kiểm tra dữ liệu
    if not submissions:
        st.warning("⚠️ Không có dữ liệu bài nộp để hiển thị.")
        st.info("Dữ liệu sẽ xuất hiện sau khi có học viên làm bài.")
        return
    
    if not students:
        st.warning("⚠️ Không có dữ liệu học viên để hiển thị.")
        return
    
    if not questions:
        st.warning("⚠️ Không có dữ liệu câu hỏi để hiển thị.")
        return
    
    # Thống kê cơ bản
    total_submissions = len(submissions)
    scores = [s.get("score", 0) for s in submissions]
    avg_score = sum(scores) / total_submissions if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    
    # Số học viên unique
    unique_students = len(set([s.get("user_email") for s in submissions]))
    
    # Hiển thị metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Tổng số bài nộp", total_submissions)
        st.metric("👥 Số học viên đã làm", unique_students)
    
    with col2:
        st.metric("📊 Điểm trung bình", f"{avg_score:.1f}/{max_possible}")
        st.metric("🏆 Điểm cao nhất", f"{max_score}/{max_possible}")
    
    with col3:
        st.metric("📉 Điểm thấp nhất", f"{min_score}/{max_possible}")
        st.metric("📋 Số câu hỏi", len(questions))
    
    with col4:
        avg_percent = (avg_score / max_possible * 100) if max_possible > 0 else 0
        st.metric("📈 Tỷ lệ đúng TB", f"{avg_percent:.1f}%")
        st.metric("👨‍🎓 Tổng số học viên", len(students))
    
    # Biểu đồ phân phối điểm số
    st.subheader("📈 Phân phối điểm số")
    
    if scores:
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Tạo histogram với bins phù hợp
            n_bins = min(10, len(set(scores)))  # Tối đa 10 bins
            ax.hist(scores, bins=n_bins, alpha=0.7, color='skyblue', edgecolor='black')
            
            # Thêm đường trung bình
            ax.axvline(avg_score, color='red', linestyle='--', 
                      label=f'Trung bình: {avg_score:.1f}')
            
            ax.set_xlabel("Điểm số")
            ax.set_ylabel("Số lượng bài nộp")
            ax.set_title("Phân phối điểm số các bài nộp")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Lỗi khi vẽ biểu đồ: {str(e)}")
    
    # Thống kê theo thời gian
    st.subheader("📅 Hoạt động theo thời gian")
    
    try:
        # Chuẩn bị dữ liệu thời gian
        time_data = []
        for s in submissions:
            timestamp = s.get("timestamp")
            if timestamp:
                try:
                    if isinstance(timestamp, (int, float)):
                        submit_time = datetime.fromtimestamp(timestamp)
                    else:
                        submit_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    
                    time_data.append({
                        "date": submit_time.date(),
                        "score": s.get("score", 0)
                    })
                except:
                    continue
        
        if time_data:
            df_time = pd.DataFrame(time_data)
            
            # Nhóm theo ngày
            daily_stats = df_time.groupby('date').agg({
                'score': ['count', 'mean', 'max', 'min']
            }).round(2)
            
            daily_stats.columns = ['Số bài nộp', 'Điểm TB', 'Điểm cao nhất', 'Điểm thấp nhất']
            
            st.dataframe(daily_stats, use_container_width=True)
            
        else:
            st.info("Không có dữ liệu thời gian hợp lệ để hiển thị.")
            
    except Exception as e:
        st.error(f"Lỗi khi xử lý dữ liệu thời gian: {str(e)}")

def display_student_tab(submissions=None, students=None, questions=None, max_possible=0):
    """Hiển thị tab theo học viên"""
    if submissions is None:
        submissions = []
    if students is None:
        students = []
    if questions is None:
        questions = []
        
    st.subheader("👥 Chi tiết theo học viên")
    
    # Kiểm tra dữ liệu
    if not submissions:
        st.warning("⚠️ Không có dữ liệu bài nộp để hiển thị.")
        return
    
    if not students:
        st.warning("⚠️ Không có dữ liệu học viên để hiển thị.")
        return
    
    # Tạo DataFrame từ dữ liệu
    user_data = []
    for s in submissions:
        try:
            # Tìm thông tin học viên
            student_info = next((student for student in students if student.get("email") == s.get("user_email")), None)
            full_name = student_info.get("full_name", "Không xác định") if student_info else "Không xác định"
            class_name = student_info.get("class", "Không xác định") if student_info else "Không xác định"
            
            # Xử lý timestamp
            submission_time = format_timestamp(s.get("timestamp"))
            
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
            continue
    
    if not user_data:
        st.warning("⚠️ Không có dữ liệu hợp lệ để hiển thị.")
        return
    
    df_users = pd.DataFrame(user_data)
    
    # Lọc theo email hoặc lớp với dữ liệu thực tế
    col1, col2 = st.columns(2)
    
    with col1:
        # Lấy danh sách email unique
        unique_emails = sorted(list(set([u.get("email", "") for u in user_data if u.get("email")])))
        user_filter = st.selectbox(
            "Chọn học viên để xem chi tiết:",
            options=["Tất cả"] + unique_emails,
            key="user_filter_tab2"
        )
    
    with col2:
        # Lấy danh sách lớp unique (loại bỏ "Không xác định")
        unique_classes = sorted(list(set([u.get("class", "") for u in user_data 
                                        if u.get("class") and u.get("class") != "Không xác định"])))
        class_filter = st.selectbox(
            "Lọc theo lớp:",
            options=["Tất cả"] + unique_classes,
            key="class_filter_tab2"
        )
    
    # Áp dụng bộ lọc
    df_filtered = df_users.copy()
    
    if user_filter != "Tất cả":
        df_filtered = df_filtered[df_filtered["email"] == user_filter]
    
    if class_filter != "Tất cả":
        df_filtered = df_filtered[df_filtered["class"] == class_filter]
    
    # Hiển thị số liệu thống kê
    st.write(f"📊 **Hiển thị {len(df_filtered)} / {len(df_users)} bài nộp**")
    
    # Hiển thị bảng
    if not df_filtered.empty:
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
                
                # Hiển thị chi tiết bài nộp
                display_submission_details(selected_submission, submissions, questions, max_possible)
    else:
        st.info("Không có dữ liệu phù hợp với bộ lọc đã chọn.")

def display_question_tab(submissions=None, questions=None):
    """Hiển thị tab phân tích câu hỏi - ĐÃ SỬA LỖI HIỂN THỊ"""
    if submissions is None:
        submissions = []
    if questions is None:
        questions = []
        
    st.subheader("❓ Phân tích theo câu hỏi")
    
    if not questions:
        st.warning("⚠️ Không có câu hỏi để phân tích.")
        return pd.DataFrame()
    
    if not submissions:
        st.warning("⚠️ Không có bài nộp để phân tích.")
        return pd.DataFrame()
    
    # Thống kê tỷ lệ đúng/sai cho từng câu hỏi
    question_stats = {}
    
    for q in questions:
        q_id = str(q.get("id", ""))
        correct_count = 0
        wrong_count = 0
        skip_count = 0
        
        for s in submissions:
            # Đảm bảo responses đúng định dạng
            responses = s.get("responses", {})
            if isinstance(responses, str):
                try:
                    responses = json.loads(responses)
                except:
                    responses = {}
            
            user_ans = responses.get(q_id, [])
            
            if not user_ans:
                skip_count += 1
            elif check_answer_correctness(user_ans, q):
                correct_count += 1
            else:
                wrong_count += 1
        
        question_stats[q_id] = {
            "question": q.get("question", ""),
            "type": q.get("type", ""),
            "correct": correct_count,
            "wrong": wrong_count,
            "skip": skip_count,
            "total": correct_count + wrong_count + skip_count,
            "correct_rate": correct_count / (correct_count + wrong_count + skip_count) if (correct_count + wrong_count + skip_count) > 0 else 0
        }
    
    # DataFrame thống kê câu hỏi - ĐÃ SỬA HIỂN THỊ
    df_questions_data = [
        {
            "ID": q_id,
            "Nội dung câu hỏi": stats["question"],
            "Loại": stats["type"],
            "Đúng": stats["correct"],
            "Sai": stats["wrong"],
            "Bỏ qua": stats["skip"],
            "Tổng": stats["total"],
            "Tỷ lệ đúng (%)": f"{stats['correct_rate']*100:.1f}%"
        }
        for q_id, stats in question_stats.items()
    ]
    
    if not df_questions_data:
        st.info("Không có dữ liệu câu hỏi để phân tích.")
        return pd.DataFrame()
    
    df_questions = pd.DataFrame(df_questions_data)
    
    # Tạo bộ lọc loại câu hỏi
    question_types = ["Tất cả", "Checkbox", "Combobox", "Essay"]
    selected_type = st.selectbox("Lọc theo loại câu hỏi:", question_types, key="filter_question_type_tab3")
    
    # Áp dụng bộ lọc
    filtered_df = df_questions
    if selected_type != "Tất cả":
        filtered_df = df_questions[df_questions["Loại"] == selected_type]
    
    # ✅ SỬA LỖI HIỂN THỊ: Sử dụng st.data_editor với cấu hình tự động điều chỉnh
    st.write(f"📊 **Hiển thị {len(filtered_df)} / {len(df_questions)} câu hỏi**")
    
    # Cấu hình hiển thị cột
    column_config = {
        "ID": st.column_config.NumberColumn("ID", width="small"),
        "Nội dung câu hỏi": st.column_config.TextColumn(
            "Nội dung câu hỏi",
            width="large",
            help="Nội dung đầy đủ của câu hỏi"
        ),
        "Loại": st.column_config.TextColumn("Loại", width="small"),
        "Đúng": st.column_config.NumberColumn("Đúng", width="small"),
        "Sai": st.column_config.NumberColumn("Sai", width="small"),
        "Bỏ qua": st.column_config.NumberColumn("Bỏ qua", width="small"),
        "Tổng": st.column_config.NumberColumn("Tổng", width="small"),
        "Tỷ lệ đúng (%)": st.column_config.TextColumn("Tỷ lệ đúng (%)", width="medium")
    }
    
    # Hiển thị bảng với khả năng mở rộng
    st.data_editor(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        disabled=True,  # Chỉ xem, không chỉnh sửa
        column_config=column_config,
        height=600  # Tăng chiều cao để hiển thị nhiều dữ liệu hơn
    )
    
    # Thêm chi tiết cho từng câu hỏi
    st.subheader("📋 Chi tiết từng câu hỏi")
    
    # Dropdown để chọn câu hỏi cụ thể
    question_options = {f"Câu {q_id}: {stats['question'][:50]}...": q_id 
                       for q_id, stats in question_stats.items()}
    
    if question_options:
        selected_question = st.selectbox(
            "Chọn câu hỏi để xem chi tiết:",
            options=list(question_options.keys()),
            key="select_question_detail"
        )
        
        if selected_question:
            q_id = question_options[selected_question]
            stats = question_stats[q_id]
            
            # Hiển thị thông tin chi tiết
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("✅ Trả lời đúng", stats["correct"])
            with col2:
                st.metric("❌ Trả lời sai", stats["wrong"])
            with col3:
                st.metric("⏭️ Bỏ qua", stats["skip"])
            with col4:
                st.metric("📊 Tỷ lệ đúng", f"{stats['correct_rate']*100:.1f}%")
            
            # Tìm câu hỏi gốc để hiển thị đáp án đúng
            original_question = next((q for q in questions if str(q.get("id")) == q_id), None)
            
            if original_question:
                st.write("**📝 Nội dung câu hỏi:**")
                st.write(original_question.get("question", ""))
                
                if original_question.get("type") != "Essay":
                    st.write("**✅ Đáp án đúng:**")
                    correct_answers = get_correct_answers(original_question)
                    for ans in correct_answers:
                        st.write(f"- {ans}")
    
    return df_questions

def display_student_list_tab(submissions=None, students=None, max_possible=0):
    """Hiển thị tab danh sách học viên"""
    if submissions is None:
        submissions = []
    if students is None:
        students = []
        
    st.subheader("📋 Danh sách học viên")
    
    # Kiểm tra dữ liệu
    if not students:
        st.warning("⚠️ Chưa có học viên nào đăng ký trong hệ thống.")
        st.info("Học viên sẽ xuất hiện sau khi đăng ký tài khoản.")
        return pd.DataFrame(), pd.DataFrame()
    
    # Chuẩn bị dữ liệu
    student_data = []
    for student in students:
        try:
            # Tìm tất cả bài nộp của học viên
            student_email = student.get("email", "")
            student_submissions = [s for s in submissions if s.get("user_email") == student_email]
            submission_count = len(student_submissions)
            
            # Tìm điểm cao nhất
            max_student_score = max([s.get("score", 0) for s in student_submissions]) if student_submissions else 0
            
            # Thời gian đăng ký
            registration_date = format_timestamp(student.get("registration_date"))
            
            student_data.append({
                "full_name": student.get("full_name", ""),
                "email": student_email,
                "class": student.get("class", ""),
                "registration_date": registration_date,
                "submission_count": submission_count,
                "max_score": max_student_score,
                "max_possible": max_possible,
                "percent": f"{(max_student_score/max_possible*100):.1f}%" if max_possible > 0 else "N/A"
            })
        except Exception as e:
            st.error(f"Lỗi khi xử lý dữ liệu học viên {student.get('email', '')}: {str(e)}")
            continue
    
    if not student_data:
        st.warning("⚠️ Không có dữ liệu học viên hợp lệ.")
        return pd.DataFrame(), pd.DataFrame()
    
    # DataFrame cho danh sách học viên
    df_students_list = pd.DataFrame([
        {
            "Họ và tên": s["full_name"],
            "Email": s["email"],
            "Lớp": s["class"],
            "Ngày đăng ký": s["registration_date"],
            "Số lần làm bài": s["submission_count"],
            "Điểm cao nhất": s["max_score"],
            "Điểm tối đa": s["max_possible"],
            "Tỷ lệ đúng": s["percent"]
        } for s in student_data
    ])
    
    # Lọc theo lớp với dữ liệu thực tế
    unique_classes = sorted(list(set([s["class"] for s in student_data 
                                    if s["class"] and s["class"].strip()])))
    
    class_filter = st.selectbox(
        "Lọc theo lớp:",
        options=["Tất cả"] + unique_classes,
        key="class_filter_tab4"
    )
    
    # Áp dụng bộ lọc
    df_students = pd.DataFrame(student_data)
    
    if class_filter != "Tất cả":
        df_students = df_students[df_students["class"] == class_filter]
    
    # Sắp xếp theo tên
    df_students = df_students.sort_values(by="full_name")
    
    # Hiển thị số liệu
    st.write(f"📊 **Hiển thị {len(df_students)} / {len(student_data)} học viên**")
    
    # Hiển thị bảng
    if not df_students.empty:
        display_columns = ["full_name", "email", "class", "registration_date", 
                          "submission_count", "max_score", "percent"]
        
        display_df = df_students[display_columns].copy()
        display_df.columns = ["Họ và tên", "Email", "Lớp", "Ngày đăng ký", 
                             "Số lần làm", "Điểm cao nhất", "Tỷ lệ đúng"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Thống kê theo lớp
        st.subheader("📊 Thống kê theo lớp")
        
        class_stats = df_students.groupby("class").agg({
            "email": "count",
            "submission_count": "sum",
            "max_score": "mean"
        }).reset_index()
        
        class_stats.columns = ["Lớp", "Số học viên", "Tổng số bài nộp", "Điểm trung bình"]
        class_stats["Điểm trung bình"] = class_stats["Điểm trung bình"].round(2)
        
        df_class_stats = class_stats.copy()
        
        st.dataframe(class_stats, use_container_width=True, hide_index=True)
        
        return df_students_list, df_class_stats
    else:
        st.info("Không có học viên nào phù hợp với bộ lọc đã chọn.")
        return pd.DataFrame(), pd.DataFrame()

def display_export_tab(df_all_submissions=None, df_questions=None, df_students_list=None, df_class_stats=None):
    """Hiển thị tab xuất báo cáo - ĐÃ BỔ SUNG CHỨC NĂNG XUẤT FILE"""
    if df_all_submissions is None:
        df_all_submissions = pd.DataFrame()
    if df_questions is None:
        df_questions = pd.DataFrame()
    if df_students_list is None:
        df_students_list = pd.DataFrame()
    if df_class_stats is None:
        df_class_stats = pd.DataFrame()
        
    st.subheader("📤 Xuất báo cáo")
    
    # Lấy dữ liệu cần thiết
    questions = get_all_questions()
    students = get_all_users(role="student")
    submissions = get_all_submissions()
    max_possible = sum([q.get("score", 0) for q in questions])
    
    # Thêm tab cho các loại báo cáo khác nhau
    report_tab1, report_tab2, report_tab3 = st.tabs([
        "📊 Báo cáo tổng hợp", 
        "👤 Báo cáo theo học viên",
        "🎓 Báo cáo theo lớp"
    ])
    
    with report_tab1:
        st.write("### 📊 Báo cáo tổng hợp hệ thống")
        
        if not submissions or not students or not questions:
            st.warning("⚠️ Chưa có đủ dữ liệu để xuất báo cáo tổng hợp.")
            st.info("Cần có ít nhất: 1 câu hỏi, 1 học viên và 1 bài nộp.")
            return
        
        st.success(f"✅ Sẵn sàng xuất báo cáo tổng hợp:")
        st.write(f"- 📝 **Câu hỏi:** {len(questions)}")
        st.write(f"- 👥 **Học viên:** {len(students)}")
        st.write(f"- 📋 **Bài nộp:** {len(submissions)}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Xuất báo cáo tổng hợp (DOCX)", 
                        type="primary", use_container_width=True):
                with st.spinner("🔄 Đang tạo báo cáo DOCX..."):
                    try:
                        buffer = create_overall_report(submissions, students, questions, max_possible)
                        
                        if buffer.getvalue():
                            filename = f"bao_cao_tong_hop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                            
                            st.download_button(
                                label="📥 Tải xuống báo cáo DOCX",
                                data=buffer.getvalue(),
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                            st.success("✅ Báo cáo DOCX đã được tạo thành công!")
                        else:
                            st.error("❌ Không thể tạo báo cáo DOCX. Vui lòng thử lại.")
                    except Exception as e:
                        st.error(f"❌ Lỗi khi tạo báo cáo: {str(e)}")
        
        with col2:
            if st.button("📑 Xuất báo cáo tổng hợp (PDF)", 
                        type="secondary", use_container_width=True):
                with st.spinner("🔄 Đang tạo báo cáo PDF..."):
                    try:
                        # Tạo DataFrame tổng hợp cho PDF
                        summary_data = []
                        for s in submissions:
                            student_info = next((st for st in students if st.get("email") == s.get("user_email")), None)
                            summary_data.append({
                                "Họ tên": student_info.get("full_name", "N/A") if student_info else "N/A",
                                "Lớp": student_info.get("class", "N/A") if student_info else "N/A",
                                "Email": s.get("user_email", ""),
                                "Thời gian": format_timestamp(s.get("timestamp")),
                                "Điểm": f"{s.get('score', 0)}/{max_possible}",
                                "Tỷ lệ": f"{(s.get('score', 0)/max_possible*100):.1f}%" if max_possible > 0 else "N/A"
                            })
                        
                        df_summary = pd.DataFrame(summary_data)
                        buffer = dataframe_to_pdf_fpdf(df_summary, "Báo cáo tổng hợp hệ thống", "bao_cao_tong_hop")
                        
                        if buffer.getvalue():
                            filename = f"bao_cao_tong_hop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            
                            st.download_button(
                                label="📥 Tải xuống báo cáo PDF",
                                data=buffer.getvalue(),
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("✅ Báo cáo PDF đã được tạo thành công!")
                        else:
                            st.error("❌ Không thể tạo báo cáo PDF. Vui lòng thử lại.")
                    except Exception as e:
                        st.error(f"❌ Lỗi khi tạo báo cáo: {str(e)}")
        
        # Xuất Excel tổng hợp
        st.divider()
        if st.button("📊 Xuất tất cả dữ liệu (Excel)", use_container_width=True):
            with st.spinner("🔄 Đang tạo file Excel..."):
                try:
                    # Chuẩn bị nhiều sheet
                    sheets_data = []
                    sheet_names = []
                    
                    # Sheet 1: Tất cả bài nộp
                    if not df_all_submissions.empty:
                        sheets_data.append(df_all_submissions)
                        sheet_names.append("Tất cả bài nộp")
                    
                    # Sheet 2: Danh sách học viên
                    if not df_students_list.empty:
                        sheets_data.append(df_students_list)
                        sheet_names.append("Danh sách học viên")
                    
                    # Sheet 3: Thống kê câu hỏi
                    if not df_questions.empty:
                        sheets_data.append(df_questions)
                        sheet_names.append("Thống kê câu hỏi")
                    
                    # Sheet 4: Thống kê lớp
                    if not df_class_stats.empty:
                        sheets_data.append(df_class_stats)
                        sheet_names.append("Thống kê lớp")
                    
                    if sheets_data:
                        filename = f"bao_cao_tong_hop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        excel_link = export_to_excel(sheets_data, sheet_names, filename)
                        st.markdown(excel_link, unsafe_allow_html=True)
                        st.success("✅ File Excel đã được tạo thành công!")
                    else:
                        st.warning("⚠️ Không có dữ liệu để xuất Excel.")
                        
                except Exception as e:
                    st.error(f"❌ Lỗi khi tạo file Excel: {str(e)}")
    
    with report_tab2:
        st.write("### 👤 Báo cáo chi tiết theo từng học viên")
        
        if not students:
            st.warning("⚠️ Không có dữ liệu học viên để hiển thị.")
            return
        
        # Dropdown chọn học viên
        student_emails = [student.get("email", "") for student in students if student.get("email")]
        student_emails = sorted(list(set(student_emails)))
        
        if not student_emails:
            st.warning("⚠️ Không tìm thấy email học viên hợp lệ.")
            return
        
        selected_email = st.selectbox(
            "Chọn email học viên:",
            options=student_emails,
            key="export_student_select"
        )
        
        if selected_email:
            # Hiển thị thông tin học viên
            student_info = next((s for s in students if s.get("email") == selected_email), None)
            
            if student_info:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**👤 Họ tên:** {student_info.get('full_name', 'N/A')}")
                    st.write(f"**📧 Email:** {student_info.get('email', 'N/A')}")
                with col2:
                    st.write(f"**🎓 Lớp:** {student_info.get('class', 'N/A')}")
                    st.write(f"**👥 Vai trò:** {student_info.get('role', 'N/A')}")
                
                # Lấy bài nộp của học viên
                student_submissions = get_user_submissions(selected_email)
                
                if student_submissions:
                    st.success(f"📋 Tìm thấy {len(student_submissions)} bài làm của học viên này")
                    
                    # Chọn bài nộp cụ thể
                    if len(student_submissions) > 1:
                        submission_options = {}
                        for i, sub in enumerate(student_submissions):
                            timestamp = format_timestamp(sub.get("timestamp"))
                            score = sub.get("score", 0)
                            submission_options[f"Bài {i+1}: {timestamp} - Điểm: {score}"] = sub
                        
                        selected_submission_name = st.selectbox(
                            "Chọn bài làm để xuất báo cáo:",
                            options=list(submission_options.keys()),
                            key="select_submission_export"
                        )
                        selected_submission = submission_options[selected_submission_name]
                    else:
                        selected_submission = student_submissions[0]
                        timestamp = format_timestamp(selected_submission.get("timestamp"))
                        score = selected_submission.get("score", 0)
                        st.info(f"📝 Sẽ xuất báo cáo cho bài làm: {timestamp} - Điểm: {score}")
                    
                    # Nút xuất báo cáo
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📄 Xuất báo cáo học viên (DOCX)", 
                                    type="primary", use_container_width=True):
                            with st.spinner("🔄 Đang tạo báo cáo DOCX..."):
                                try:
                                    buffer = create_student_report_docx(
                                        student_info.get("full_name", ""),
                                        student_info.get("email", ""),
                                        student_info.get("class", ""),
                                        selected_submission,
                                        questions,
                                        max_possible
                                    )
                                    
                                    if buffer.getvalue():
                                        filename = f"bao_cao_{student_info.get('full_name', 'hoc_vien')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                                        
                                        st.download_button(
                                            label="📥 Tải xuống báo cáo DOCX",
                                            data=buffer.getvalue(),
                                            file_name=filename,
                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                            use_container_width=True
                                        )
                                        st.success("✅ Báo cáo DOCX đã được tạo thành công!")
                                    else:
                                        st.error("❌ Không thể tạo báo cáo DOCX.")
                                except Exception as e:
                                    st.error(f"❌ Lỗi khi tạo báo cáo: {str(e)}")
                    
                    with col2:
                        if st.button("📑 Xuất báo cáo học viên (PDF)", 
                                    type="secondary", use_container_width=True):
                            with st.spinner("🔄 Đang tạo báo cáo PDF..."):
                                try:
                                    buffer = create_student_report_pdf_fpdf(
                                        student_info.get("full_name", ""),
                                        student_info.get("email", ""),
                                        student_info.get("class", ""),
                                        selected_submission,
                                        questions,
                                        max_possible
                                    )
                                    
                                    if buffer.getvalue():
                                        filename = f"bao_cao_{student_info.get('full_name', 'hoc_vien')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                        
                                        st.download_button(
                                            label="📥 Tải xuống báo cáo PDF",
                                            data=buffer.getvalue(),
                                            file_name=filename,
                                            mime="application/pdf",
                                            use_container_width=True
                                        )
                                        st.success("✅ Báo cáo PDF đã được tạo thành công!")
                                    else:
                                        st.error("❌ Không thể tạo báo cáo PDF.")
                                except Exception as e:
                                    st.error(f"❌ Lỗi khi tạo báo cáo: {str(e)}")
                else:
                    st.warning(f"⚠️ Không tìm thấy bài nộp nào của học viên {selected_email}")
                    st.info("Học viên cần hoàn thành ít nhất một bài khảo sát để có thể xuất báo cáo.")
    
    with report_tab3:
        st.write("### 🎓 Báo cáo chi tiết theo lớp")
        
        if not students:
            st.warning("⚠️ Không có dữ liệu học viên để hiển thị.")
            return
        
        # Lấy danh sách lớp
        classes = sorted(list(set([s.get("class", "") for s in students 
                                 if s.get("class") and s.get("class").strip()])))
        
        if not classes:
            st.warning("⚠️ Không tìm thấy thông tin lớp hợp lệ.")
            return
        
        selected_class = st.selectbox(
            "Chọn lớp để xuất báo cáo:",
            options=classes,
            key="export_class_select"
        )
        
        if selected_class:
            # Hiển thị thông tin lớp
            class_students = [s for s in students if s.get("class") == selected_class]
            class_submissions = [s for s in submissions 
                               if any(st.get("email") == s.get("user_email") for st in class_students)]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("👥 Tổng số học viên", len(class_students))
            with col2:
                st.metric("📋 Tổng số bài nộp", len(class_submissions))
            with col3:
                avg_score = sum(s.get("score", 0) for s in class_submissions) / len(class_submissions) if class_submissions else 0
                st.metric("📊 Điểm trung bình", f"{avg_score:.1f}/{max_possible}")
            
            if class_submissions:
                # Nút xuất báo cáo lớp
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📄 Xuất báo cáo lớp (DOCX)", 
                                type="primary", use_container_width=True):
                        with st.spinner("🔄 Đang tạo báo cáo lớp DOCX..."):
                            try:
                                buffer = create_class_report(
                                    selected_class,
                                    class_submissions,
                                    class_students,
                                    questions,
                                    max_possible
                                )
                                
                                if buffer.getvalue():
                                    filename = f"bao_cao_lop_{selected_class}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                                    
                                    st.download_button(
                                        label="📥 Tải xuống báo cáo lớp DOCX",
                                        data=buffer.getvalue(),
                                        file_name=filename,
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        use_container_width=True
                                    )
                                    st.success("✅ Báo cáo lớp DOCX đã được tạo thành công!")
                                else:
                                    st.error("❌ Không thể tạo báo cáo lớp DOCX.")
                            except Exception as e:
                                st.error(f"❌ Lỗi khi tạo báo cáo: {str(e)}")
                
                with col2:
                    if st.button("📑 Xuất báo cáo lớp (PDF)", 
                                type="secondary", use_container_width=True):
                        with st.spinner("🔄 Đang tạo báo cáo lớp PDF..."):
                            try:
                                # Tạo DataFrame cho báo cáo lớp
                                class_data = []
                                for submission in class_submissions:
                                    student_info = next((s for s in class_students 
                                                       if s.get("email") == submission.get("user_email")), None)
                                    class_data.append({
                                        "Họ tên": student_info.get("full_name", "N/A") if student_info else "N/A",
                                        "Email": submission.get("user_email", ""),
                                        "Thời gian nộp": format_timestamp(submission.get("timestamp")),
                                        "Điểm số": f"{submission.get('score', 0)}/{max_possible}",
                                        "Tỷ lệ": f"{(submission.get('score', 0)/max_possible*100):.1f}%" if max_possible > 0 else "N/A"
                                    })
                                
                                df_class = pd.DataFrame(class_data)
                                buffer = dataframe_to_pdf_fpdf(
                                    df_class, 
                                    f"Báo cáo lớp {selected_class}", 
                                    f"bao_cao_lop_{selected_class}"
                                )
                                
                                if buffer.getvalue():
                                    filename = f"bao_cao_lop_{selected_class}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                    
                                    st.download_button(
                                        label="📥 Tải xuống báo cáo lớp PDF",
                                        data=buffer.getvalue(),
                                        file_name=filename,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                                    st.success("✅ Báo cáo lớp PDF đã được tạo thành công!")
                                else:
                                    st.error("❌ Không thể tạo báo cáo lớp PDF.")
                            except Exception as e:
                                st.error(f"❌ Lỗi khi tạo báo cáo: {str(e)}")
            else:
                st.warning(f"⚠️ Lớp {selected_class} chưa có bài nộp nào.")
                st.info("Cần có ít nhất một bài nộp từ lớp này để có thể xuất báo cáo.")
                

def display_submission_details(submission_id, submissions, questions, max_possible):
    """Hiển thị chi tiết một bài nộp"""
    # Tìm bài nộp được chọn
    submission = next((s for s in submissions if str(s.get("id", "")) == str(submission_id)), None)
    
    if not submission:
        st.error("Không tìm thấy bài nộp!")
        return
    
    st.subheader(f"📋 Chi tiết bài nộp #{submission_id}")
    
    # Thông tin tổng quan
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📧 Email", submission.get("user_email", "N/A"))
    with col2:
        st.metric("🎯 Điểm số", f"{submission.get('score', 0)}/{max_possible}")
    with col3:
        timestamp = format_timestamp(submission.get("timestamp"))
        st.metric("⏰ Thời gian", timestamp)
    
    # Chi tiết câu trả lời
    st.write("### 📝 Chi tiết câu trả lời")
    
    responses = submission.get("responses", {})
    if isinstance(responses, str):
        try:
            responses = json.loads(responses)
        except:
            responses = {}
    
    total_correct = 0
    
    for q in questions:
        q_id = str(q.get("id", ""))
        
        with st.expander(f"Câu {q_id}: {q.get('question', '')[:50]}..."):
            # Đáp án người dùng
            user_ans = responses.get(q_id, [])
            
            # Kiểm tra đúng/sai
            is_correct = check_answer_correctness(user_ans, q)
            if is_correct:
                total_correct += 1
            
            # Hiển thị đáp án
            st.write("**Đáp án của học viên:**")
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
                
                # Hiển thị đáp án đúng
                correct_answers = get_correct_answers(q)
                st.write("**Đáp án đúng:**")
                for ans in correct_answers:
                    st.write(f"- {ans}")
    
    # Tổng kết
    st.write("### 📊 Tổng kết")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Số câu đúng", f"{total_correct}/{len(questions)}")
    col2.metric("Điểm số", f"{submission.get('score', 0)}/{max_possible}")
    
    if len(questions) > 0:
        accuracy = (total_correct / len(questions)) * 100
        col3.metric("Tỷ lệ đúng", f"{accuracy:.1f}%")

# ===============================
# HÀM CHÍNH
# ===============================

def view_statistics():
    """Hiển thị trang thống kê và báo cáo - HÀM CHÍNH"""
    st.title("📊 Báo cáo & thống kê")
    
    # Khởi tạo biến trước
    questions = []
    students = []
    submissions = []
    max_possible = 0
    df_questions = pd.DataFrame()
    df_students_list = pd.DataFrame()
    df_class_stats = pd.DataFrame()
    df_all_submissions = pd.DataFrame()
    
      
    try:
        # Sử dụng các hàm hoàn thiện
        with st.spinner("🔄 Đang tải dữ liệu từ database..."):
            
            # Lấy dữ liệu câu hỏi
            questions = get_all_questions()
            if questions:
                st.success(f"📝 Đã tải {len(questions)} câu hỏi")
            else:
                st.warning("⚠️ Không có câu hỏi nào trong hệ thống")
            
            # Lấy dữ liệu học viên với role="student"
            students = get_all_users(role="student")
            if students:
                st.success(f"👥 Đã tải {len(students)} học viên")
            else:
                st.warning("⚠️ Không có học viên nào trong hệ thống")
            
            # Lấy tất cả bài nộp
            submissions = get_all_submissions()
            if submissions:
                st.success(f"📋 Đã tải {len(submissions)} bài nộp")
            else:
                st.warning("⚠️ Không có bài nộp nào trong hệ thống")
        
        # Tạo form tìm kiếm email nếu muốn xem báo cáo theo học viên cụ thể
        with st.sidebar:
            st.subheader("🔍 Tìm kiếm học viên")
            
            if students:
                # Tạo dropdown với email thực tế
                student_emails = [s.get("email", "") for s in students if s.get("email")]
                selected_student = st.selectbox(
                    "Chọn học viên:",
                    options=["Tất cả"] + sorted(student_emails),
                    key="sidebar_student_select"
                )
                
                if selected_student != "Tất cả":
                    # Lọc submissions theo email đã chọn
                    student_submissions = get_user_submissions(selected_student)
                    if student_submissions:
                        submissions = student_submissions
                        st.success(f"✅ Đã lọc {len(submissions)} bài nộp của {selected_student}")
                    else:
                        st.warning(f"⚠️ Không có bài nộp nào của {selected_student}")
            else:
                st.info("Không có học viên để tìm kiếm")
        
        # Kiểm tra dữ liệu cần thiết
        if not questions:
            st.error("❌ Không có câu hỏi nào trong hệ thống.")
            st.info("💡 Vui lòng thêm câu hỏi trong phần 'Quản lý câu hỏi' trước.")
            return
        
        if not students:
            st.error("❌ Không có học viên nào trong hệ thống.")
            st.info("💡 Vui lòng kiểm tra lại database hoặc có học viên đăng ký.")
            return
            
        if not submissions:
            st.info("ℹ️ Chưa có bài nộp nào. Dữ liệu sẽ hiển thị sau khi có học viên làm bài.")
            # Vẫn hiển thị tabs để admin có thể xem cấu trúc
        
        # Tạo tab thống kê
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Tổng quan", 
            "👤 Theo học viên", 
            "❓ Theo câu hỏi", 
            "📋 Danh sách học viên", 
            "📤 Xuất báo cáo"
        ])
        
        # Tính tổng điểm tối đa
        max_possible = sum([q.get("score", 0) for q in questions])
        st.info(f"🎯 **Tổng điểm tối đa của bài khảo sát:** {max_possible} điểm")
        
        # Chuẩn bị dữ liệu cho tất cả các submissions
        if submissions:
            all_submission_data = prepare_submission_data(submissions, students, questions, max_possible)
            df_all_submissions = pd.DataFrame(all_submission_data) if all_submission_data else pd.DataFrame()
        
        with tab1:
            display_overview_tab(submissions, students, questions, max_possible)
        
        with tab2:
            display_student_tab(submissions, students, questions, max_possible)
        
        with tab3:
            df_questions = display_question_tab(submissions, questions)
        
        with tab4:
            df_students_list, df_class_stats = display_student_list_tab(submissions, students, max_possible)
        
        with tab5:
            display_export_tab(df_all_submissions, df_questions, df_students_list, df_class_stats)
    
    except Exception as e:
        st.error(f"❌ Đã xảy ra lỗi không mong muốn: {str(e)}")
        
        # Hiển thị thông tin debug chi tiết
        with st.expander("🔍 Chi tiết lỗi"):
            st.code(traceback.format_exc())
            
            st.write("**Thông tin debug:**")
            st.write(f"- Số câu hỏi: {len(questions) if questions else 0}")
            st.write(f"- Số học viên: {len(students) if students else 0}")
            st.write(f"- Số bài nộp: {len(submissions) if submissions else 0}")
            
            # Hiển thị sample data nếu có
            if questions:
                st.write("**Sample Question:**")
                st.json(questions[0])
            
            if students:
                st.write("**Sample Student:**")
                st.json(students[0])
            
            if submissions:
                st.write("**Sample Submission:**")
                st.json(submissions[0])

# ===============================
# CÁC HÀM XUẤT FILE (PLACEHOLDER)
# ===============================

def get_download_link_docx(buffer, filename, text):
    """Tạo link tải xuống cho file DOCX"""
    b64 = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{filename}">📥 {text}</a>'
    return href

def get_download_link_pdf(buffer, filename, text):
    """Tạo link tải xuống cho file PDF"""
    b64 = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 {text}</a>'
    return href

def export_to_excel(dataframes, sheet_names, filename):
    """Tạo file Excel với nhiều sheet từ các DataFrame - ĐÃ CẢI THIỆN"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for df, sheet_name in zip(dataframes, sheet_names):
                if not df.empty:
                    # Làm sạch tên sheet (loại bỏ ký tự không hợp lệ)
                    clean_sheet_name = sheet_name.replace("/", "-").replace("\\", "-")[:31]
                    df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
                    
                    # Tối ưu độ rộng cột
                    worksheet = writer.sheets[clean_sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        data = output.getvalue()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 Tải xuống {filename}</a>'
        return href
        
    except Exception as e:
        st.error(f"Lỗi khi tạo file Excel: {str(e)}")
        return ""

# ===============================
# CÁC HÀM XUẤT BÁO CÁO CHI TIẾT
# ===============================

def create_student_report_docx(student_name, student_email, student_class, submission, questions, max_possible):
    """Tạo báo cáo chi tiết bài làm của học viên dạng DOCX, bao gồm câu tự luận"""
    try:
        doc = Document()
        
        # Thiết lập font chữ mặc định là Times New Roman
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Thêm tiêu đề - font chữ hỗ trợ Unicode
        heading = doc.add_heading(f"Báo cáo chi tiết - {student_name}", level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Thêm thời gian xuất báo cáo
        time_paragraph = doc.add_paragraph(f"Thời gian xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        time_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Thêm thông tin học viên
        doc.add_heading("Thông tin học viên", level=2)
        info_table = doc.add_table(rows=4, cols=2, style='Table Grid')
        
        # Đặt độ rộng cột
        for cell in info_table.columns[0].cells:
            cell.width = Inches(1.5)
        for cell in info_table.columns[1].cells:
            cell.width = Inches(4.5)
        
        # Thiết lập màu nền cho hàng tiêu đề
        for i in range(4):
            # Sửa lỗi: Đảm bảo có runs trước khi truy cập
            cell = info_table.rows[i].cells[0]
            cell_paragraph = cell.paragraphs[0]
            if not cell_paragraph.runs:
                cell_paragraph.add_run(cell.text if cell.text else '')
            cell_paragraph.runs[0].font.bold = True
            
            # Thêm màu nền
            shading_elm = parse_xml(r'<w:shd {} w:fill="E9E9E9"/>'.format(nsdecls('w')))
            info_table.rows[i].cells[0]._tc.get_or_add_tcPr().append(shading_elm)
        
        # Thêm dữ liệu vào bảng thông tin
        cells = info_table.rows[0].cells
        cells[0].text = "Họ và tên"
        cells[1].text = student_name
        
        cells = info_table.rows[1].cells
        cells[0].text = "Email"
        cells[1].text = student_email
        
        cells = info_table.rows[2].cells
        cells[0].text = "Lớp"
        cells[1].text = student_class
        
        # Xử lý timestamp tương thích với cả hai kiểu dữ liệu (số và chuỗi ISO)
        submission_time = format_timestamp(submission.get("timestamp"))
        
        cells = info_table.rows[3].cells
        cells[0].text = "Thời gian nộp"
        cells[1].text = submission_time
        
        # Lấy điểm câu hỏi tự luận (nếu có)
        essay_grades = {}
        if "essay_grades" in submission:
            if isinstance(submission["essay_grades"], str):
                try:
                    essay_grades = json.loads(submission["essay_grades"])
                except:
                    essay_grades = {}
            else:
                essay_grades = submission.get("essay_grades", {})
                
        # Lấy nhận xét câu hỏi tự luận (nếu có)
        essay_comments = {}
        if "essay_comments" in submission:
            if isinstance(submission["essay_comments"], str):
                try:
                    essay_comments = json.loads(submission["essay_comments"])
                except:
                    essay_comments = {}
            else:
                essay_comments = submission.get("essay_comments", {})
        
        # Tính toán thông tin về bài làm
        total_correct = 0
        total_questions = len(questions)
        
        doc.add_heading("Chi tiết câu trả lời", level=2)
        
        # Tạo bảng chi tiết câu trả lời
        answers_table = doc.add_table(rows=1, cols=5, style='Table Grid')
        
        # Thiết lập độ rộng tương đối cho các cột
        col_widths = [2.5, 2, 2, 1, 0.8]  # Tỷ lệ tương đối
        for i, width in enumerate(col_widths):
            for cell in answers_table.columns[i].cells:
                cell.width = Inches(width)
        
        # Thêm tiêu đề cho bảng với định dạng rõ ràng
        header_cells = answers_table.rows[0].cells
        headers = ["Câu hỏi", "Đáp án của học viên", "Đáp án đúng/Nhận xét", "Kết quả", "Điểm"]
        
        # Tạo nền xám cho hàng tiêu đề
        for i, cell in enumerate(header_cells):
            cell.text = headers[i]
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                # Đảm bảo có runs trước khi truy cập
                if not paragraph.runs:
                    paragraph.add_run(headers[i])
                for run in paragraph.runs:
                    run.bold = True
            # Thêm màu nền
            shading_elm = parse_xml(r'<w:shd {} w:fill="E9E9E9"/>'.format(nsdecls('w')))
            cell._tc.get_or_add_tcPr().append(shading_elm)
        
        # Đảm bảo responses đúng định dạng
        responses = submission.get("responses", {})
        if isinstance(responses, str):
            try:
                responses = json.loads(responses)
            except:
                responses = {}
        
        # Thêm dữ liệu câu trả lời với định dạng cải thiện
        for q in questions:
            q_id = str(q.get("id", ""))
            
            # Đáp án người dùng
            user_ans = responses.get(q_id, [])
            
            # Kiểm tra đúng/sai
            is_correct = check_answer_correctness(user_ans, q)
            if is_correct and q.get("type") != "Essay":
                total_correct += 1
            
            # Thêm hàng mới vào bảng
            row_cells = answers_table.add_row().cells
            
            # Thêm thông tin câu hỏi
            row_cells[0].text = f"Câu {q.get('id', '')}: {q.get('question', '')}"
            
            # Xử lý nội dung đáp án dựa trên loại câu hỏi
            if q.get("type") == "Essay":
                # Đối với câu hỏi tự luận
                essay_answer = user_ans[0] if user_ans else "Không trả lời"
                row_cells[1].text = essay_answer
                
                # Hiển thị nhận xét giáo viên nếu có
                essay_comment = essay_comments.get(q_id, "Chưa có nhận xét")
                row_cells[2].text = essay_comment
                
                # Điểm câu hỏi tự luận
                essay_score = essay_grades.get(q_id, 0)
                
                # Kết quả dựa trên việc học viên có trả lời hay không và đã chấm điểm chưa
                if is_correct:
                    if q_id in essay_grades:
                        result = "Đã chấm điểm"
                        points = essay_score
                    else:
                        result = "Chưa chấm điểm"
                        points = 0
                else:
                    result = "Không trả lời"
                    points = 0
                
                row_cells[3].text = result
                row_cells[4].text = str(points)
                
            else:
                # Đối với câu hỏi trắc nghiệm
                row_cells[1].text = ", ".join([str(a) for a in user_ans]) if user_ans else "Không trả lời"
                
                # Chuẩn bị đáp án đúng
                expected = get_correct_answers(q)
                
                row_cells[2].text = ", ".join([str(a) for a in expected])
                row_cells[3].text = "Đúng" if is_correct else "Sai"
                row_cells[4].text = str(q.get("score", 0) if is_correct else 0)
            
            # Đặt màu cho kết quả
            for paragraph in row_cells[3].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if not paragraph.runs:
                    paragraph.add_run(row_cells[3].text)
                run = paragraph.runs[0]
                if "Đúng" in row_cells[3].text or "Đã chấm điểm" in row_cells[3].text:
                    run.font.color.rgb = RGBColor(0, 128, 0)  # Màu xanh lá cho đúng
                    run.bold = True
                elif "Sai" in row_cells[3].text or "Không trả lời" in row_cells[3].text:
                    run.font.color.rgb = RGBColor(255, 0, 0)  # Màu đỏ cho sai
                    run.bold = True
                else:  # Trường hợp "Chưa chấm điểm"
                    run.font.color.rgb = RGBColor(255, 140, 0)  # Màu cam
                    run.bold = True
            
            # Căn giữa cột điểm
            row_cells[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Thêm tổng kết với định dạng rõ ràng
        doc.add_heading("Tổng kết", level=2)
        summary_table = doc.add_table(rows=3, cols=2, style='Table Grid')
        
        # Thiết lập độ rộng cho bảng tổng kết
        for cell in summary_table.columns[0].cells:
            cell.width = Inches(1.5)
        for cell in summary_table.columns[1].cells:
            cell.width = Inches(3.0)
        
        # Thêm màu nền cho cột tiêu đề
        for i in range(3):
            cell = summary_table.rows[i].cells[0]
            paragraph = cell.paragraphs[0]
            if not paragraph.runs:
                paragraph.add_run(cell.text if cell.text else '')
            paragraph.runs[0].font.bold = True
            shading_elm = parse_xml(r'<w:shd {} w:fill="E9E9E9"/>'.format(nsdecls('w')))
            cell._tc.get_or_add_tcPr().append(shading_elm)
        
        cells = summary_table.rows[0].cells
        cells[0].text = "Số câu đúng"
        cells[1].text = f"{total_correct}/{total_questions}"
        
        cells = summary_table.rows[1].cells
        cells[0].text = "Điểm số"
        cells[1].text = f"{submission.get('score', 0)}/{max_possible}"
        
        cells = summary_table.rows[2].cells
        cells[0].text = "Tỷ lệ đúng"
        cells[1].text = f"{(total_correct/total_questions*100):.1f}%" if total_questions > 0 else "0%"
        
        # Thêm chân trang
        doc.add_paragraph()
        footer = doc.add_paragraph("Xuất báo cáo từ Hệ thống Khảo sát & Đánh giá")
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        time_footer = doc.add_paragraph(f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        time_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Lưu tệp
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        print(f"Lỗi khi tạo báo cáo DOCX: {str(e)}")
        traceback.print_exc()
        # Trả về buffer trống nếu lỗi
        buffer = io.BytesIO()
        buffer.seek(0)
        return buffer

def create_student_report_pdf_fpdf(student_name, student_email, student_class, submission, questions, max_possible):
    """Tạo báo cáo chi tiết bài làm của học viên dạng PDF sử dụng FPDF2 với hỗ trợ Unicode, bao gồm câu tự luận"""
    buffer = io.BytesIO()
    
    try:
        # Tạo PDF mới
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Thiết lập font cho tiêu đề
        pdf.set_font('Arial', 'B', 16)
        title = f"Báo cáo chi tiết - {student_name}"
        pdf.cell(0, 10, title, 0, 1, 'C')
        
        # Thêm thời gian báo cáo
        pdf.set_font('Arial', 'I', 10)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pdf.cell(0, 5, f'Thời gian xuất báo cáo: {timestamp}', 0, 1, 'R')
        pdf.ln(5)
        
        # Tính toán thông tin về bài làm
        total_correct = 0
        total_questions = len(questions)
        
        # Đảm bảo responses đúng định dạng
        responses = submission.get("responses", {})
        if isinstance(responses, str):
            try:
                responses = json.loads(responses)
            except:
                responses = {}
                
        # Lấy điểm câu hỏi tự luận (nếu có)
        essay_grades = {}
        if "essay_grades" in submission:
            if isinstance(submission["essay_grades"], str):
                try:
                    essay_grades = json.loads(submission["essay_grades"])
                except:
                    essay_grades = {}
            else:
                essay_grades = submission.get("essay_grades", {})
                
        # Lấy nhận xét câu hỏi tự luận (nếu có)
        essay_comments = {}
        if "essay_comments" in submission:
            if isinstance(submission["essay_comments"], str):
                try:
                    essay_comments = json.loads(submission["essay_comments"])
                except:
                    essay_comments = {}
            else:
                essay_comments = submission.get("essay_comments", {})
        
        # Xử lý timestamp
        submission_time = format_timestamp(submission.get("timestamp"))
        
        # Thông tin học viên
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Thông tin học viên', 0, 1, 'L')
        
        # Bảng thông tin học viên
        pdf.set_font('Arial', '', 10)
        info_width = 190
        col1_width = 50
        col2_width = info_width - col1_width
        
        # Tạo khung thông tin học viên
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(col1_width, 10, 'Họ và tên', 1, 0, 'L', 1)
        pdf.cell(col2_width, 10, student_name, 1, 1, 'L')
        
        pdf.cell(col1_width, 10, 'Email', 1, 0, 'L', 1)
        pdf.cell(col2_width, 10, student_email, 1, 1, 'L')
        
        pdf.cell(col1_width, 10, 'Lớp', 1, 0, 'L', 1)
        pdf.cell(col2_width, 10, student_class, 1, 1, 'L')
        
        pdf.cell(col1_width, 10, 'Thời gian nộp', 1, 0, 'L', 1)
        pdf.cell(col2_width, 10, submission_time, 1, 1, 'L')
        
        pdf.ln(5)
        
        # Chi tiết câu trả lời
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Chi tiết câu trả lời', 0, 1, 'L')
        
        # Tiêu đề bảng chi tiết
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(240, 240, 240)
        
        # Xác định độ rộng cột
        q_width = 65
        user_width = 35
        correct_width = 40
        result_width = 25
        points_width = 15
        
        # Vẽ header bảng
        pdf.cell(q_width, 10, 'Câu hỏi', 1, 0, 'C', 1)
        pdf.cell(user_width, 10, 'Đáp án học viên', 1, 0, 'C', 1)
        pdf.cell(correct_width, 10, 'Đáp án đúng/Nhận xét', 1, 0, 'C', 1)
        pdf.cell(result_width, 10, 'Kết quả', 1, 0, 'C', 1)
        pdf.cell(points_width, 10, 'Điểm', 1, 1, 'C', 1)
        
        # Vẽ dữ liệu câu trả lời
        pdf.set_font('Arial', '', 9)
        
        for q in questions:
            q_id = str(q.get("id", ""))
            
            # Đáp án người dùng
            user_ans = responses.get(q_id, [])
            
            # Kiểm tra đúng/sai
            is_correct = check_answer_correctness(user_ans, q)
            if is_correct and q.get("type") != "Essay":
                total_correct += 1
            
            # Chuẩn bị nội dung dựa trên loại câu hỏi
            question_text = f"Câu {q.get('id', '')}: {q.get('question', '')}"
            
            if q.get("type") == "Essay":
                # Đối với câu hỏi tự luận
                essay_answer = user_ans[0] if user_ans else "Không trả lời"
                user_answer_text = essay_answer[:50] + "..." if len(essay_answer) > 50 else essay_answer
                
                # Nhận xét của giáo viên
                essay_comment = essay_comments.get(q_id, "Chưa có nhận xét")
                correct_answer_text = essay_comment[:50] + "..." if len(essay_comment) > 50 else essay_comment
                
                # Điểm câu hỏi tự luận
                essay_score = essay_grades.get(q_id, 0)
                
                # Kết quả chấm điểm
                if is_correct:
                    if q_id in essay_grades:
                        result = "Đã chấm điểm"
                        points = essay_score
                    else:
                        result = "Chưa chấm điểm"
                        points = 0
                else:
                    result = "Không trả lời"
                    points = 0
            else:
                # Đối với câu hỏi trắc nghiệm
                user_answer_text = ", ".join([str(a) for a in user_ans]) if user_ans else "Không trả lời"
                
                # Chuẩn bị đáp án đúng
                expected = get_correct_answers(q)
                correct_answer_text = ", ".join([str(a) for a in expected])
                result = "Đúng" if is_correct else "Sai"
                points = q.get("score", 0) if is_correct else 0
            
            # Vẽ dữ liệu (đơn giản hóa để tránh lỗi)
            row_height = 10
            
            # Lưu vị trí x hiện tại
            x = pdf.get_x()
            y = pdf.get_y()
            
            # Kiểm tra nếu sẽ vượt quá trang
            if y + row_height > pdf.page_break_trigger:
                pdf.add_page()
                y = pdf.get_y()
            
            # Vẽ từng ô
            pdf.set_xy(x, y)
            pdf.cell(q_width, row_height, question_text[:30] + "..." if len(question_text) > 30 else question_text, 1, 0, 'L')
            
            pdf.set_xy(x + q_width, y)
            pdf.cell(user_width, row_height, user_answer_text[:20] + "..." if len(user_answer_text) > 20 else user_answer_text, 1, 0, 'L')
            
            pdf.set_xy(x + q_width + user_width, y)
            pdf.cell(correct_width, row_height, correct_answer_text[:25] + "..." if len(correct_answer_text) > 25 else correct_answer_text, 1, 0, 'L')
            
            pdf.set_xy(x + q_width + user_width + correct_width, y)
            pdf.cell(result_width, row_height, result, 1, 0, 'C')
            
            pdf.set_xy(x + q_width + user_width + correct_width + result_width, y)
            pdf.cell(points_width, row_height, str(points), 1, 1, 'C')
        
        pdf.ln(5)
        
        # Tổng kết
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Tổng kết', 0, 1, 'L')
        
        # Bảng tổng kết
        pdf.set_font('Arial', '', 10)
        pdf.set_fill_color(240, 240, 240)
        
        summary_col1 = 50
        summary_col2 = 140
        
        pdf.cell(summary_col1, 10, 'Số câu đúng', 1, 0, 'L', 1)
        pdf.cell(summary_col2, 10, f"{total_correct}/{total_questions}", 1, 1, 'L')
        
        pdf.cell(summary_col1, 10, 'Điểm số', 1, 0, 'L', 1)
        pdf.cell(summary_col2, 10, f"{submission.get('score', 0)}/{max_possible}", 1, 1, 'L')
        
        pdf.cell(summary_col1, 10, 'Tỷ lệ đúng', 1, 0, 'L', 1)
        percent = total_correct/total_questions*100 if total_questions > 0 else 0
        pdf.cell(summary_col2, 10, f"{percent:.1f}% {'(Đạt)' if percent >= 50 else '(Chưa đạt)'}", 1, 1, 'L')
        
        # Lưu PDF vào buffer
        pdf.output(buffer)
    except Exception as e:
        print(f"Lỗi khi tạo báo cáo PDF: {str(e)}")
        traceback.print_exc()
        
        # Tạo báo cáo đơn giản nếu gặp lỗi
        try:
            simple_pdf = FPDF()
            simple_pdf.add_page()
            simple_pdf.set_font('Arial', 'B', 16)
            simple_pdf.cell(0, 10, f'Báo cáo chi tiết - {student_name}', 0, 1, 'C')
            simple_pdf.set_font('Arial', '', 10)
            error_text = f'Không thể hiển thị báo cáo chi tiết. Vui lòng sử dụng định dạng DOCX.\nLỗi: {str(e)}'
            simple_pdf.multi_cell(0, 10, error_text, 0, 'L')
            simple_pdf.output(buffer)
        except Exception as e2:
            print(f"Không thể tạo báo cáo thay thế: {str(e2)}")
    
    buffer.seek(0)
    return buffer

def dataframe_to_docx(df, title, filename):
    """Tạo file DOCX từ DataFrame"""
    try:
        doc = Document()
        
        # Thiết lập font chữ mặc định
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Thêm tiêu đề
        heading = doc.add_heading(title, level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Thêm thời gian xuất báo cáo
        time_paragraph = doc.add_paragraph(f"Thời gian xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        time_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Tạo bảng
        # Thêm một hàng cho tiêu đề cột
        table = doc.add_table(rows=1, cols=len(df.columns), style='Table Grid')
        
        # Thêm tiêu đề cột
        header_cells = table.rows[0].cells
        for i, col_name in enumerate(df.columns):
            header_cells[i].text = str(col_name)
            # Đặt kiểu cho tiêu đề
            for paragraph in header_cells[i].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = paragraph.runs[0] if paragraph.runs else paragraph.add_run(str(col_name))
                run.bold = True
        
        # Thêm dữ liệu
        for _, row in df.iterrows():
            row_cells = table.add_row().cells
            for i, value in enumerate(row):
                row_cells[i].text = str(value)
                # Căn giữa cho các ô
                for paragraph in row_cells[i].paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Thêm chân trang
        doc.add_paragraph()
        footer = doc.add_paragraph("Hệ thống Khảo sát & Đánh giá")
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Lưu tệp
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        print(f"Lỗi khi tạo DOCX: {str(e)}")
        st.error(f"Không thể tạo file DOCX: {str(e)}")
        # Trả về buffer trống nếu lỗi
        buffer = io.BytesIO()
        buffer.seek(0)
        return buffer

def dataframe_to_pdf_fpdf(df, title, filename):
    """Tạo file PDF từ DataFrame sử dụng FPDF2"""
    buffer = io.BytesIO()
    
    try:
        # Xác định hướng trang dựa vào số lượng cột
        orientation = 'L' if len(df.columns) > 5 else 'P'
        
        pdf = FPDF(orientation=orientation, unit='mm', format='A4')
        pdf.add_page()
        
        # Thêm tiêu đề
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, title, 0, 1, 'C')
        
        # Thêm thời gian báo cáo
        pdf.set_font('Arial', 'I', 10)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pdf.cell(0, 5, f'Thời gian xuất báo cáo: {timestamp}', 0, 1, 'R')
        pdf.ln(5)
        
        # Xác định kích thước trang và số cột
        page_width = 297 if orientation == 'L' else 210
        margin = 10
        usable_width = page_width - 2*margin
        
        # Tính toán độ rộng cột
        col_count = len(df.columns)
        col_width = usable_width / col_count if col_count > 0 else 20
        
        # Mặc định font cho nội dung
        pdf.set_font('Arial', '', 8)
        
        # Tạo tiêu đề cột
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(240, 240, 240)
        
        for col_name in df.columns:
            # Cắt ngắn tên cột nếu quá dài
            display_name = str(col_name)[:15] + "..." if len(str(col_name)) > 15 else str(col_name)
            pdf.cell(col_width, 8, display_name, 1, 0, 'C', 1)
        pdf.ln()
        
        # Vẽ nội dung
        pdf.set_font('Arial', '', 8)
        
        # Giới hạn số lượng hàng
        max_rows = min(100, len(df))
        
        for i in range(max_rows):
            for j, col in enumerate(df.columns):
                content = str(df.iloc[i, j])
                # Cắt ngắn nội dung nếu quá dài
                display_content = content[:20] + "..." if len(content) > 20 else content
                pdf.cell(col_width, 6, display_content, 1, 0, 'L')
            pdf.ln()
        
        # Lưu PDF vào buffer
        pdf.output(buffer)
        
    except Exception as e:
        print(f"Lỗi khi tạo báo cáo PDF: {str(e)}")
        traceback.print_exc()
        
        # Tạo báo cáo đơn giản nếu gặp lỗi
        try:
            simple_pdf = FPDF()
            simple_pdf.add_page()
            simple_pdf.set_font('Arial', 'B', 16)
            simple_pdf.cell(0, 10, title, 0, 1, 'C')
            simple_pdf.set_font('Arial', '', 10)
            simple_pdf.multi_cell(0, 10, f'Không thể tạo báo cáo chi tiết.\nLỗi: {str(e)}', 0, 'L')
            simple_pdf.output(buffer)
        except Exception as e2:
            print(f"Không thể tạo báo cáo thay thế: {str(e2)}")
    
    buffer.seek(0)
    return buffer

def format_date(date_value):
    """Định dạng ngày tháng từ nhiều kiểu dữ liệu khác nhau"""
    if not date_value:
        return "N/A"
    
    try:
        # Nếu là số nguyên (timestamp)
        if isinstance(date_value, (int, float)):
            return datetime.fromtimestamp(date_value).strftime("%d/%m/%Y")
        
        # Nếu là chuỗi ISO (từ Supabase)
        elif isinstance(date_value, str):
            try:
                # Thử parse chuỗi ISO
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return dt.strftime("%d/%m/%Y")
            except:
                # Nếu không phải ISO, trả về nguyên bản
                return date_value
        
        # Nếu đã là đối tượng datetime
        elif isinstance(date_value, datetime):
            return date_value.strftime("%d/%m/%Y")
            
        # Các trường hợp khác, trả về dạng chuỗi
        else:
            return str(date_value)
    except Exception as e:
        print(f"Error formatting date: {e}, value type: {type(date_value)}, value: {date_value}")
        return "N/A"

def create_class_report(class_name, submissions, students, questions, max_possible):
    """Tạo báo cáo tổng hợp theo lớp"""
    try:
        doc = Document()
        
        # Thiết lập font chữ mặc định
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Thêm tiêu đề
        heading = doc.add_heading(f"Báo cáo tổng hợp lớp {class_name}", level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Thêm thời gian xuất báo cáo
        time_paragraph = doc.add_paragraph(f"Thời gian xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        time_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Thông tin tổng quan
        doc.add_heading("Tổng quan", level=2)
        
        class_students = [s for s in students if s.get("class") == class_name]
        class_submissions = [s for s in submissions if any(st.get("email") == s.get("user_email") for st in class_students)]
        
        info_table = doc.add_table(rows=5, cols=2, style='Table Grid')
        
        # Thiết lập độ rộng cột
        for cell in info_table.columns[0].cells:
            cell.width = Inches(2)
        for cell in info_table.columns[1].cells:
            cell.width = Inches(4)
        
        # Thêm dữ liệu
        rows_data = [
            ("Tên lớp", class_name),
            ("Số học viên", str(len(class_students))),
            ("Số bài nộp", str(len(class_submissions))),
            ("Điểm trung bình", f"{sum(s.get('score', 0) for s in class_submissions) / len(class_submissions):.2f}/{max_possible}" if class_submissions else "0"),
            ("Ngày xuất báo cáo", datetime.now().strftime('%d/%m/%Y'))
        ]
        
        for i, (label, value) in enumerate(rows_data):
            cells = info_table.rows[i].cells
            cells[0].text = label
            cells[1].text = value
            
            # Đặt in đậm cho cột đầu
            cells[0].paragraphs[0].runs[0].bold = True
        
        # Bảng kết quả chi tiết
        doc.add_heading("Kết quả chi tiết", level=2)
        
        if class_submissions:
            # Tạo bảng kết quả
            results_table = doc.add_table(rows=1, cols=5, style='Table Grid')
            
            # Header
            header_cells = results_table.rows[0].cells
            headers = ["Họ tên", "Email", "Thời gian nộp", "Điểm số", "Tỷ lệ (%)"]
            
            for i, header in enumerate(headers):
                header_cells[i].text = header
                header_cells[i].paragraphs[0].runs[0].bold = True
                header_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Dữ liệu
            for submission in class_submissions:
                row_cells = results_table.add_row().cells
                
                # Tìm thông tin học viên
                student_info = next((s for s in class_students if s.get("email") == submission.get("user_email")), None)
                student_name = student_info.get("full_name", "Không xác định") if student_info else "Không xác định"
                
                # Xử lý timestamp
                timestamp = submission.get("timestamp", "")
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        submit_time = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        submit_time = "Không xác định"
                else:
                    try:
                        submit_time = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
                    except:
                        submit_time = "Không xác định"
                
                score = submission.get("score", 0)
                percentage = (score / max_possible * 100) if max_possible > 0 else 0
                
                row_cells[0].text = student_name
                row_cells[1].text = submission.get("user_email", "")
                row_cells[2].text = submit_time
                row_cells[3].text = f"{score}/{max_possible}"
                row_cells[4].text = f"{percentage:.1f}%"
                
                # Căn giữa các ô
                for cell in row_cells:
                    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Thống kê theo câu hỏi
        doc.add_heading("Thống kê theo câu hỏi", level=2)
        
        question_stats = {}
        for q in questions:
            q_id = str(q.get("id"))
            correct_count = 0
            total_count = 0
            
            for submission in class_submissions:
                responses = submission.get("responses", {})
                if isinstance(responses, str):
                    try:
                        responses = json.loads(responses)
                    except:
                        responses = {}
                
                if q_id in responses:
                    total_count += 1
                    user_ans = responses[q_id]
                    if check_answer_correctness(user_ans, q):
                        correct_count += 1
            
            if total_count > 0:
                question_stats[q_id] = {
                    "question": q.get("question", ""),
                    "correct": correct_count,
                    "total": total_count,
                    "percentage": (correct_count / total_count) * 100
                }
        
        if question_stats:
            stats_table = doc.add_table(rows=1, cols=4, style='Table Grid')
            
            # Header
            header_cells = stats_table.rows[0].cells
            headers = ["Câu hỏi", "Số câu đúng", "Tổng số", "Tỷ lệ đúng (%)"]
            
            for i, header in enumerate(headers):
                header_cells[i].text = header
                header_cells[i].paragraphs[0].runs[0].bold = True
                header_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Dữ liệu
            for q_id, stats in question_stats.items():
                row_cells = stats_table.add_row().cells
                
                row_cells[0].text = f"Câu {q_id}: {stats['question'][:50]}..."
                row_cells[1].text = str(stats['correct'])
                row_cells[2].text = str(stats['total'])
                row_cells[3].text = f"{stats['percentage']:.1f}%"
                
                # Căn giữa các ô số
                for i in range(1, 4):
                    row_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Chân trang
        doc.add_paragraph()
        footer = doc.add_paragraph("Báo cáo được tạo bởi Hệ thống Khảo sát & Đánh giá")
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Lưu tệp
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        print(f"Lỗi khi tạo báo cáo lớp: {str(e)}")
        buffer = io.BytesIO()
        buffer.seek(0)
        return buffer

def create_overall_report(submissions, students, questions, max_possible):
    """Tạo báo cáo tổng hợp toàn bộ hệ thống"""
    try:
        doc = Document()
        
        # Thiết lập font chữ mặc định
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Thêm tiêu đề
        heading = doc.add_heading("Báo cáo tổng hợp hệ thống", level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Thêm thời gian xuất báo cáo
        time_paragraph = doc.add_paragraph(f"Thời gian xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        time_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Thông tin tổng quan
        doc.add_heading("Thông tin tổng quan", level=2)
        
        # Thống kê cơ bản
        total_students = len(students)
        total_submissions = len(submissions)
        avg_score = sum(s.get('score', 0) for s in submissions) / len(submissions) if submissions else 0
        
        # Thống kê theo lớp
        classes = {}
        for student in students:
            class_name = student.get("class", "Không xác định")
            if class_name not in classes:
                classes[class_name] = 0
            classes[class_name] += 1
        
        info_table = doc.add_table(rows=6, cols=2, style='Table Grid')
        
        rows_data = [
            ("Tổng số học viên", str(total_students)),
            ("Tổng số bài nộp", str(total_submissions)),
            ("Điểm trung bình", f"{avg_score:.2f}/{max_possible}"),
            ("Số lớp tham gia", str(len(classes))),
            ("Số câu hỏi", str(len(questions))),
            ("Ngày xuất báo cáo", datetime.now().strftime('%d/%m/%Y'))
        ]
        
        for i, (label, value) in enumerate(rows_data):
            cells = info_table.rows[i].cells
            cells[0].text = label
            cells[1].text = value
            cells[0].paragraphs[0].runs[0].bold = True
        
        # Thống kê theo lớp
        doc.add_heading("Thống kê theo lớp", level=2)
        
        class_table = doc.add_table(rows=1, cols=4, style='Table Grid')
        
        # Header
        header_cells = class_table.rows[0].cells
        headers = ["Lớp", "Số học viên", "Số bài nộp", "Điểm trung bình"]
        
        for i, header in enumerate(headers):
            header_cells[i].text = header
            header_cells[i].paragraphs[0].runs[0].bold = True
            header_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Dữ liệu theo lớp
        for class_name, student_count in classes.items():
            class_students = [s for s in students if s.get("class") == class_name]
            class_submissions = [s for s in submissions if any(st.get("email") == s.get("user_email") for st in class_students)]
            
            class_avg = sum(s.get('score', 0) for s in class_submissions) / len(class_submissions) if class_submissions else 0
            
            row_cells = class_table.add_row().cells
            row_cells[0].text = class_name
            row_cells[1].text = str(student_count)
            row_cells[2].text = str(len(class_submissions))
            row_cells[3].text = f"{class_avg:.2f}/{max_possible}"
            
            for i in range(1, 4):
                row_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Top 10 học viên
        doc.add_heading("Top 10 học viên xuất sắc", level=2)
        
        # Tính điểm cao nhất của mỗi học viên
        student_best_scores = {}
        for submission in submissions:
            email = submission.get("user_email")
            score = submission.get("score", 0)
            
            if email not in student_best_scores or score > student_best_scores[email]["score"]:
                student_info = next((s for s in students if s.get("email") == email), None)
                student_best_scores[email] = {
                    "score": score,
                    "name": student_info.get("full_name", "Không xác định") if student_info else "Không xác định",
                    "class": student_info.get("class", "Không xác định") if student_info else "Không xác định"
                }
        
        # Sắp xếp và lấy top 10
        top_students = sorted(student_best_scores.values(), key=lambda x: x["score"], reverse=True)[:10]
        
        if top_students:
            top_table = doc.add_table(rows=1, cols=4, style='Table Grid')
            
            # Header
            header_cells = top_table.rows[0].cells
            headers = ["Hạng", "Họ tên", "Lớp", "Điểm cao nhất"]
            
            for i, header in enumerate(headers):
                header_cells[i].text = header
                header_cells[i].paragraphs[0].runs[0].bold = True
                header_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Dữ liệu
            for i, student in enumerate(top_students):
                row_cells = top_table.add_row().cells
                row_cells[0].text = str(i + 1)
                row_cells[1].text = student["name"]
                row_cells[2].text = student["class"]
                row_cells[3].text = f"{student['score']}/{max_possible}"
                
                for cell in row_cells:
                    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Chân trang
        doc.add_paragraph()
        footer = doc.add_paragraph("Báo cáo được tạo bởi Hệ thống Khảo sát & Đánh giá")
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Lưu tệp
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        print(f"Lỗi khi tạo báo cáo tổng hợp: {str(e)}")
        buffer = io.BytesIO()
        buffer.seek(0)
        return buffer

# ===============================
# CÁC HÀM TƯƠNG THÍCH
# ===============================

def get_submission_statistics():
    """Lấy thống kê submissions - để tương thích với code cũ"""
    try:
        submissions = get_all_submissions()
        if not submissions:
            return {
                "total_submissions": 0,
                "student_count": 0,
                "avg_score": 0,
                "total_possible_score": 0,
                "daily_counts": {}
            }
        
        # Tính thống kê
        total_submissions = len(submissions)
        unique_students = len(set([s.get("user_email") for s in submissions]))
        scores = [s.get("score", 0) for s in submissions]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Tính tổng điểm có thể
        questions = get_all_questions()
        total_possible_score = sum([q.get("score", 0) for q in questions])
        
        # Thống kê theo ngày
        daily_counts = {}
        for s in submissions:
            timestamp = s.get("timestamp")
            if timestamp:
                try:
                    if isinstance(timestamp, (int, float)):
                        date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                    else:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        date_str = dt.strftime("%Y-%m-%d")
                    
                    daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
                except:
                    continue
        
        return {
            "total_submissions": total_submissions,
            "student_count": unique_students,
            "avg_score": avg_score,
            "total_possible_score": total_possible_score,
            "daily_counts": daily_counts
        }
        
    except Exception as e:
        print(f"Lỗi khi lấy submission statistics: {str(e)}")
        return {
            "total_submissions": 0,
            "student_count": 0,
            "avg_score": 0,
            "total_possible_score": 0,
            "daily_counts": {}
        }

# Chỉ chạy hàm main khi chạy file này trực tiếp
if __name__ == "__main__":
    st.set_page_config(
        page_title="Báo cáo & Thống kê",
        page_icon="📊",
        layout="wide",
    )
    view_statistics()
