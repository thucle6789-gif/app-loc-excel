import streamlit as st
import pandas as pd

# Cấu hình giao diện trang web hiển thị rộng rãi
st.set_page_config(page_title="Phần mềm Lọc Dữ Liệu Excel", layout="wide")

st.title("📊 ỨNG DỤNG LỌC DỮ LIỆU EXCEL TỪ GOOGLE DRIVE")
st.subheader("📋 Đang đọc dữ liệu từ sheet: DSKH (Tiêu đề dòng 4)")
st.write("Dữ liệu được cập nhật theo thời gian thực từ file Excel trên Drive của bạn.")

# --- BƯỚC THAY ĐỔI THÔNG TIN CỦA BẠN ---
# 1. Hãy thay chuỗi chữ dưới đây bằng MÃ_FILE_CỦA_BẠN thực tế của bạn
FILE_ID = "1mrhz-JQAKu2lrQk7cDB_9Vpv4BOQWREh"

# 2. HÃY THAY TÊN CỘT BẠN MUỐN TÍNH TỔNG VÀO ĐÂY (Ví dụ: "Doanh Số", "Số Lượng", "Tiền"...)
COT_TINH_TONG = "V_SHOP" 
# --------------------------------------

# Đường dẫn tải trực tiếp file Excel từ Google Drive
excel_url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# Hàm đọc dữ liệu và làm sạch triệt để mọi lỗi định dạng JSON
@st.cache_data(ttl=10)
def load_data():
    try:
        df = pd.read_excel(excel_url, sheet_name='DSKH', header=3, engine='openpyxl')
        df.columns = df.columns.str.strip()
        df = df.loc[:, ~df.columns.str.contains('^Unnamed:')]
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
    
    all_columns = [col for col in df.columns.tolist() if col.strip() != ""]
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
        unique_vals = [str(val).strip() for val in df[col].unique() if str(val).strip() != ""]
        unique_vals = sorted(list(set(unique_vals)))
        selected_vals = st.sidebar.multiselect(f"Lọc theo {col}:", options=unique_vals)
        
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_vals)]
            
    # --- PHẦN 2: HIỂN THỊ BẢNG DỮ LIỆU CHÍNH ---
    # Ép kiểu dữ liệu sang String để hiển thị bảng an toàn không lỗi đồ họa
    df_hien_thi = filtered_df.copy().astype(object)
    df_hien_thi = df_hien_thi.map(lambda x: "" if pd.isna(x) or str(x).strip().lower() in ["nan", "nat", "null", "#n/a"] else x)
    df_hien_thi.columns = [str(c) for c in df_hien_thi.columns if str(c).lower() != 'nan']
    
    st.dataframe(df_hien_thi.astype(str), use_container_width=True)
    
    # Nút bấm tải dữ liệu (.CSV)
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Tải danh sách đã lọc về máy (.CSV)",
        data=csv,
        file_name="dskh_da_loc.csv",
        mime="text/csv",
    )
    
    # --- PHẦN 3: LAYOUT THỐNG KÊ TÍNH TỔNG (NẰM PHÍA DƯỚI) ---
    st.markdown("---") # Dấu gạch ngang phân cách bản dữ liệu và khu vực tổng kết
    st.subheader("📊 Khu vực tính tổng dữ liệu sau khi lọc")
    
    # Tạo 2 cột nằm ngang phía dưới để hiển thị số liệu tổng kết
    col_thong_ke_1, col_thong_ke_2 = st.columns(2)
    
    with col_thong_ke_1:
        # Thống kê số 1: Đếm tổng số dòng (số khách hàng) sau khi lọc
        st.metric(label="Tổng số dòng dữ liệu lọc được", value=f"{len(filtered_df)} dòng")
        
    with col_thong_ke_2:
        # Thống kê số 2: Tính tổng một cột số
        if COT_TINH_TONG in filtered_df.columns:
            # Chuyển đổi dữ liệu cột đó sang dạng số, bỏ qua các ô lỗi hoặc ô chữ để tính tổng không bị lỗi
            solieu_so = pd.to_numeric(filtered_df[COT_TINH_TONG], errors='coerce').fillna(0)
            tong_gia_tri = solieu_so.sum()
            
            # Hiển thị số tổng (được định dạng có dấu phẩy phân cách hàng nghìn cho dễ nhìn)
            st.metric(label=f"Tổng cộng của cột [{COT_TINH_TONG}]", value=f"{tong_gia_tri:,.0f}")
        else:
            st.info(f"💡 Để tính tổng số tiền/số lượng, hãy sửa tên biến COT_TINH_TONG ở dòng 16 thành tên cột số có trong file của bạn (Hiện tại không tìm thấy cột tên '{COT_TINH_TONG}').")
