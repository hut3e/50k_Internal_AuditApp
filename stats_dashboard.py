import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

# Import từ các module khác
from database_helper import get_all_questions, get_user_submissions, get_submission_statistics, check_answer_correctness

def stats_dashboard():
    """Hiển thị trang thống kê và báo cáo"""
    st.title("Thống kê và Báo cáo")
    
    # Lấy dữ liệu thống kê
    stats = get_submission_statistics()
    
    if not stats:
        st.error("Không thể lấy dữ liệu thống kê. Vui lòng thử lại sau.")
        return
    
    # Hiển thị các chỉ số quan trọng
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số bài nộp", stats["total_submissions"])
    col2.metric("Số học viên đã làm bài", stats["student_count"])
    col3.metric(f"Điểm trung bình ({stats['total_possible_score']} điểm)", f"{stats['avg_score']:.1f} ({stats['avg_percentage']:.1f}%)")
    
    # Thêm các tab thống kê
    tab1, tab2, tab3 = st.tabs(["Thống kê chung", "Phân tích câu hỏi", "Dữ liệu học viên"])
    
    with tab1:
        general_statistics(stats)
    
    with tab2:
        question_analysis(stats)
    
    with tab3:
        student_data_analysis()

def general_statistics(stats):
    """Hiển thị thống kê chung về bài làm"""
    st.subheader("Thống kê chung")
    
    # Tạo biểu đồ số lượng bài nộp theo ngày
    st.write("### Số lượng bài nộp theo ngày")
    
    daily_counts = stats["daily_counts"]
    
    if daily_counts:
        dates = list(daily_counts.keys())
        counts = list(daily_counts.values())
        
        # Sắp xếp theo ngày
        sorted_data = sorted(zip(dates, counts), key=lambda x: x[0])
        dates, counts = zip(*sorted_data) if sorted_data else ([], [])
        
        # Tạo DataFrame cho dễ vẽ biểu đồ
        df = pd.DataFrame({
            'Ngày': dates,
            'Số lượng': counts
        })
        
        # Vẽ biểu đồ
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(df['Ngày'], df['Số lượng'], color='skyblue')
        ax.set_xlabel('Ngày')
        ax.set_ylabel('Số lượng bài nộp')
        ax.set_title('Số lượng bài nộp theo ngày')
        plt.xticks(rotation=45)
        
        # Sử dụng constrained_layout thay vì tight_layout để tránh lỗi
        fig.set_constrained_layout(True)
        
        # Hiển thị biểu đồ
        st.pyplot(fig)
        
        # Hiển thị dữ liệu dạng bảng
        st.write("### Dữ liệu chi tiết")
        st.dataframe(df)
        
        # Tính toán thống kê mô tả
        avg_submissions = sum(counts) / len(counts) if counts else 0
        max_submissions = max(counts) if counts else 0
        max_date = dates[counts.index(max_submissions)] if counts else "N/A"
        
        st.write(f"- Trung bình: {avg_submissions:.1f} bài nộp/ngày")
        st.write(f"- Ngày có nhiều bài nộp nhất: {max_date} ({max_submissions} bài)")
    else:
        st.info("Chưa có dữ liệu bài nộp.")

