import streamlit as st
import pandas as pd

# Cấu hình giao diện trang web hiển thị rộng rãi
st.set_page_config(page_title="Phần mềm Lọc Dữ Liệu Excel", layout="wide")

st.title("📊 ỨNG DỤNG LỌC DỮ LIỆU EXCEL TỪ GOOGLE DRIVE")
st.subheader("📋 Đang đọc dữ liệu từ sheet: DSKH (Cố định 2 dòng tiêu đề)")
st.write("Dữ liệu được cập nhật theo thời gian thực từ file Excel trên Drive của bạn.")

# --- BƯỚC THAY ĐỔI THÔNG TIN CỦA BẠN ---
# 1. Hãy thay chuỗi chữ dưới đây bằng MÃ_FILE_CỦA_BẠN thực tế của bạn
FILE_ID = "1mrhz-JQAKu2lrQk7cDB_9Vpv4BOQWREh"

# 2. HÃY THAY TÊN CỘT BẠN MUỐN TÍNH TỔNG VÀO ĐÂY (Điền chính xác tên cột ở dòng số 4 của Excel)
COT_TINH_TONG = "PSDS T4" 
# --------------------------------------

# Đường dẫn tải trực tiếp file Excel từ Google Drive
excel_url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# Hàm đọc dữ liệu gốc và tách thành 2 tầng tiêu đề độc lập
@st.cache_data(ttl=10)
def load_data():
    try:
        df_raw = pd.read_excel(excel_url, sheet_name='DSKH', header=None, engine='openpyxl')
        return df_raw
    except ValueError:
        st.error("❌ Không tìm thấy sheet tên là 'DSKH' trong file Excel của bạn. Vui lòng kiểm tra lại tên sheet.")
        return None
    except Exception as e:
        st.error(f"❌ Không thể kết nối đến file Excel trên Drive. Lỗi: {e}")
        return None

df_raw = load_data()

