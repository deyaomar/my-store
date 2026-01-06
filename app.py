import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المحاسبي", layout="wide", page_icon="🍏")

# وظيفة ذكية لتحويل النص لرقم (تعالج الفاصلة والنقطة)
def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        # استبدال الفاصلة العربية والأجنبية بنقطة
        processed = str(text).replace(',', '.').replace('،', '.')
        return float(processed)
    except:
        return 0.0

# 2. ملفات البيانات
DB_FILE = 'inventory_final.csv'
SALES_FILE = 'sales_final.csv'
CATS_FILE = 'categories_final.csv'

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame({'name': st.session_state.categories}).to_csv(CATS_FILE, index=False)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)

# تحميل البيانات وتجهيز الجلسة
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

# 3. الهوية البصرية (رصاصي غامق + أخضر)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: 800 !important; font-size: 20px !important; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; color: white !important; border: 2px solid #2ecc71 !important; height: 3.5em; width: 100%; font-weight: bold; }
    .stButton > button[kind="secondary"] { background-color: #ecf0f1 !important; color: #2c3e50 !important; height: 3.5em; width: 100%; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول (يدعم الـ Enter)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        pwd = st.text_input("أدخل كلمة المرور", type="password")
        if st.form_submit_button("دخول للنظام (أو اضغط Enter)"):
            if pwd == "123":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
else:
    # القائمة الجانبية
    st.sidebar.markdown("<h2 style='text-align:center;'>🍎 القائمة</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("", ["🛒 شاشة البيع", "📦 المخزن والأصناف", "📊 التقارير"], label_visibility="collapsed")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع (تم الإصلاح) ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        
        if 'p_method' not in st.session_state: st.session_state.p_method = "نقداً"
        
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
                st.session_state.p_method = "نقداً"; st.rerun()
        with c_p2:
            if st.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                st.session_state.p_method = "تطبيق"; st.rerun()

        st.write("---")
        
        # مصفوفة لتخزين العناصر المختارة
        current_bill = []
        
        for cat in st.session_state.categories:
            with st.expander(f"📂 {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item, data in items.items():
                    col1, col2, col3, col4 = st.columns([0.5, 2, 2, 2])
                    with col1:
                        is_selected = st.checkbox("", key=f"chk_{item}")
                    with col2:
                        st.markdown(f"**{item}** \n<small>متوفر: {data['كمية']
