import streamlit as st
import pandas as pd

# Cấu hình giao diện trang web hiển thị rộng rãi
st.set_page_config(page_title="Phần mềm Lọc Dữ Liệu Excel", layout="wide")

st.title("📊 ỨNG DỤNG LỌC DỮ LIỆU EXCEL TỪ GOOGLE DRIVE")
st.write("Dữ liệu được cập nhật theo thời gian thực từ file Excel trên Drive của bạn.")

# --- BƯỚC THAY ĐỔI THÔNG TIN CỦA BẠN ---
# Hãy thay chuỗi chữ dưới đây bằng MÃ_FILE_CỦA_BẠN đã lấy ở Bước 1
FILE_ID = "1mrhz-JQAKu2lrQk7cDB_9Vpv4BOQWREh"
# --------------------------------------

# Đường dẫn tải trực tiếp file Excel từ Google Drive
excel_url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# Hàm đọc dữ liệu và lưu vào bộ nhớ tạm để web chạy nhanh hơn
@st.cache_data(ttl=60) # Tự động tải lại dữ liệu mới sau mỗi 60 giây nếu có thay đổi
def load_data():
    try:
        df = pd.read_excel(excel_url, engine='openpyxl')
        # Loại bỏ khoảng trắng thừa ở tên cột
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Không thể kết nối đến file Excel trên Drive. Vui lòng kiểm tra lại mã File ID và quyền chia sẻ công khai. Lỗi: {e}")
        return None

df = load_data()

if df is not None:
    # --- PHẦN 1: TẠO BỘ LỌC DỮ LIỆU (SIDEBAR) ---
    st.sidebar.header("Bộ Lọc Dữ Liệu")
    
    # 1. Ô tìm kiếm từ khóa chung toàn bảng
    search_query = st.sidebar.text_input("🔍 Tìm kiếm từ khóa nhanh:")
    
    # 2. Tạo các bộ lọc tự động theo từng cột dữ liệu (Ví dụ: Trạng thái, Danh mục...)
    # Hệ thống sẽ tự động lấy danh sách tất cả các cột trong file Excel của bạn
    all_columns = df.columns.tolist()
    
    # Chọn các cột bạn muốn dùng để lọc (Mặc định chọn 2 cột đầu tiên, bạn có thể chỉnh trên giao diện web)
    selected_filter_cols = st.sidebar.multiselect(
        "Chọn các cột bạn muốn lọc chi tiết:", 
        options=all_columns, 
        default=all_columns[:2] if len(all_columns) >= 2 else all_columns
    )
    
    # Áp dụng bộ lọc
    filtered_df = df.copy()
    
    # Thực hiện lọc theo ô tìm kiếm chung trước
    if search_query:
        # Tìm kiếm không phân biệt chữ hoa chữ thường trên tất cả các cột dạng chuỗi
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
        
    # Thực hiện lọc chi tiết theo từng cột được chọn
    for col in selected_filter_cols:
        # Lấy các giá trị duy nhất (Unique values) của cột đó để làm menu thả xuống
        unique_vals = df[col].dropna().unique().tolist()
        selected_vals = st.sidebar.multiselect(f"Lọc theo {col}:", options=unique_vals)
        
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
            
    # --- PHẦN 2: HIỂN THỊ KẾT QUẢ ---
    # Hiển thị tổng số dòng tìm thấy
    st.metric(label="Số dòng tìm thấy", value=len(filtered_df))
    
    # Hiển thị bảng dữ liệu dưới dạng bảng tương tác (cho phép sắp xếp, phóng to)
    st.dataframe(filtered_df, use_container_width=True)
    
    # Nút bấm cho phép tải dữ liệu đã lọc về máy (dạng .csv hoặc .xlsx nếu muốn)
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Tải dữ liệu đã lọc về máy (.CSV)",
        data=csv,
        file_name="du_lieu_da_loc.csv",
        mime="text/csv",
    )