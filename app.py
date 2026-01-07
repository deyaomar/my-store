import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة والتنسيق الأصلي
st.set_page_config(page_title="نظام أبو عمر - الإدارة العامة", layout="wide", page_icon="🏢")

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

# 2. إدارة البيانات (المحلات والمستخدمين)
def load_data():
    # قاعدة بيانات المحلات والمستخدمين
    if 'branches_db' not in st.session_state:
        if os.path.exists('branches_config.csv'):
            st.session_state.branches_db = pd.read_csv('branches_config.csv')
        else:
            # افتراضياً عند أول تشغيل
            st.session_state.branches_db = pd.DataFrame([
                {'branch_name': 'المحل الأول', 'user_name': 'user1', 'password': '123'}
            ])
    
    if 'sales_df' not in st.session_state:
        st.session_state.sales_df = pd.read_csv('sales_vFinal.csv') if os.path.exists('sales_vFinal.csv') else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'branch', 'cat'])
    
    if 'inventory' not in st.session_state:
        if os.path.exists('inventory_vFinal.csv'):
            st.session_state.inventory = pd.read_csv('inventory_vFinal.csv').to_dict('records')
        else:
            st.session_state.inventory = []

def save_all():
    st.session_state.branches_db.to_csv('branches_config.csv', index=False)
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_vFinal.csv', index=False)
    st.session_state.sales_df.to_csv('sales_vFinal.csv', index=False)

load_data()

# 3. التنسيق الجمالي
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 26px; text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 15px; margin-bottom: 25px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام تسجيل الدخول المحمي
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔒 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    col_log, _ = st.columns([1, 1])
    with col_log:
        u_in = st.text_input("اسم المستخدم")
        p_in = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if u_in == "أبو عمر" and p_in == "admin":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.active_user = "أبو عمر"
                st.rerun()
            else:
                db = st.session_state.branches_db
                match = db[(db['user_name'] == u_in) & (db['password'] == p_in)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "shop"
                    st.session_state.my_branch = match.iloc[0]['branch_name']
                    st.session_state.active_user = u_in
                    st.rerun()
                else:
                    st.error("خطأ في البيانات")
    st.stop()

# 5. الواجهة بعد الدخول (تم حل مشكلة AttributeError هنا)
role = st.session_state.get('user_role', 'shop')
user_name = st.session_state.get('active_user', 'مستخدم')

st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {user_name} 👋</div>", unsafe_allow_html=True)

if role == "admin":
    b_list = ["الكل"] + st.session_state.branches_db['branch_name'].tolist()
    active_branch = st.sidebar.selectbox("تبديل المحل:", b_list)
    menu = st.sidebar.radio("التنقل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير", "🏗️ إدارة المحلات", "⚙️ الإعدادات"])
else:
    active_branch = st.session_state.get('my_branch', 'المحل الأول')
    menu = st.sidebar.radio("التنقل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية"])

if st.sidebar.button("🚪 خروج"):
    st.session_state.clear(); st.rerun()

# --- إدارة المحلات (للمدير العام فقط) ---
if menu == "🏗️ إدارة المحلات":
    st.markdown("<h1 class='main-title'>🏗️ التحكم في المحلات والمستخدمين</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("إضافة محل ومسؤول جديد")
        nb = st.text_input("اسم المحل")
        nu = st.text_input("اسم المستخدم (لصاحب المحل)")
        np = st.text_input("كلمة المرور", type="password")
        if st.button("حفظ المحل"):
            new_r = {'branch_name': nb, 'user_name': nu, 'password': np}
            st.session_state.branches_db = pd.concat([st.session_state.branches_db, pd.DataFrame([new_r])], ignore_index=True)
            save_all(); st.success("تم الحفظ!"); st.rerun()
    with c2:
        st.subheader("قائمة المحلات الحالية")
        st.dataframe(st.session_state.branches_db, use_container_width=True)

# --- نقطة البيع (الواجهة المعتادة) ---
elif menu == "🛒 نقطة البيع":
    st.markdown(f"<h1 class='main-title'>🛒 بيع - {active_branch}</h1>", unsafe_allow_html=True)
    if active_branch == "الكل":
        st.warning("اختر محلاً محدداً من القائمة الجانبية للبيع")
    else:
        search = st.text_input("🔍 بحث...")
        b_inv = [i for i in st.session_state.inventory if i['branch'] == active_branch]
        bill = []
        for item in b_inv:
            if search.lower() in item['item'].lower():
                col1, col2, col3 = st.columns([2, 1, 2])
                col1.markdown(f"**{item['item']}**\n<small>متوفر: {format_num(item['qty'])}</small>", unsafe_allow_html=True)
                m = col2.radio("بـ", ["₪", "كجم"], key=f"m_{item['item']}")
                v = clean_num(col3.text_input("المقدار", key=f"v_{item['item']}"))
                if v > 0:
                    q = v if m == "كجم" else v / item['sell']
                    bill.append({"item": item['item'], "qty": q, "amount": v if m == "₪" else v * item['sell'], "profit": (item['sell'] - item['buy']) * q, "cat": item['cat']})
        
        if st.button("🚀 إتمام العملية") and bill:
            for e in bill:
                for i in st.session_state.inventory:
                    if i['item'] == e['item'] and i['branch'] == active_branch: i['qty'] -= e['qty']
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'branch': active_branch, 'cat': e['cat']}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            save_all(); st.success("✅ تم بنجاح"); st.rerun()

# --- التقارير (الكروت الثلاثية الأصلية) ---
elif menu == "📊 التقارير" or menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 تقارير {active_branch}</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df.copy()
    if active_branch != "الكل": s_df = s_df[s_df['branch'] == active_branch]
    
    today_sales = s_df[pd.to_datetime(s_df['date']).dt.date == datetime.now().date()]
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-box'><div>مبيعات اليوم</div><div class='metric-value'>{format_num(today_sales['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'><div>أرباح اليوم</div><div class='metric-value'>{format_num(today_sales['profit'].sum())} ₪</div></div>", unsafe_allow_html=True)
    
    # حساب رأس مال المحل المختار
    inv_df = pd.DataFrame(st.session_state.inventory)
    if active_branch != "الكل" and not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]
    cap = (inv_df['buy'] * inv_df['qty']).sum() if not inv_df.empty else 0
    c3.markdown(f"<div class='metric-box' style='border-color:#e67e22'><div>رأس مال البضاعة</div><div class='metric-value'>{format_num(cap)} ₪</div></div>", unsafe_allow_html=True)

# --- الإعدادات (إضافة الأصناف) ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إضافة بضاعة</h1>", unsafe_allow_html=True)
    with st.form("add"):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("اسم الصنف")
        b = c2.selectbox("المحل", st.session_state.branches_db['branch_name'].tolist())
        ct = c3.selectbox("القسم", ["خضار", "مكسرات", "أخرى"])
        buy = c1.number_input("سعر الشراء")
        sell = c2.number_input("سعر البيع")
        qty = c3.number_input("الكمية")
        if st.form_submit_button("إضافة"):
            st.session_state.inventory.append({'item':n, 'branch':b, 'cat':ct, 'buy':buy, 'sell':sell, 'qty':qty})
            save_all(); st.rerun()
