import streamlit as st
import pandas as pd

# Cấu hình giao diện trang web hiển thị rộng rãi
st.set_page_config(page_title="Phần mềm Lọc Dữ Liệu Excel", layout="wide")

st.title("📊 ỨNG DỤNG LỌC DỮ LIỆU EXCEL TỪ GOOGLE DRIVE")
st.subheader("📋 Đang đọc dữ liệu từ sheet: DSKH")
st.write("Dữ liệu được cập nhật theo thời gian thực từ file Excel trên Drive của bạn.")

# --- BƯỚC THAY ĐỔI THÔNG TIN CỦA BẠN ---
# Hãy thay chuỗi chữ dưới đây bằng MÃ_FILE_CỦA_BẠN của bạn
FILE_ID = "1mrhz-JQAKu2lrQk7cDB_9Vpv4BOQWREh"
# --------------------------------------

# Đường dẫn tải trực tiếp file Excel từ Google Drive
excel_url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# Hàm đọc dữ liệu từ sheet "DSKH"
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_excel(excel_url, sheet_name='DSKH', engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        # --- ĐOẠN SỬA LỖI JSON / NaN ---
        # Điền chuỗi rỗng vào các ô trống và xử lý lỗi không tương thích định dạng JSON của Streamlit
        df = df.fillna("")
        # Đảm bảo chuyển hết các cột về dạng chuỗi hoặc số chuẩn để Streamlit vẽ bảng mượt mà
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
        # -------------------------------
        
        return df
    except ValueError:
        st.error("❌ Không tìm thấy sheet tên là 'DSKH' trong file Excel của bạn.")
        return None
    except Exception as e:
        st.error(f"❌ Không thể kết nối đến file Excel trên Drive. Lỗi: {e}")
        return None

df = load_data()

if df is not None:
    # --- PHẦN 1: TẠO BỘ LỌC DỮ LIỆU (SIDEBAR) ---
    st.sidebar.header("Bộ Lọc Dữ Liệu DSKH")
    
    # Ô tìm kiếm từ khóa chung toàn bảng
    search_query = st.sidebar.text_input("🔍 Tìm kiếm nhanh (Tên, SĐT, Địa chỉ...):")
    
    # Tạo các bộ lọc tự động theo từng cột dữ liệu
    all_columns = df.columns.tolist()
    
    # Chọn các cột muốn dùng để lọc chi tiết
    selected_filter_cols = st.sidebar.multiselect(
        "Chọn các cột bạn muốn lọc chi tiết:", 
        options=all_columns, 
        default=all_columns[:2] if len(all_columns) >= 2 else all_columns
    )
    
    # Áp dụng bộ lọc
    filtered_df = df.copy()
    
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
        
    for col in selected_filter_cols:
        # Lấy giá trị duy nhất và bỏ các giá trị rỗng khỏi menu lọc
        unique_vals = [val for val in df[col].unique() if str(val).strip() != ""]
        selected_vals = st.sidebar.multiselect(f"Lọc theo {col}:", options=unique_vals)
        
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
            
    # --- PHẦN 2: HIỂN THỊ KẾT QUẢ ---
    st.metric(label="Tổng số khách hàng tìm thấy", value=len(filtered_df))
    
    # Hiển thị bảng dữ liệu (Đã an toàn không lo lỗi JSON)
    st.dataframe(filtered_df, use_container_width=True)
    
    # Nút bấm tải dữ liệu (.CSV)
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Tải danh sách đã lọc về máy (.CSV)",
        data=csv,
        file_name="dskh_da_loc.csv",
        mime="text/csv",
    )