def question_analysis(stats):
    """Phân tích câu hỏi và tỷ lệ trả lời đúng"""
    st.subheader("Phân tích câu hỏi")
    
    question_stats = stats.get("question_stats", {})
    
    if question_stats:
        # Tạo dữ liệu cho biểu đồ
        q_ids = []
        correct_rates = []
        questions = []
        
        for q_id, q_stat in question_stats.items():
            q_ids.append(q_id)
            correct_rates.append(q_stat["correct_percentage"])
            questions.append(q_stat["question"])
        
        # Tạo DataFrame
        df = pd.DataFrame({
            'ID': q_ids,
            'Câu hỏi': questions,
            'Tỷ lệ đúng (%)': correct_rates,
            'Số người trả lời': [question_stats[q_id]["total_answers"] for q_id in q_ids],
            'Số người trả lời đúng': [question_stats[q_id]["correct_count"] for q_id in q_ids]
        })
        
        # Giới hạn độ dài của câu hỏi để tránh lỗi hiển thị
        df['Câu hỏi hiển thị'] = df['Câu hỏi'].apply(lambda x: x[:50] + '...' if len(x) > 50 else x)
        
        # Vẽ biểu đồ
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(df['Câu hỏi hiển thị'], df['Tỷ lệ đúng (%)'], color='skyblue')
        ax.set_xlabel('Tỷ lệ trả lời đúng (%)')
        ax.set_title('Tỷ lệ trả lời đúng theo câu hỏi')
        ax.set_xlim(0, 100)
        
        # Thêm nhãn giá trị vào cuối mỗi thanh
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 2, bar.get_y() + bar.get_height()/2, f'{width:.1f}%',
                    va='center', fontsize=8)
        
        # Sử dụng constrained_layout thay vì tight_layout
        fig.set_constrained_layout(True)
        st.pyplot(fig)
        
        # Hiển thị dữ liệu dạng bảng
        st.write("### Dữ liệu kết quả kiểm tra chi tiết")
        
        # Sắp xếp theo tỷ lệ đúng tăng dần
        df_sorted = df.sort_values('Tỷ lệ đúng (%)')
        display_df = df_sorted[['ID', 'Câu hỏi', 'Tỷ lệ đúng (%)', 'Số người trả lời', 'Số người trả lời đúng']]
        st.dataframe(display_df)
        
        # Phân tích câu hỏi khó và dễ
        st.write("### Phân tích câu hỏi")
        
        # Câu hỏi khó nhất (tỷ lệ đúng thấp nhất)
        hardest = df.iloc[df['Tỷ lệ đúng (%)'].idxmin()]
        st.write(f"**Câu hỏi khó nhất:** {hardest['Câu hỏi']} (ID: {hardest['ID']})")
        st.write(f"- Tỷ lệ đúng: {hardest['Tỷ lệ đúng (%)']:.1f}%")
        st.write(f"- Số người trả lời: {hardest['Số người trả lời']}")
        
        # Câu hỏi dễ nhất (tỷ lệ đúng cao nhất)
        easiest = df.iloc[df['Tỷ lệ đúng (%)'].idxmax()]
        st.write(f"**Câu hỏi dễ nhất:** {easiest['Câu hỏi']} (ID: {easiest['ID']})")
        st.write(f"- Tỷ lệ đúng: {easiest['Tỷ lệ đúng (%)']:.1f}%")
        st.write(f"- Số người trả lời: {easiest['Số người trả lời']}")
        
        # Gợi ý cải thiện
        st.write("### Gợi ý cải thiện")
        
        # Các câu hỏi có tỷ lệ đúng quá thấp
        very_hard = df[df['Tỷ lệ đúng (%)'] < 30]
        if not very_hard.empty:
            st.write("**Câu hỏi nên xem xét lại (tỷ lệ đúng < 30%):**")
            for _, row in very_hard.iterrows():
                st.write(f"- {row['Câu hỏi']} (ID: {row['ID']}, Tỷ lệ đúng: {row['Tỷ lệ đúng (%)']:.1f}%)")
        
        # Các câu hỏi có tỷ lệ đúng quá cao
        very_easy = df[df['Tỷ lệ đúng (%)'] > 90]
        if not very_easy.empty:
            st.write("**Câu hỏi có thể quá dễ (tỷ lệ đúng > 90%):**")
            for _, row in very_easy.iterrows():
                st.write(f"- {row['Câu hỏi']} (ID: {row['ID']}, Tỷ lệ đúng: {row['Tỷ lệ đúng (%)']:.1f}%)")
    else:
        st.info("Chưa có dữ liệu để phân tích câu hỏi.")

