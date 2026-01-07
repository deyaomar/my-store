import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة (الواجهة الأصلية)
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📊")

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

# 2. إدارة البيانات والفروع
BRANCHES = ["المحل الأول", "المحل الثاني", "المحل الثالث"]

if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv('sales_vFinal.csv') if os.path.exists('sales_vFinal.csv') else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch', 'cat'])

if 'inventory' not in st.session_state:
    if os.path.exists('inventory_vFinal.csv'):
        st.session_state.inventory = pd.read_csv('inventory_vFinal.csv').to_dict('records')
    else:
        st.session_state.inventory = []

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_vFinal.csv', index=False)
    st.session_state.sales_df.to_csv('sales_vFinal.csv', index=False)

# 3. التنسيق (نفس الستايل الأخضر الأصلي)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 900; font-size: 20px; padding: 10px; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 26px; text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 15px; margin-bottom: 25px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول النظام</h1>", unsafe_allow_html=True)
    utype = st.selectbox("الحساب", ["أبو عمر", "مسؤول فرع"])
    b_sel = "الكل"
    if utype == "مسؤول فرع": b_sel = st.selectbox("المحل", BRANCHES)
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if (utype == "أبو عمر" and pwd == "admin") or (utype == "مسؤول فرع" and pwd == "123"):
            st.session_state.logged_in = True
            st.session_state.user_role = utype
            st.session_state.my_branch = b_sel
            st.rerun()
else:
    # القائمة الجانبية الأصلية كما هي
    st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
    
    if st.session_state.user_role == "أبو عمر":
        active_branch = st.sidebar.selectbox("تبديل المحل:", ["الكل"] + BRANCHES)
    else:
        active_branch = st.session_state.my_branch

    # ترتيب الأزرار الأصلي
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. نقطة البيع (الواجهة القديمة) ---
    if menu == "🛒 نقطة البيع":
        st.markdown(f"<h1 class='main-title'>🛒 نقطة بيع: {active_branch}</h1>", unsafe_allow_html=True)
        if active_branch == "الكل":
            st.warning("اختر محلاً للبيع")
        else:
            search_q = st.text_input("🔍 ابحث عن صنف...")
            branch_inv = [i for i in st.session_state.inventory if i['branch'] == active_branch]
            bill_items = []
            for item in branch_inv:
                if search_q.lower() in item['item'].lower():
                    c1, c2, c3 = st.columns([2, 1, 2])
                    c1.markdown(f"**{item['item']}**\n<small>متوفر: {format_num(item['qty'])}</small>", unsafe_allow_html=True)
                    mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item['item']}")
                    val = clean_num(c3.text_input("المقدار", key=f"v_{item['item']}"))
                    if val > 0:
                        qty = val if mode == "كجم" else val / item["sell"]
                        bill_items.append({"item": item["item"], "qty": qty, "amount": val if mode == "₪" else val * item["sell"], "profit": (item["sell"] - item["buy"]) * qty, "cat": item["cat"]})
            
            if st.button("🚀 إتمام البيع", type="primary") and bill_items:
                bid = str(uuid.uuid4())[:8]
                for e in bill_items:
                    for i in st.session_state.inventory:
                        if i['item'] == e['item'] and i['branch'] == active_branch: i['qty'] -= e['qty']
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'branch': active_branch, 'bill_id': bid, 'cat': e['cat']}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.success("تم!"); st.rerun()

    # --- 2. التقارير المالية (الواجهة اللي طلبتها بالظبط) ---
    elif menu == "📊 التقارير المالية":
        st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
        
        s_df = st.session_state.sales_df.copy()
        if active_branch != "الكل": s_df = s_df[s_df['branch'] == active_branch]
        
        s_df['date_dt'] = pd.to_datetime(s_df['date'])
        today = datetime.now().date()
        
        d_profit = s_df[s_df['date_dt'].dt.date == today]['profit'].sum()
        
        inv_df = pd.DataFrame(st.session_state.inventory)
        if active_branch != "الكل" and not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]
        total_cap = (inv_df['buy'] * inv_df['qty']).sum() if not inv_df.empty else 0

        # الكروت الأصلية
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-box'><div>صافي ربح اليوم</div><div class='metric-value'>{format_num(d_profit)} ₪</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'><div>إجمالي مبيعات اليوم</div><div class='metric-value'>{format_num(s_df[s_df['date_dt'].dt.date == today]['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-box' style='border-color:#e67e22'><div>رأس مال المحل</div><div class='metric-value'>{format_num(total_cap)} ₪</div></div>", unsafe_allow_html=True)

        st.markdown("### 💰 رأس مال الأقسام")
        if not inv_df.empty:
            cat_cap = inv_df.assign(v=inv_df['buy']*inv_df['qty']).groupby('cat')['v'].sum().reset_index()
            for _, row in cat_cap.iterrows():
                st.write(f"**{row['cat']}:** {format_num(row['v'])} ₪")

    # --- 3. الإعدادات (نفس الواجهة القديمة) ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        with st.form("add"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("الصنف"); br = c2.selectbox("المحل", BRANCHES); ct = c3.selectbox("القسم", ["خضار", "مكسرات", "أخرى"])
            b = c1.number_input("شراء"); s = c2.number_input("بيع"); q = c3.number_input("كمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory.append({'item':n, 'branch':br, 'cat':ct, 'buy':b, 'sell':s, 'qty':q})
                auto_save(); st.rerun()

    # باقي الأقسام (المخزن والمصروفات) تظهر هنا بنفس الطريقة..
