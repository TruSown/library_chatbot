import streamlit as st
import json
import google.generativeai as genai

# --- CẤU HÌNH TRANG WEB (MTB 1.2.e - Sản phẩm truyền thông) ---
st.set_page_config(
    page_title="Thư viện số",
    page_icon="📚",
    layout="centered"
)

# --- CẤU HÌNH API ---
# Dán API Key của bạn vào đây
API_KEY = "AIzaSyDzyKV_maEuob_g-c6RAIuKalb0qkHaHyk" 
try:
    genai.configure(api_key=API_KEY)
except:
    st.error("Chưa nhập API Key hoặc Key bị lỗi!")

# --- 1. LOAD DỮ LIỆU ---
@st.cache_data # Giúp load dữ liệu nhanh hơn, không phải load lại mỗi lần click
def load_library():
    try:
        with open('library_database.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

library_data = load_library()

# Chuẩn bị dữ liệu text cho AI
library_text = ""
if library_data:
    for book in library_data:
        library_text += f"- Tên: {book['title']} | Tác giả: {book['author']} | Thể loại: {book['category']} | Tóm tắt: {book['summary'][:200]}...\n"

# --- 2. THIẾT LẬP NHÂN VẬT THƯ (MTB 1.2.c - Tinh chỉnh AI) ---
system_instruction = f"""
BỐI CẢNH:
Bạn tên là Thư - một học sinh trường Vinschool Times City.
Bạn là "Người Giám Tuyển" (The Curator) của thư viện số này.

NHIỆM VỤ:
Tư vấn sách cho học sinh dựa trên danh sách sau:
{library_text}

PHONG CÁCH:
- Xưng hô: Tớ (Thư) - Cậu (Bạn).
- Tính cách: Thông minh, hơi bí ẩn, cuốn hút.
- Luôn gợi mở sự tò mò.
- Ngắn gọn (dưới 150 từ).
"""

# Khởi tạo Model
if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", # Hoặc gemini-pro nếu lỗi
        system_instruction=system_instruction
    )

# --- 3. GIAO DIỆN NGƯỜI DÙNG (UI) ---

# Cột bên trái (Sidebar) để khoe số liệu (MTB 2.1)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Vinschool_Logo.png/640px-Vinschool_Logo.png", width=150)
    st.title("Thông tin Thư viện")
    if library_data:
        st.metric("Tổng đầu sách", len(library_data))
        st.metric("Sách Tiếng Việt", len([b for b in library_data if b.get('language') == 'Vietnamese']))
        st.metric("Sách Tiếng Anh", len([b for b in library_data if b.get('language') == 'English']))
    else:
        st.warning("Chưa có dữ liệu!")
    
    st.write("---")
    st.write("Project: Smart Library Curator")
    st.write("Thực hiện bởi: Nhóm 10")

# Tiêu đề chính
st.title("🔮 The Curator: Trò chuyện cùng Thư")
st.caption("Người giám tuyển thư viện AI - Vinschool Times City")

# --- 4. XỬ LÝ CHAT (Lưu lịch sử chat) ---
if "messages" not in st.session_state:
    # Lời chào đầu tiên
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào cậu! Tớ là Thư. Cậu đang tìm kiếm bí mật nào trong những trang sách?"}
    ]

# Hiển thị lại các tin nhắn cũ
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="🧑‍🎓").write(msg["content"])
    else:
        st.chat_message("assistant", avatar="✨").write(msg["content"])

# Hộp nhập liệu
if prompt := st.chat_input("Nhập câu hỏi của bạn ở đây..."):
    # 1. Hiển thị câu hỏi của người dùng
    st.chat_message("user", avatar="🧑‍🎓").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. AI suy nghĩ và trả lời
    if library_text:
        try:
            chat_session = st.session_state.model.start_chat(history=[])
            # Gửi kèm ngữ cảnh lịch sử chat (để AI nhớ câu trước)
            full_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            
            response = chat_session.send_message(prompt)
            msg_content = response.text
            
            # Hiển thị câu trả lời của Thư
            st.chat_message("assistant", avatar="✨").write(msg_content)
            st.session_state.messages.append({"role": "assistant", "content": msg_content})
            
        except Exception as e:
            st.error(f"Thư đang bận (Lỗi kết nối): {e}")
    else:
        st.error("Chưa load được dữ liệu sách!")