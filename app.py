import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📊")

# --- دالات المساعدة والحماية ---
def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except:
            return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# --- إدارة الفروع ---
def get_db_path(): return 'branches_config.csv'

def force_read_branches():
    df = safe_read_csv(get_db_path(), ['branch_name', 'user_name', 'password'])
    if df.empty:
        return pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])
    for c in df.columns:
        if df[c].dtype == 'object': df[c] = df[c].astype(str).str.strip()
    return df

# 2. تحميل البيانات (Session State)
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch', 'cat']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value', 'branch']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value', 'branch'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        st.session_state[state_key] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_role' not in st.session_state: st.session_state.user_role = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-box { background: white; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .sidebar-user { color: #27ae60; font-weight: 900; font-size: 22px; text-align: center; padding: 10px; border-bottom: 2px solid #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول
if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر المتكامل</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("👤 اسم المستخدم").strip()
            p = st.text_input("🔑 كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول"):
                if u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in = True
                    st.session_state.user_role = "admin"
                    st.session_state.active_user = "أبو عمر"
                    st.rerun()
                else:
                    db = force_read_branches()
                    match = db[(db['user_name'] == u) & (db['password'] == p)]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_role = "shop"
                        st.session_state.active_user = u
                        st.session_state.my_branch = match.iloc[0]['branch_name']
                        st.rerun()
                    else: st.error("بيانات الدخول غير صحيحة")
    st.stop()

# 5. بعد تسجيل الدخول: توزيع الشاشات
if st.session_state.user_role == "admin":
    # --- شاشة أبو عمر (المدير) ---
    st.sidebar.markdown(f"<div class='sidebar-user'>👑 المدير: {st.session_state.active_user}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة", ["📊 التقارير العامة", "🏪 إدارة الفروع", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    
    if menu == "📊 التقارير العامة":
        st.markdown("<h1 class='main-title'>📊 تقارير كافة الفروع</h1>", unsafe_allow_html=True)
        st.info("هنا تظهر بيانات جميع المحلات التابعة لك.")

    elif menu == "🏪 إدارة الفروع":
        st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1.5])
        with col1:
            with st.form("add_br"):
                n = st.text_input("اسم المحل")
                u = st.text_input("اسم مستخدم الفرع")
                p = st.text_input("كلمة مرور الفرع")
                if st.form_submit_button("إضافة الفرع"):
                    if n and u and p:
                        db = force_read_branches()
                        new_row = pd.DataFrame([{'branch_name':n, 'user_name':u, 'password':p}])
                        pd.concat([db, new_row]).to_csv(get_db_path(), index=False)
                        st.success("تمت الإضافة!")
                        st.rerun()
        with col2:
            st.table(force_read_branches())

else:
    # --- شاشة مسؤول الفرع (كود المحل الخاص بك) ---
    st.sidebar.markdown(f"<div class='sidebar-user'>🏪 فرع: {st.session_state.my_branch}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("نظام المحل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية"])
    
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    if menu == "🛒 نقطة البيع":
        st.markdown(f"<h1 class='main-title'>🛒 نقطة بيع: {st.session_state.my_branch}</h1>", unsafe_allow_html=True)
        # ... (نفس كود نقطة البيع الذي أرسلته سابقاً)
        st.write("شاشة البيع نشطة الآن...")

    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 أداء الفرع المالي</h1>", unsafe_allow_html=True)
        # حساب رأس المال لهذا الفرع فقط
        inv_df = pd.DataFrame(my_inv)
        if not inv_df.empty:
            cap = (inv_df['شراء'] * inv_df['كمية']).sum()
            st.metric("رأس مال المحل", f"{format_num(cap)} ₪")

if st.sidebar.button("🚨 خروج من النظام"):
    st.session_state.clear()
    st.rerun()
