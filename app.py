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

# --- إدارة الفروع والقاعدة ---
def get_db_path(): return 'branches_config.csv'

def initialize_db():
    path = get_db_path()
    if not os.path.exists(path) or os.path.getsize(path) > 0:
        try:
            return pd.read_csv(path)
        except:
            pass
    df = pd.DataFrame([
        {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
        {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
    ])
    df.to_csv(path, index=False)
    return df

# 2. تحميل البيانات الأساسية
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

FILES = {
    'sales': ('sales_final.csv', ['date','item','amount','profit','method','customer_name','customer_phone','bill_id','branch']),
    'expenses': ('expenses_final.csv', ['date','reason','amount','branch']),
    'waste': ('waste_final.csv', ['date','item','qty','loss_value','branch']),
    'adjust': ('inventory_adjustments.csv', ['date','item','diff_qty','loss_value','branch'])
}

for key, (file, cols) in FILES.items():
    if f"{key}_df" not in st.session_state:
        st.session_state[f"{key}_df"] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv',
        ['item','branch','قسم','شراء','بيع','كمية','سعر_القطعة'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    existing = cat_df['name'].tolist() if not cat_df.empty else []
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + existing))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
</style>
""", unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    _, col, _ = st.columns([1,1.2,1])
    with col:
        with st.form("login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                db = pd.read_csv(get_db_path())
                m = db[(db.user_name==u)&(db.password==p)]
                if not m.empty:
                    st.session_state.logged_in=True
                    st.session_state.active_user=u
                    st.session_state.user_role=m.iloc[0]['role']
                    st.session_state.my_branch=m.iloc[0]['branch_name']
                    st.rerun()
    st.stop()

# 5. القائمة
menu = st.sidebar.radio("القائمة",
    ["🛒 نقطة البيع","📦 المخزن والجرد","💸 المصروفات","📊 التقارير المالية","⚙️ إدارة الأصناف"])

# ⚙️ إدارة الأصناف
if menu=="⚙️ إدارة الأصناف":
    tab_add,_,tab_cats = st.tabs(["➕ إضافة أصناف","🛠️","📂 إدارة الأقسام"])

    with tab_add:
        cat = st.selectbox("اختر القسم", st.session_state.categories)
        with st.form("add_item", clear_on_submit=True):

            if cat=="سجائر":
                st.warning("🚬 نظام السجائر (علب + فرط)")
                n = st.text_input("اسم النوع")
                c1,c2 = st.columns(2)
                q_box = c1.text_input("عدد العلب","0")
                q_single = c2.text_input("عدد السجائر الفرط","0")
                buy = st.text_input("سعر العلبة")
                sell = st.text_input("سعر بيع العلبة")
                single_price = st.text_input("سعر السيجارة")
            else:
                n = st.text_input("اسم الصنف")
                q_box = st.text_input("الكمية","0")
                q_single="0"
                buy = st.text_input("سعر الشراء")
                sell = st.text_input("سعر البيع")
                single_price="0"

            if st.form_submit_button("حفظ"):
                qty = clean_num(q_box)+(clean_num(q_single)/20)
                st.session_state.inventory.append({
                    "item":n,"قسم":cat,"شراء":clean_num(buy),
                    "بيع":clean_num(sell),"كمية":qty,
                    "سعر_القطعة":clean_num(single_price),
                    "branch":st.session_state.my_branch
                })
                auto_save()
                st.success("تمت الإضافة")
                st.rerun()

    with tab_cats:
        with st.form("cat_add"):
            nc = st.text_input("قسم جديد")
            if st.form_submit_button("إضافة"):
                if nc and nc not in st.session_state.categories:
                    st.session_state.categories.append(nc)
                    auto_save(); st.rerun()
        for c in st.session_state.categories:
            col1,col2=st.columns([4,1])
            col1.write(c)
            if c!="سجائر" and col2.button("❌",key=c):
                st.session_state.categories.remove(c)
                auto_save(); st.rerun()
