import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

# دالات التنسيق والتنظيف
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

# دالة القراءة الآمنة
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try: return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# --- نظام تسجيل الدخول المحصن ---
def get_db_path(): 
    return 'branches_config.csv'

def force_init_db():
    path = get_db_path()
    default_data = [
        {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
        {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
    ]
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        pd.DataFrame(default_data).to_csv(path, index=False, encoding='utf-8-sig')
    return pd.read_csv(path, encoding='utf-8-sig').assign(
        role=lambda df: df['role'] if 'role' in df.columns else 'shop'
    )

# 2. تحميل البيانات الأساسية
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = force_init_db()

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        st.session_state[state_key] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية', 'سعر_القطعة'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + (cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"])))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم (CSS الأصلي)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; direction: rtl; }
[data-testid="stSidebar"] { background-color: #0f172a !important; border-left: 3px solid #10b981; }
.sidebar-user { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white !important; font-weight: 900; font-size: 22px; text-align: center; padding: 20px; border-radius: 15px; margin: 10px; }
.nav-label { color: #94a3b8; font-size: 14px; margin: 20px 10px 10px 0; font-weight: bold; }
[data-testid="stSidebar"] .stRadio div label { background-color: #1e293b; border-radius: 12px; padding: 10px 15px !important; margin-bottom: 8px; border: 1px solid #334155; }
[data-testid="stSidebar"] .stRadio div label[data-selected="true"] { background-color: #10b981 !important; border-color: #059669; }
[data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 700 !important; font-size: 16px !important; }
.main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
.metric-container { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #10b981; text-align: center; margin-bottom: 20px; }
.sale-card { background: #f8fafc; padding: 15px; border-radius: 12px; border-right: 6px solid #10b981; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        u_in = st.text_input("👤 اسم المستخدم").strip()
        p_in = st.text_input("🔑 كلمة المرور", type="password").strip()
        if st.form_submit_button("دخول"):
            db = force_init_db()
            db['user_name'] = db['user_name'].astype(str).str.strip()
            db['password'] = db['password'].astype(str).str.strip()
            match = db[(db['user_name'] == u_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.active_user = u_in
                st.session_state.my_branch = match.iloc[0]['branch_name']
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='nav-label'>🧭 التنقل السريع</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"], label_visibility="collapsed")
    st.sidebar.markdown("<div class='nav-label'>🏠 تصفية حسب الفرع:</div>", unsafe_allow_html=True)
    active_branch = st.sidebar.selectbox("", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist(), label_visibility="collapsed")
else:
    menu = st.sidebar.radio("", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"], label_visibility="collapsed")
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- الصفحات (اختصارا، نركز على صفحات المدير العام والمدير الفرع) ---

if st.session_state.user_role == "admin" and menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع - المدير العام</h1>", unsafe_allow_html=True)
    db = pd.read_csv(get_db_path())

    st.subheader("➕ إضافة فرع جديد")
    with st.form("add_branch"):
        bn = st.text_input("اسم الفرع")
        un = st.text_input("اسم المستخدم")
        pw = st.text_input("كلمة المرور")
        if st.form_submit_button("إضافة"):
            if bn and un and pw:
                db = pd.concat([db, pd.DataFrame([{'branch_name': bn, 'user_name': un, 'password': pw, 'role': 'shop'}])], ignore_index=True)
                db.to_csv(get_db_path(), index=False)
                st.success("تمت الإضافة")
                st.rerun()

    st.divider()
    st.subheader("✏️ تعديل / حذف الفروع")
    for i, row in db.iterrows():
        if row['role'] != 'shop':
            continue
        with st.expander(f"🏬 {row['branch_name']}"):
            new_bn = st.text_input("اسم الفرع", row['branch_name'], key=f"bn_{i}")
            new_un = st.text_input("اسم المستخدم", row['user_name'], key=f"un_{i}")
            new_pw = st.text_input("كلمة المرور", row['password'], key=f"pw_{i}")
            c1, c2 = st.columns(2)
            if c1.button("💾 حفظ التعديلات", key=f"save_{i}"):
                db.loc[i, ['branch_name', 'user_name', 'password']] = [new_bn, new_un, new_pw]
                db.to_csv(get_db_path(), index=False)
                st.success("تم التعديل")
                st.rerun()
            if c2.button("🗑️ حذف الفرع", key=f"del_{i}"):
                db = db.drop(i)
                db.to_csv(get_db_path(), index=False)
                st.warning("تم الحذف")
                st.rerun()
