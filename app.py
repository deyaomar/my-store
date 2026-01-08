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
        try: return pd.read_csv(file_path, encoding='utf-8-sig')
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# --- نظام تسجيل الدخول وإدارة الفروع ---
def get_db_path(): return 'branches_config.csv'

def force_init_db():
    path = get_db_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        default_data = [
            {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
            {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
        ]
        pd.DataFrame(default_data).to_csv(path, index=False, encoding='utf-8-sig')
    
    df = pd.read_csv(path, encoding='utf-8-sig')
    if 'role' not in df.columns:
        df['role'] = 'shop'
        df.loc[df['user_name'] == 'أبو عمر', 'role'] = 'admin'
    return df

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
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False, encoding='utf-8-sig')
    st.session_state.sales_df.to_csv('sales_final.csv', index=False, encoding='utf-8-sig')
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False, encoding='utf-8-sig')

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
            # اقرأ آخر نسخة من الملف مباشرة
            fresh_db = force_init_db()
            st.session_state.branches_db = fresh_db
            
            u_clean = u_in.replace("أ", "ا")
            match = fresh_db[(fresh_db['user_name'].str.replace("أ", "ا") == u_clean) & (fresh_db['password'] == p_in)]
            
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.active_user = match.iloc[0]['user_name']
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
    all_brs = st.session_state.branches_db['branch_name'].tolist()
    active_branch = st.sidebar.selectbox("", ["كافة الفروع"] + all_brs, label_visibility="collapsed")
else:
    menu = st.sidebar.radio("", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"], label_visibility="collapsed")
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear()
    st.rerun()

# --- صفحات إدارة الفروع ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع والمستخدمين</h1>", unsafe_allow_html=True)
    
    with st.expander("➕ إضافة فرع جديد", expanded=False):
        with st.form("add_branch_form"):
            new_bn = st.text_input("اسم المحل / الفرع")
            new_un = st.text_input("اسم المستخدم")
            new_pw = st.text_input("كلمة المرور")
            if st.form_submit_button("حفظ الفرع الجديد"):
                if new_bn and new_un and new_pw:
                    new_row = {'branch_name': new_bn, 'user_name': new_un, 'password': new_pw, 'role': 'shop'}
                    current_db = force_init_db()
                    updated_db = pd.concat([current_db, pd.DataFrame([new_row])], ignore_index=True)
                    updated_db.to_csv(get_db_path(), index=False, encoding='utf-8-sig')
                    st.session_state.branches_db = updated_db
                    st.success(f"تم إضافة {new_bn} بنجاح. يمكنك الآن تسجيل الدخول بهذا الحساب.")
                    st.rerun()

    st.write("### قائمة الفروع الحالية")
    db_display = st.session_state.branches_db.copy()
    
    for index, row in db_display.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            col1.write(f"**الفرع:** {row['branch_name']}")
            col2.write(f"**المستخدم:** {row['user_name']}")
            is_admin = True if row.get('role','shop') == 'admin' else False
            if not is_admin:
                if col3.button("📝 تعديل", key=f"edit_{index}"):
                    st.session_state.edit_index = index
                if col4.button("🗑️ حذف", key=f"del_{index}"):
                    st.session_state.branches_db = st.session_state.branches_db.drop(index)
                    st.session_state.branches_db.to_csv(get_db_path(), index=False, encoding='utf-8-sig')
                    st.warning("تم حذف الفرع")
                    st.rerun()
        st.divider()

    if 'edit_index' in st.session_state:
        idx = st.session_state.edit_index
        st.markdown("---")
        st.subheader(f"تعديل بيانات: {st.session_state.branches_db.loc[idx, 'branch_name']}")
        with st.form("edit_form"):
            e_bn = st.text_input("الاسم الجديد", value=st.session_state.branches_db.loc[idx, 'branch_name'])
            e_un = st.text_input("المستخدم الجديد", value=st.session_state.branches_db.loc[idx, 'user_name'])
            e_pw = st.text_input("كلمة المرور الجديدة", value=st.session_state.branches_db.loc[idx, 'password'])
            if st.form_submit_button("تحديث البيانات"):
                st.session_state.branches_db.loc[idx, ['branch_name','user_name','password']] = [e_bn,e_un,e_pw]
                st.session_state.branches_db.to_csv(get_db_path(), index=False, encoding='utf-8-sig')
                del st.session_state.edit_index
                st.success("تم التحديث")
                st.rerun()
        if st.button("إلغاء التعديل"):
            del st.session_state.edit_index
            st.rerun()
