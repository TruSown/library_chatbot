import streamlit as st
import json
import google.generativeai as genai
import os

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="Thư viện số Vinschool",
    page_icon="📚",
    layout="centered"
)

# --- CẤU HÌNH API (Đã sửa lỗi) ---
# Cách hoạt động: Streamlit sẽ tìm biến tên là "GOOGLE_API_KEY" trong secrets
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("⚠️ Lỗi: Chưa tìm thấy 'GOOGLE_API_KEY' trong Secrets.")
        st.stop() # Dừng chương trình nếu không có key
except Exception as e:
    st.error(f"⚠️ Lỗi cấu hình API: {e}")
    st.stop()

# --- 1. LOAD DỮ LIỆU ---
@st.cache_data
def load_library():
    try:
        # Kiểm tra file có tồn tại không
        if not os.path.exists('library_database.json'):
            st.warning("Chưa tìm thấy file dữ liệu 'library_database.json'. Đang dùng dữ liệu mẫu.")
            return []
            
        with open('library_database.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Lỗi đọc file dữ liệu: {e}")
        return []

library_data = load_library()

# Chuẩn bị dữ liệu text cho AI
library_text = ""
if library_data:
    for book in library_data:
        # Xử lý an toàn nếu thiếu trường thông tin
        title = book.get('title', 'Không tên')
        author = book.get('author', 'Không rõ')
        category = book.get('category', 'Khác')
        summary = book.get('summary', '')[:200]
        library_text += f"- Tên: {title} | Tác giả: {author} | Thể loại: {category} | Tóm tắt: {summary}...\n"

# --- 2. THIẾT LẬP NHÂN VẬT THƯ ---
system_instruction = f"""
BỐI CẢNH:
Bạn tên là Thư - một học sinh trường Vinschool Times City.
Bạn là "Người Giám Tuyển" (The Curator) của thư viện số này.

NHIỆM VỤ:
Tư vấn sách cho học sinh dựa trên danh sách sau (nếu không có trong danh sách, hãy nói khéo là thư viện chưa nhập về):
{library_text}

PHONG CÁCH:
- Xưng hô: Tớ (Thư) - Cậu (Bạn).
- Tính cách: Thông minh, hơi bí ẩn, cuốn hút, gen Z.
- Sử dụng emoji hợp lý ✨.
- Câu trả lời ngắn gọn (dưới 150 từ).
"""

# Khởi tạo Model
if "model" not in st.session_state:
    try:
        st.session_state.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Dùng 1.5-flash cho ổn định (2.5 đang preview có thể chưa public cho mọi key)
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"Không thể khởi tạo mô hình AI: {e}")

# --- 3. GIAO DIỆN NGƯỜI DÙNG (UI) ---

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3429/3429149.png", width=100)
    st.title("Thông tin Thư viện")
    if library_data:
        st.metric("Tổng đầu sách", len(library_data))
        # Đếm sách theo ngôn ngữ an toàn hơn
        viet_books = len([b for b in library_data if b.get('language') == 'Vietnamese'])
        eng_books = len([b for b in library_data if b.get('language') == 'English'])
        st.metric("Sách Tiếng Việt", viet_books)
        st.metric("Sách Tiếng Anh", eng_books)
    else:
        st.info("Đang cập nhật dữ liệu sách...")
    
    st.markdown("---")
    st.caption("Project: Smart Library Curator")
    st.caption("Thực hiện bởi: **Huyền Thư & Thủy Anh**")

# Main Content
st.title("🔮 The Curator: Trò chuyện cùng Thư")
st.markdown("*Người giám tuyển thư viện AI - Vinschool Times City*")

# --- 4. XỬ LÝ CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào cậu! Tớ là Thư ✨. Hôm nay cậu muốn tìm nguồn cảm hứng từ cuốn sách nào?"}
    ]

# Hiển thị lịch sử
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="🧑‍🎓").write(msg["content"])
    else:
        st.chat_message("assistant", avatar="✨").write(msg["content"])

# Xử lý input
if prompt := st.chat_input("Hỏi Thư về sách toán, văn, khoa học..."):
    # Hiển thị câu hỏi user
    st.chat_message("user", avatar="🧑‍🎓").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI trả lời
    if "model" in st.session_state:
        try:
            # Tạo hiệu ứng loading
            with st.spinner("Thư đang tra cứu dữ liệu..."):
                chat_session = st.session_state.model.start_chat(
                    history=[
                        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                        for m in st.session_state.messages[:-1] # Lấy lịch sử trừ câu mới nhất
                    ]
                )
                
                response = chat_session.send_message(prompt)
                msg_content = response.text
                
            # Hiển thị trả lời
            st.chat_message("assistant", avatar="✨").write(msg_content)
            st.session_state.messages.append({"role": "assistant", "content": msg_content})
            
        except Exception as e:
            st.error(f"Oops! Thư đang mất kết nối vũ trụ (Lỗi API): {e}")
    else:
        st.error("AI chưa sẵn sàng. Vui lòng kiểm tra lại API Key.")
