import streamlit as st
import pandas as pd

# Cấu hình giao diện trang web hiển thị rộng rãi
st.set_page_config(page_title="Phần mềm Lọc Dữ Liệu Excel", layout="wide")

st.title("📊 ỨNG DỤNG LỌC DỮ LIỆU EXCEL TỪ GOOGLE DRIVE")
st.subheader("📋 Đang đọc dữ liệu từ sheet: DSKH (Cố định tiêu đề 2 dòng)")
st.write("Dữ liệu được cập nhật theo thời gian thực từ file Excel trên Drive của bạn.")

# --- BƯỚC THAY ĐỔI THÔNG TIN CỦA BẠN ---
# 1. Hãy thay chuỗi chữ dưới đây bằng MÃ_FILE_CỦA_BẠN thực tế của bạn
FILE_ID = "1mrhz-JQAKu2lrQk7cDB_9Vpv4BOQWREh"

# 2. HÃY THAY TÊN CỘT BẠN MUỐN TÍNH TỔNG VÀO ĐÂY (Sửa đúng theo tên ở dòng số 4)
COT_TINH_TONG = "V_SHOP" 
# --------------------------------------

# Đường dẫn tải trực tiếp file Excel từ Google Drive
excel_url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# Hàm đọc dữ liệu giữ nguyên dòng 4 làm header và dòng 5 làm dòng đầu tiên
@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_excel(excel_url, sheet_name='DSKH', header=3, engine='openpyxl')
        
        # Xử lý các ô tiêu đề ở dòng 4 bị trống (nếu trống thì đặt tên Cột_Trống)
        final_headers = []
        for idx, col in enumerate(df.columns):
            col_name = str(col).strip()
            if col_name == "" or col_name.startswith("Unnamed:"):
                final_headers.append(f"Cột_Trống_{idx + 1}")
            else:
                final_headers.append(col_name)
        
        df.columns = final_headers
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
    search_query = st.sidebar.text_input("🔍 Tìm kiếm nhanh (Mã, Tên, SĐT...):")
    
    all_columns = df.columns.tolist()
    selected_filter_cols = st.sidebar.multiselect(
        "Chọn các cột bạn muốn lọc chi tiết:", 
        options=all_columns, 
        default=all_columns[:2] if len(all_columns) >= 2 else all_columns
    )
    
    # Tách riêng dòng số 5 (tiêu đề phụ) để cố định
    dong_5 = df.iloc[[0]].copy() 
    du_lieu_thuc_te = df.iloc[1:].copy() 
    
    # Áp dụng bộ lọc tìm kiếm trên dữ liệu thực tế
    filtered_df = du_lieu_thuc_te.copy()
    
    if search_query:
        mask = du_lieu_thuc_te.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
        
    for col in selected_filter_cols:
        unique_vals = [str(val).strip() for val in du_lieu_thuc_te[col].unique() if str(val).strip() != ""]
        unique_vals = sorted(list(set(unique_vals)))
        selected_vals = st.sidebar.multiselect(f"Lọc theo {col}:", options=unique_vals)
        
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_vals)]
            
    # --- PHẦN 2: HIỂN THỊ BẢNG DỮ LIỆU CHÍNH ---
    bảng_hiển_thị = pd.concat([dong_5, filtered_df]).reset_index(drop=True)
    
    bảng_hiển_thị = bảng_hiển_thị.astype(object)
    bảng_hiển_thị = bảng_hiển_thị.map(lambda x: "" if pd.isna(x) or str(x).strip().lower() in ["nan", "nat", "null", "#n/a"] else x)
    
    # --- ĐOẠN CODE CSS CỐ ĐỊNH DÒNG ĐẦU TIÊN (DÒNG 5 EXCEL) ---
    # Đoạn mã này can thiệp vào bảng Streamlit để ghim hàng số 1 luôn chạy theo thanh tiêu đề
    st.markdown(
        """
        <style>
        /* Nhắm vào hàng dữ liệu đầu tiên (index 0) trong bảng hiển thị */
        div[data-testid="stDataFrame"] table tbody tr:first-child {
            position: sticky;
            top: 0;
            background-color: #f0f2f6 !important; /* Đổi màu nền sang xám nhạt để nhận biết là tiêu đề */
            font-weight: bold; /* Bôi đậm chữ */
            z-index: 2;
            box-shadow: 0 2px 2px -1px rgba(0,0,0,0.4);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Hiển thị bảng lên trang web
    st.dataframe(bảng_hiển_thị.astype(str), use_container_width=True)
    
    # Nút bấm tải dữ liệu (.CSV)
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Tải danh sách đã lọc về máy (.CSV)",
        data=csv,
        file_name="dskh_da_loc.csv",
        mime="text/csv",
    )
    
    # --- PHẦN 3: LAYOUT THỐNG KÊ TÍNH TỔNG ---
    st.markdown("---") 
    st.subheader("📊 Khu vực tính tổng dữ liệu sau khi lọc")
    
    col_thong_ke_1, col_thong_ke_2 = st.columns(2)
    
    with col_thong_ke_1:
        st.metric(label="Tổng số dòng dữ liệu lọc được", value=f"{len(filtered_df)} dòng")
        
    with col_thong_ke_2:
        if COT_TINH_TONG in filtered_df.columns:
            solieu_so = pd.to_numeric(filtered_df[COT_TINH_TONG], errors='coerce').fillna(0)
            tong_gia_tri = solieu_so.sum()
            st.metric(label=f"Tổng cộng của cột [{COT_TINH_TONG}]", value=f"{tong_gia_tri:,.0f}")
        else:
            st.info(f"💡 Để tính tổng, hãy sửa biến COT_TINH_TONG ở dòng 15 thành tên chính xác của cột ở dòng số 4.")
