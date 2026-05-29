import streamlit as st
import pandas as pd

# Cấu hình giao diện trang web hiển thị rộng rãi
st.set_page_config(page_title="Phần mềm Lọc Dữ Liệu Excel", layout="wide")

st.title("📊 ỨNG DỤNG LỌC DỮ LIỆU EXCEL TỪ GOOGLE DRIVE")
st.subheader("📋 Đang đọc dữ liệu từ sheet: DSKH (Tiêu đề 2 tầng cố định)")
st.write("Dữ liệu được cập nhật theo thời gian thực từ file Excel trên Drive của bạn.")

# --- BƯỚC THAY ĐỔI THÔNG TIN CỦA BẠN ---
# 1. Hãy thay chuỗi chữ dưới đây bằng MÃ_FILE_CỦA_BẠN thực tế của bạn
FILE_ID = "1mrhz-JQAKu2lrQk7cDB_9Vpv4BOQWREh"

# 2. HÃY THAY TÊN CỘT BẠN MUỐN TÍNH TỔNG VÀO ĐÂY (Ví dụ: "Doanh Số" hoặc tên cột sau khi gộp)
COT_TINH_TONG = "Doanh Số" 
# --------------------------------------

# Đường dẫn tải trực tiếp file Excel từ Google Drive
excel_url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# Hàm xử lý đặt tên cột độc bản, chống lỗi trùng lặp (Duplicate Column Names)
def make_unique_columns(headers):
    seen = {}
    unique_headers = []
    for item in headers:
        item_str = str(item).strip()
        if item_str == "" or item_str.lower() in ["nan", "unnamed:"]:
            item_str = "Cột_Trống"
            
        if item_str not in seen:
            seen[item_str] = 1
            unique_headers.append(item_str)
        else:
            seen[item_str] += 1
            unique_headers.append(f"{item_str}_{seen[item_str] - 1}")
    return unique_headers

# Hàm đọc dữ liệu và xử lý gộp hiển thị tiêu đề 2 tầng độc lập
@st.cache_data(ttl=10)
def load_data():
    try:
        # Đọc file thô từ đầu để bóc tách dòng 4 và dòng 5
        df_raw = pd.read_excel(excel_url, sheet_name='DSKH', header=None, engine='openpyxl')
        
        # Lấy dữ liệu dòng 4 (index 3) và dòng 5 (index 4)
        row_4 = df_raw.iloc[3].fillna("").astype(str).str.strip()
        row_5 = df_raw.iloc[4].fillna("").astype(str).str.strip()
        
        # Tiến hành xử lý nối tiêu đề thông minh
        raw_headers = []
        for idx, (r4, r5) in enumerate(zip(row_4, row_5)):
            # Lọc bỏ các chữ rác hệ thống tự sinh
            r4_clean = "" if r4.lower().startswith("unnamed:") else r4
            r5_clean = "" if r5.lower().startswith("unnamed:") else r5
            
            if r4_clean == "" and r5_clean == "":
                raw_headers.append("")
            elif r4_clean != "" and r5_clean == "":
                raw_headers.append(r4_clean)
            elif r4_clean == "" and r5_clean != "":
                raw_headers.append(r5_clean)
            else:
                raw_headers.append(f"{r4_clean} | {r5_clean}")
                
        # Ép các tên cột phải độc bản, không được trùng nhau
        final_headers = make_unique_columns(raw_headers)
                
        # Cắt bỏ phần tiêu đề cũ để lấy dữ liệu thực tế từ dòng 6 trở đi (index 5)
        df = df_raw.iloc[5:].copy()
        df.columns = final_headers
        df = df.reset_index(drop=True)
        
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
    
    # Lấy toàn bộ danh sách tên cột mới để làm bộ lọc
    all_columns = df.columns.tolist()
    selected_filter_cols = st.sidebar.multiselect(
        "Chọn các cột bạn muốn lọc chi tiết:", 
        options=all_columns, 
        default=all_columns[:2] if len(all_columns) >= 2 else all_columns
    )
    
    # Áp dụng bộ lọc tìm kiếm
    filtered_df = df.copy()
    
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
        
    for col in selected_filter_cols:
        unique_vals = [str(val).strip() for val in df[col].unique() if str(val).strip() != ""]
        unique_vals = sorted(list(set(unique_vals)))
        selected_vals = st.sidebar.multiselect(f"Lọc theo {col}:", options=unique_vals)
        
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_vals)]
            
    # --- PHẦN 2: HIỂN THỊ BẢNG DỮ LIỆU CHÍNH ---
    # Làm sạch các ô trống để hiển thị mượt mà không lỗi JSON
    df_hien_thi = filtered_df.copy().astype(object)
    df_hien_thi = df_hien_thi.map(lambda x: "" if pd.isna(x) or str(x).strip().lower() in ["nan", "nat", "null", "#n/a"] else x)
    
    # Hiển thị bảng tương tác (Tiêu đề gộp sẽ đứng im cố định 100% khi cuộn chuột)
    st.dataframe(df_hien_thi.astype(str), use_container_width=True)
    
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
            st.info(f"💡 Để tính tổng, hãy sửa biến COT_TINH_TONG ở dòng 16 thành tên cột hiển thị chính xác trên bảng.")
