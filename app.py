# ================== IMPORTS ==================
import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# ================== PAGE CONFIG ==================
st.set_page_config(
    page_title="نظام أبو عمر المتكامل 2026",
    layout="wide",
    page_icon="👑"
)

# ================== HELPERS ==================
def normalize_branch(x):
    return str(x).strip()

def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: 
        return str(val)

def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: 
        return 0.0

def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except:
            pass
    return pd.DataFrame(columns=default_cols)

# ================== BRANCH DB ==================
def get_db_path():
    return "branches_config.csv"

def initialize_db():
    path = get_db_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame([
            {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
            {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
        ])
        df.to_csv(path, index=False)
    df = pd.read_csv(path)
    df['branch_name'] = df['branch_name'].apply(normalize_branch)
    return df

# ================== SESSION INIT ==================
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

FILES = {
    'sales': ('sales_final.csv', ['date','item','amount','profit','method','customer_name','customer_phone','bill_id','branch']),
    'expenses': ('expenses_final.csv', ['date','reason','amount','branch']),
    'waste': ('waste_final.csv', ['date','item','qty','loss_value','branch']),
    'adjust': ('inventory_adjustments.csv', ['date','item','diff','branch'])
}

for key,(file,cols) in FILES.items():
    sk = f"{key}_df"
    if sk not in st.session_state:
        st.session_state[sk] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    inv = safe_read_csv('inventory_final.csv', ['item','branch','قسم','شراء','بيع','كمية'])
    if not inv.empty:
        inv['branch'] = inv['branch'].apply(normalize_branch)
    st.session_state.inventory = inv.to_dict('records')

if 'categories' not in st.session_state:
    cat = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = cat['name'].tolist() if not cat.empty else ["خضار","ألبان","منظفات"]

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# ================== LOGIN ==================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center'>🔐 تسجيل الدخول</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            db = pd.read_csv(get_db_path())
            db['branch_name'] = db['branch_name'].apply(normalize_branch)
            m = db[(db['user_name']==u) & (db['password']==p)]
            if not m.empty:
                row = m.iloc[0]
                st.session_state.logged_in = True
                st.session_state.user_role = row['role']
                st.session_state.active_user = u
                st.session_state.my_branch = normalize_branch(row['branch_name'])
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# ================== SIDEBAR ==================
st.sidebar.markdown(f"<div style='font-size:22px;font-weight:900'>👤 {st.session_state.active_user}</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("القائمة", ["🏪 إدارة الفروع","⚙️ إدارة الأصناف"])
else:
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع","📦 المخزن"])

# ================== MANAGE ITEMS ==================
if menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)

    branches = [normalize_branch(b) for b in pd.read_csv(get_db_path())['branch_name']]
    target_branch = st.selectbox("اختر الفرع", branches)

    with st.form("add_item"):
        n = st.text_input("اسم الصنف")
        c = st.selectbox("القسم", st.session_state.categories)
        b = st.text_input("شراء")
        s = st.text_input("بيع")
        q = st.text_input("كمية")
        if st.form_submit_button("حفظ"):
            st.session_state.inventory.append({
                "item": n,
                "قسم": c,
                "شراء": clean_num(b),
                "بيع": clean_num(s),
                "كمية": clean_num(q),
                "branch": normalize_branch(target_branch)
            })
            auto_save()
            st.success("تم الحفظ")
            st.rerun()

# ================== POS ==================
elif menu == "🛒 نقطة البيع":
    my_branch = normalize_branch(st.session_state.my_branch)
    my_inv = [i for i in st.session_state.inventory if i['branch']==my_branch]
    st.write("عدد الأصناف:", len(my_inv))
    st.table(pd.DataFrame(my_inv))

# ================== INVENTORY ==================
elif menu == "📦 المخزن":
    my_branch = normalize_branch(st.session_state.my_branch)
    my_inv = [i for i in st.session_state.inventory if i['branch']==my_branch]
    st.table(pd.DataFrame(my_inv))
