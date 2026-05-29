import streamlit as st
import pandas as pd

# Cấu hình giao diện trang web hiển thị rộng rãi
st.set_page_config(page_title="Phần mềm Lọc Dữ Liệu Excel", layout="wide")

st.title("📊 ỨNG DỤNG LỌC DỮ LIỆU EXCEL TỪ GOOGLE DRIVE")
st.subheader("📋 Đang đọc dữ liệu từ sheet: DSKH")
st.write("Dữ liệu được cập nhật theo thời gian thực từ file Excel trên Drive của bạn.")

# --- BƯỚC THAY ĐỔI THÔNG TIN CỦA BẠN ---
# Hãy thay chuỗi chữ dưới đây bằng MÃ_FILE_CỦA_BẠN đã lấy ở các bước trước
FILE_ID = "1mrhz-JQAKu2lrQk7cDB_9Vpv4BOQWREh"
# --------------------------------------

# Đường dẫn tải trực tiếp file Excel từ Google Drive
excel_url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# Hàm đọc dữ liệu từ sheet "DSKH" và lưu vào bộ nhớ tạm để web chạy nhanh hơn
@st.cache_data(ttl=60) # Tự động tải lại dữ liệu mới sau mỗi 60 giây nếu có thay đổi
def load_data():
    try:
        # Bổ sung tham số sheet_name='DSKH' để ép buộc đọc đúng sheet Danh sách khách hàng
        df = pd.read_excel(excel_url, sheet_name='DSKH', engine='openpyxl')
        
        # Loại bỏ khoảng trắng thừa ở tên cột
        df.columns = df.columns.str.strip()
        return df
    except ValueError:
        st.error("❌ Không tìm thấy sheet tên là 'DSKH' trong file Excel của bạn. Vui lòng kiểm tra lại chính xác tên sheet (có dấu cách hay viết hoa/viết thường không).")
        return None
    except Exception as e:
        st.error(f"❌ Không thể kết nối đến file Excel trên Drive. Vui lòng kiểm tra lại mã File ID và quyền chia sẻ công khai. Lỗi: {e}")
        return None

df = load_data()

if df is not None:
    # --- PHẦN 1: TẠO BỘ LỌC DỮ LIỆU (SIDEBAR) ---
    st.sidebar.header("Bộ Lọc Dữ Liệu DSKH")
    
    # 1. Ô tìm kiếm từ khóa chung toàn bảng (ví dụ: gõ tên khách hàng hoặc số điện thoại)
    search_query = st.sidebar.text_input("🔍 Tìm kiếm nhanh (Tên, SĐT, Địa chỉ...):")
    
    # 2. Tạo các bộ lọc tự động theo từng cột dữ liệu
    all_columns = df.columns.tolist()
    
    # Chọn các cột bạn muốn dùng để lọc chi tiết (Mặc định chọn 2 cột đầu tiên, nhân viên có thể tự tích chọn thêm trên web)
    selected_filter_cols = st.sidebar.multiselect(
        "Chọn các cột bạn muốn lọc chi tiết:", 
        options=all_columns, 
        default=all_columns[:2] if len(all_columns) >= 2 else all_columns
    )
    
    # Áp dụng bộ lọc
    filtered_df = df.copy()
    
    # Thực hiện lọc theo ô tìm kiếm chung trước
    if search_query:
        # Tìm kiếm không phân biệt chữ hoa chữ thường trên tất cả các cột
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
        
    # Thực hiện lọc chi tiết theo từng cột được chọn (Ví dụ: Khu vực, Nhóm khách hàng...)
    for col in selected_filter_cols:
        unique_vals = df[col].dropna().unique().tolist()
        selected_vals = st.sidebar.multiselect(f"Lọc theo {col}:", options=unique_vals)
        
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
            
    # --- PHẦN 2: HIỂN THỊ KẾT QUẢ ---
    # Hiển thị tổng số dòng tìm thấy
    st.metric(label="Tổng số khách hàng tìm thấy", value=len(filtered_df))
    
    # Hiển thị bảng dữ liệu dưới dạng bảng tương tác (cho phép sắp xếp, phóng to)
    st.dataframe(filtered_df, use_container_width=True)
    
    # Nút bấm cho phép tải dữ liệu đã lọc về máy dạng .CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Tải danh sách đã lọc về máy (.CSV)",
        data=csv,
        file_name="dskh_da_loc.csv",
        mime="text/csv",
    )