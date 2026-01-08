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

# دالة ذكية للقراءة تحمي من EmptyDataError
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            df = pd.read_csv(file_path)
            return df
        except:
            return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# --- إدارة الملفات والقواعد ---
def get_db_path(): return 'branches_config.csv'

def force_read_branches():
    df = safe_read_csv(get_db_path(), ['branch_name', 'user_name', 'password'])
    if df.empty:
        return pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])
    for c in df.columns:
        if df[c].dtype == 'object': df[c] = df[c].astype(str).str.strip()
    return df

# 2. تحميل البيانات (Session State) مع الحماية من الملفات الفارغة
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

# حالات التشغيل لشاشة الفرع
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق (CSS) - ستايل أبو عمر
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-box { background: white; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    .sidebar-user { color: #27ae60; font-weight: 900; font-size: 22px; text-align: center; padding: 10px; border-bottom: 2px solid #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر المتكامل</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("👤 اسم المستخدم").strip()
            p = st.text_input("🔑 كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول"):
                if u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
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

# 5. شاشة المدير العام (أبو عمر)
if st.session_state.user_role == "admin":
    st.sidebar.markdown(f"<div class='sidebar-user'>👑 المدير: {st.session_state.active_user}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة", ["📊 التقارير العامة", "🏪 إدارة الفروع", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    
    if menu == "📊 التقارير العامة":
        st.markdown("<h1 class='main-title'>📊 تقارير كافة الفروع</h1>", unsafe_allow_html=True)
        st.write("ملخص أداء النظام العام...")

    elif menu == "🏪 إدارة الفروع":
        st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1.5])
        with col1:
            with st.form("add"):
                n = st.text_input("اسم المحل").strip()
                u = st.text_input("المستخدم").strip()
                p = st.text_input("كلمة المرور").strip()
                if st.form_submit_button("حفظ"):
                    if n and u and p:
                        db = force_read_branches()
                        new_db = pd.concat([db, pd.DataFrame([{'branch_name':n,'user_name':u,'password':p}])])
                        new_db.to_csv(get_db_path(), index=False); st.rerun()
        with col2:
            st.table(force_read_branches())

# 6. شاشة مسؤول الفرع (كود المحل المدمج)
else:
    st.sidebar.markdown(f"<div class='sidebar-user'>🏪 فرع: {st.session_state.my_branch}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("نظام المحل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية"])
    
    # تصفية البضاعة الخاصة بالفرع الحالي فقط
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    if menu == "🛒 نقطة البيع":
        st.markdown(f"<h1 class='main-title'>🛒 بيع - {st.session_state.my_branch}</h1>", unsafe_allow_html=True)
        if st.session_state.show_cust_fields:
            c_n = st.text_input("اسم الزبون")
            if st.button("💾 حفظ"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, 'customer_name'] = c_n
                auto_save(); st.session_state.show_cust_fields = False; st.rerun()
        else:
            search_q = st.text_input("🔍 ابحث عن صنف...")
            bill_items = []
            for cat in st.session_state.categories:
                items = [i for i in my_inv if i.get('قسم') == cat]
                if search_q: items = [i for i in items if search_q in i['item']]
                if items:
                    with st.expander(f"📂 {cat}"):
                        for it in items:
                            c1, c2, c3 = st.columns([2, 1, 1])
                            c1.write(f"**{it['item']}** (متوفر: {it['كمية']})")
                            val = clean_num(c3.text_input("المقدار", key=f"v_{it['item']}"))
                            if val > 0:
                                qty = val / it['بيع']
                                bill_items.append({"item": it['item'], "qty": qty, "amount": val, "profit": (it['بيع']-it['شراء'])*qty, "cat": cat})
            if st.button("🚀 إتمام البيع"):
                if bill_items:
                    b_id = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        for inv_item in st.session_state.inventory:
                            if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                                inv_item['كمية'] -= e['qty']
                        new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون عام', 'bill_id': b_id, 'branch': st.session_state.my_branch, 'cat': e['cat']}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save(); st.session_state.show_cust_fields = True; st.rerun()

    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 مخزن الفرع</h1>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(my_inv))

    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 أرباح الفرع</h1>", unsafe_allow_html=True)
        inv_df = pd.DataFrame(my_inv)
        if not inv_df.empty:
            capital = (inv_df['شراء'] * inv_df['كمية']).sum()
            st.metric("رأس مال الفرع الحالي", f"{format_num(capital)} ₪")

if st.sidebar.button("🚪 خروج"):
    st.session_state.clear(); st.rerun()
