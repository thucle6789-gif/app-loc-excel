import streamlit as st
import pandas as pd

# Cấu hình giao diện trang web hiển thị rộng rãi
st.set_page_config(page_title="Phần mềm Lọc Dữ Liệu Excel", layout="wide")

st.title("📊 ỨNG DỤNG LỌC DỮ LIỆU EXCEL TỪ GOOGLE DRIVE")
st.subheader("📋 Đang đọc dữ liệu từ sheet: DSKH")
st.write("Dữ liệu được cập nhật theo thời gian thực từ file Excel trên Drive của bạn.")

# --- BƯỚC THAY ĐỔI THÔNG TIN CỦA BẠN ---
# Hãy thay chuỗi chữ dưới đây bằng MÃ_FILE_CỦA_BẠN thực tế của bạn
FILE_ID = "1mrhz-JQAKu2lrQk7cDB_9Vpv4BOQWREh"
# --------------------------------------

# Đường dẫn tải trực tiếp file Excel từ Google Drive
excel_url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# Hàm đọc dữ liệu và làm sạch triệt để mọi lỗi định dạng JSON
@st.cache_data(ttl=10) # Thu ngắn thời gian cache xuống còn 10 giây
def load_data():
    try:
        df = pd.read_excel(excel_url, sheet_name='DSKH', engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        # --- KHẮC PHỤC TRIỆT ĐỂ LỖI JSON (NaN / NaT) ---
        # 1. Ép tất cả các ô về kiểu đối tượng chung để dễ xử lý ô trống
        df = df.astype(object)
        
        # 2. Thay thế applymap bằng hàm map (tương thích phiên bản Pandas mới nhất)
        # Quét qua từng ô dữ liệu, nếu gặp lỗi hệ thống hoặc rỗng sẽ biến thành chuỗi trống ""
        df = df.map(lambda x: "" if pd.isna(x) or str(x).strip().lower() in ["nan", "nat", "null", "#n/a"] else x)
        
        # 3. Đảm bảo tên cột không chứa ký tự lạ làm lỗi giao diện
        df.columns = [str(c) for c in df.columns]
        
        return df
    except ValueError:
        st.error("❌ Không tìm thấy sheet tên là 'DSKH' trong file Excel của bạn. Vui lòng kiểm tra lại tên sheet.")
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
    
    # Lấy danh sách tất cả các cột dữ liệu
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
        # Lấy giá trị duy nhất, bỏ các giá trị trống khỏi bộ lọc dropdown
        unique_vals = [str(val).strip() for val in df[col].unique() if str(val).strip() != ""]
        unique_vals = sorted(list(set(unique_vals))) # Sắp xếp thứ tự cho dễ tìm
        
        selected_vals = st.sidebar.multiselect(f"Lọc theo {col}:", options=unique_vals)
        
        if selected_vals:
            # Ép kiểu về chuỗi để so sánh chính xác với bộ lọc dữ liệu sạch
            filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_vals)]
            
    # --- PHẦN 2: HIỂN THỊ KẾT QUẢ ---
    st.metric(label="Tổng số khách hàng tìm thấy", value=len(filtered_df))
    
    # Hiển thị bảng dữ liệu dưới dạng chuỗi để tránh tuyệt đối lỗi đồ họa JSON
    st.dataframe(filtered_df.astype(str), use_container_width=True)
    
    # Nút bấm tải dữ liệu (.CSV)
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Tải danh sách đã lọc về máy (.CSV)",
        data=csv,
        file_name="dskh_da_loc.csv",
        mime="text/csv",
    )