def student_data_analysis():
    """Phân tích dữ liệu học viên"""
    st.subheader("Dữ liệu học viên")
    
    # Tạo form tìm kiếm
    with st.form("student_search_form"):
        email = st.text_input("Nhập email học viên để xem chi tiết:")
        submit_button = st.form_submit_button("Tìm kiếm")
    
    if submit_button and email:
        # Lấy dữ liệu bài làm của học viên
        submissions = get_user_submissions(email)
        
        if submissions:
            st.success(f"Đã tìm thấy {len(submissions)} bài làm của học viên {email}")
            
            # Lấy danh sách câu hỏi
            questions = get_all_questions()
            
            # Tính điểm tối đa
            max_score = sum([q.get("score", 0) for q in questions])
            
            # Hiển thị thông tin tổng quan
            st.write("### Thông tin tổng quan kết quả kiểm tra")
            
            # Tính điểm cao nhất
            max_student_score = max([s.get("score", 0) for s in submissions])
            max_percentage = (max_student_score / max_score) * 100 if max_score > 0 else 0
            
            # Tính điểm trung bình
            avg_student_score = sum([s.get("score", 0) for s in submissions]) / len(submissions)
            avg_percentage = (avg_student_score / max_score) * 100 if max_score > 0 else 0
            
            col1, col2 = st.columns(2)
            col1.metric("Số lần làm bài", len(submissions))
            col2.metric("Điểm cao nhất", f"{max_student_score}/{max_score} ({max_percentage:.1f}%)")
            
            # Hiển thị tiến triển qua các lần làm
            st.write("### Tiến triển điểm số")
            
            # Chuẩn bị dữ liệu cho biểu đồ
            attempts = [f"Lần {i+1}" for i in range(len(submissions))]
            scores = [s.get("score", 0) for s in submissions]
            percentages = [(s.get("score", 0) / max_score) * 100 for s in submissions]
            
            # Vẽ biểu đồ
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(attempts, percentages, marker='o', linestyle='-', color='skyblue')
            ax.set_xlabel('Lần thử')
            ax.set_ylabel('Tỷ lệ điểm (%)')
            ax.set_title('Tiến triển điểm số qua các lần làm')
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_ylim(0, 100)
            
            # Thêm nhãn giá trị cho mỗi điểm
            for i, (x, y) in enumerate(zip(attempts, percentages)):
                ax.text(x, y + 3, f"{y:.1f}%", ha='center', va='bottom', fontsize=9)
            
            # Sử dụng constrained_layout thay vì tight_layout
            fig.set_constrained_layout(True)
            st.pyplot(fig)
            
            # Hiển thị chi tiết từng lần làm
            st.write("### Chi tiết các lần làm")
            
            for idx, s in enumerate(submissions):
                # Xử lý timestamp
                if isinstance(s.get("timestamp"), (int, float)):
                    # Trường hợp timestamp là số (dữ liệu cũ)
                    try:
                        submission_time = datetime.fromtimestamp(s.get("timestamp")).strftime("%H:%M:%S %d/%m/%Y")
                    except:
                        submission_time = "Không xác định"
                else:
                    # Trường hợp timestamp là chuỗi ISO (dữ liệu mới)
                    try:
                        # Chuyển từ chuỗi ISO sang đối tượng datetime
                        dt = datetime.fromisoformat(s.get("timestamp", "").replace("Z", "+00:00"))
                        submission_time = dt.strftime("%H:%M:%S %d/%m/%Y")
                    except Exception as e:
                        # Trong trường hợp không thể parse được timestamp
                        submission_time = "Không xác định"
                        print(f"Lỗi parse timestamp: {e}, giá trị: {s.get('timestamp')}")
                
                score_percent = (s.get("score", 0) / max_score) * 100 if max_score > 0 else 0
                
                with st.expander(f"Lần {idx + 1}: {submission_time} - Điểm: {s.get('score', 0)}/{max_score} ({score_percent:.1f}%)"):
                    # Đảm bảo responses đúng định dạng
                    responses = s.get("responses", {})
                    if isinstance(responses, str):
                        try:
                            responses = json.loads(responses)
                        except:
                            responses = {}
                    
                    # Phân tích câu trả lời
                    correct_count = 0
                    for q in questions:
                        q_id = str(q.get("id", ""))
                        student_answers = responses.get(q_id, [])
                        
                        # Đảm bảo câu hỏi có định dạng đúng
                        if isinstance(q.get("answers"), str):
                            try:
                                q["answers"] = json.loads(q.get("answers"))
                            except:
                                q["answers"] = [q.get("answers")]
                        
                        if isinstance(q.get("correct"), str):
                            try:
                                q["correct"] = json.loads(q.get("correct"))
                            except:
                                try:
                                    q["correct"] = [int(x.strip()) for x in q.get("correct", "").split(",")]
                                except:
                                    q["correct"] = []
                        
                        # Kiểm tra tính đúng đắn
                        is_correct = check_answer_correctness(student_answers, q)
                        if is_correct:
                            correct_count += 1
                        
                        # Hiển thị đáp án người dùng đã chọn
                        st.write(f"**Câu {q.get('id')}: {q.get('question')}**")
                        st.write("Đáp án đã chọn:")
                        if not student_answers:
                            st.write("- Không trả lời")
                        else:
                            for ans in student_answers:
                                st.write(f"- {ans}")
                        
                        # Hiển thị kết quả
                        if is_correct:
                            st.success(f"✅ Đúng (+{q.get('score', 0)} điểm)")
                        else:
                            st.error("❌ Sai (0 điểm)")
                            expected_indices = q.get("correct", [])
                            expected_answers = []
                            try:
                                expected_answers = [q.get("answers", [])[i - 1] for i in expected_indices]
                            except IndexError:
                                expected_answers = ["Lỗi đáp án"]
                                
                            st.write("Đáp án đúng:")
                            for ans in expected_answers:
                                st.write(f"- {ans}")
                        
                        st.divider()
                    
                    # Tổng kết
                    total_questions = len(questions) if questions else 1  # Tránh chia cho 0
                    accuracy = (correct_count / total_questions) * 100
                    st.write(f"**Tổng kết:** {correct_count}/{total_questions} câu đúng ({accuracy:.1f}%)")
        else:
            st.error(f"Không tìm thấy dữ liệu của học viên với email: {email}")
    else:
        # Nếu chưa tìm kiếm, hiển thị một số thống kê chung về học viên
        st.info("Nhập email học viên và nhấn Tìm kiếm để xem chi tiết bài làm.")
        
        # Hiển thị tổng số học viên đã làm bài
        stats = get_submission_statistics()
        if stats:
            st.write(f"**Tổng số học viên đã làm bài:** {stats.get('student_count', 0)}")
            st.write(f"**Điểm trung bình của tất cả học viên:** {stats.get('avg_score', 0):.1f}/{stats.get('total_possible_score', 0)} ({stats.get('avg_percentage', 0):.1f}%)")
            
            # Các gợi ý phân tích thêm
            st.write("""
            ### Các phân tích có thể thực hiện:
            - Phân bố điểm số các học viên
            - Thời gian trung bình giữa các lần làm
            - Mức độ cải thiện qua các lần làm
            - Câu hỏi nào gây khó khăn nhất cho học viên
            """)