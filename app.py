import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

# 2. التنسيق البصري (تحسين القائمة الجانبية)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    /* الخط العام للنظام */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Cairo', sans-serif !important;
        text-align: right;
        direction: rtl;
    }

    /* تصميم القائمة الجانبية */
    [data-testid="stSidebar"] {
        background-color: #1e272e !important; /* لون داكن فخم */
        min-width: 300px !important;
    }

    /* اسم أبو عمر في القائمة */
    .sidebar-user-header {
        color: #27ae60 !important;
        font-size: 32px !important;
        font-weight: 900 !important;
        text-align: center;
        padding: 20px 0px;
        border-bottom: 2px solid #27ae60;
        margin-bottom: 20px;
    }

    /* عنوان "القائمة" */
    .sidebar-menu-title {
        color: #ecf0f1 !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        margin-bottom: 15px;
        padding-right: 10px;
        border-right: 4px solid #27ae60;
    }

    /* تنسيق خيارات الراديو (القائمة المنسدلة) */
    div[data-testid="stSidebar"] .stRadio div label {
        background-color: #2f3640;
        margin-bottom: 8px;
        border-radius: 10px;
        padding: 12px 15px !important;
        transition: 0.3s;
        border: 1px solid #3d4652;
    }

    div[data-testid="stSidebar"] .stRadio div label:hover {
        background-color: #3d4652;
        border-color: #27ae60;
    }

    /* النص داخل القائمة - عريض وواضح */
    div[data-testid="stSidebar"] .stRadio div label p {
        color: white !important;
        font-size: 20px !important;
        font-weight: 900 !important; /* خط عريض جداً */
        letter-spacing: 0.5px;
    }

    /* تنسيق الخيار المختار */
    div[data-testid="stSidebar"] .stRadio div label[data-checked="true"] {
        background-color: #27ae60 !important;
        border: none !important;
    }

    /* العناوين الرئيسية */
    .main-title {
        color: #2c3e50;
        text-align: center;
        border-bottom: 5px solid #27ae60;
        padding-bottom: 10px;
        font-weight: 900;
        font-size: 35px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. تحميل البيانات (مختصر لضمان عمل الكود)
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv('inventory_final.csv', index_col=0).to_dict('index') if os.path.exists('inventory_final.csv') else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv('sales_final.csv') if os.path.exists('sales_final.csv') else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])

# 4. بناء القائمة الجانبية المطورة
st.sidebar.markdown("<div class='sidebar-user-header'>أبو عمر 👋</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='sidebar-menu-title'>القائمة</div>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    label="اختر القسم:",
    options=["📊 التقارير المالية", "🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "⚙️ الإعدادات"],
    label_visibility="collapsed"
)

st.sidebar.divider()
if st.sidebar.button("🚪 خروج آمن", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# --- محتوى الصفحات بناءً على اختيار القائمة ---

if menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية والأرباح</h1>", unsafe_allow_html=True)
    # هنا يوضع كود التقارير الذي صممناه سابقاً
    st.info("هنا تظهر مبيعات اليوم وتفصيل (كاش / تطبيق) بخطوط عريضة.")

elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع المباشر</h1>", unsafe_allow_html=True)
    # هنا يوضع كود البيع
    
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إعدادات الأصناف</h1>", unsafe_allow_html=True)