if df_raw is not None:
    # 1. Trích xuất dòng 4 (Tiêu đề thật) và dòng 5 (Tiêu đề ảo)
    row_4 = df_raw.iloc[3].fillna("").astype(str).str.strip().tolist()
    row_5 = df_raw.iloc[4].fillna("").astype(str).str.strip().tolist()
    
    # Chuẩn hóa tên cột để xử lý việc lọc dữ liệu trong bộ nhớ
    headers_for_filter = []
    for idx, r4 in enumerate(row_4):
        r4_clean = "" if r4.lower().startswith("unnamed:") else r4
        if r4_clean == "":
            headers_for_filter.append(f"Cột_Trống_{idx+1}")
        else:
            if r4_clean not in headers_for_filter:
                headers_for_filter.append(r4_clean)
            else:
                headers_for_filter.append(f"{r4_clean}_{idx}")

    # Lấy dữ liệu thực tế từ dòng 6 trở đi
    df_data = df_raw.iloc[5:].copy()
    df_data.columns = headers_for_filter
    df_data = df_data.reset_index(drop=True)

    # --- PHẦN 1: TẠO BỘ LỌC DỮ LIỆU (SIDEBAR) ---
    st.sidebar.header("Bộ Lọc Dữ Liệu DSKH")
    search_query = st.sidebar.text_input("🔍 Tìm kiếm nhanh (Mã, Tên, SĐT...):")
    
    filter_options = [col for col in headers_for_filter if not col.startswith("Cột_Trống_")]
    selected_filter_cols = st.sidebar.multiselect("Chọn các cột bạn muốn lọc chi tiết:", options=filter_options, default=filter_options[:2] if len(filter_options)>=2 else filter_options)
    
    # Áp dụng logic lọc dữ liệu
    filtered_df = df_data.copy()
    if search_query:
        mask = df_data.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
        
    for col in selected_filter_cols:
        unique_vals = [str(val).strip() for val in df_data[col].unique() if str(val).strip() != ""]
        unique_vals = sorted(list(set(unique_vals)))
        selected_vals = st.sidebar.multiselect(f"Lọc theo {col}:", options=unique_vals)
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_vals)]

    # --- PHẦN 2: TẠO BẢNG GIAO DIỆN HTML/CSS CỐ ĐỊNH 2 TẦNG TIÊU ĐỀ + TỰ XUỐNG DÒNG CHỮ ---
    filtered_df_clean = filtered_df.copy().fillna("")
    filtered_df_clean = filtered_df_clean.map(lambda x: "" if str(x).strip().lower() in ["nan", "nat", "null", "#n/a"] else x)
    
    # Tạo mã HTML cho các dòng dữ liệu khách hàng (gắn class riêng cho cột Tên KH dựa vào vị trí cột)
    html_rows = ""
    for _, row in filtered_df_clean.iterrows():
        html_rows += "<tr>"
        for idx, val in enumerate(row):
            # Cột số 4 (index là 3) thường là cột Tên KH (STT=0, Column1=1, Mã KH=2, Tên KH=3)
            # Bạn có thể điều chỉnh số 3 này nếu cột Tên KH nằm ở vị trí khác
            if idx == 3: 
                html_rows += f"<td class='text-wrap-column'>{val}</td>"
            else:
                html_rows += f"<td>{val}</td>"
        html_rows += "</tr>"
        
    # Tạo mã HTML cho dòng tiêu đề thật (Dòng 4)
    html_header_4 = "<tr>"
    for idx, r4 in enumerate(row_4):
        r4_display = "" if r4.lower().startswith("unnamed:") else r4
        if idx == 3:
            html_header_4 += f"<th class='text-wrap-column'>{r4_display}</th>"
        else:
            html_header_4 += f"<th>{r4_display}</th>"
    html_header_4 += "</tr>"
    
    # Tạo mã HTML cho dòng tiêu đề ảo (Dòng 5)
    html_header_5 = "<tr>"
    for idx, r5 in enumerate(row_5):
        r5_display = "" if r5.lower().startswith("unnamed:") else r5
        if idx == 3:
            html_header_5 += f"<th class='text-wrap-column'>{r5_display}</th>"
        else:
            html_header_5 += f"<th>{r5_display}</th>"
    html_header_5 += "</tr>"

    # CSS NÂNG CẤP: Bổ sung class .text-wrap-column để ép chữ tự động xuống dòng
    table_html = f"""
    <style>
        .table-container {{
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid #dee2e6;
            font-family: sans-serif;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            padding: 8px 10px;
            border: 1px solid #dee2e6;
            text-align: left;
            white-space: nowrap; /* Mặc định các cột khác không tự giãn dòng để cuộn ngang */
        }}
        
        /* CẤU HÌNH RIÊNG CHO CỘT TÊN KHÁCH HÀNG: ÉP TỰ XUỐNG DÒNG */
        .text-wrap-column {{
            white-space: normal !important; /* Cho phép chữ tự động ngắt hàng */
            min-width: 180px !important;    /* Độ rộng tối thiểu của cột */
            max-width: 220px !important;    /* Độ rộng tối đa của cột, quá độ rộng này chữ tự xuống dòng */
            word-break: break-word;         /* Ngắt từ thông minh không làm vỡ chữ */
        }}
        
        /* Cố định dòng 4 (Tiêu đề gốc) */
        thead tr:nth-child(1) th {{
            position: sticky;
            top: 0;
            background-color: #f1f3f5;
            color: #495057;
            z-index: 10;
        }}
        /* Cố định dòng 5 (Tiêu đề ảo) */
        thead tr:nth-child(2) th {{
            position: sticky;
            top: 33px; 
            background-color: #f8f9fa;
            color: #6c757d;
            z-index: 9;
        }}
        tbody tr:hover {{
            background-color: #f8f9fa;
        }}
    </style>
    <div class="table-container">
        <table>
            <thead>
                {html_header_4}
                {html_header_5}
            </thead>
            <tbody>
                {html_rows}
            </tbody>
        </table>
    </div>
    """
    
    st.components.v1.html(table_html, height=520, scrolling=False)
    
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
            st.info(f"💡 Để tính tổng số tiền/doanh số, hãy nhập đúng tên cột ở dòng 16.")
