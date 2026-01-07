import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# ==========================================
# 1. إعدادات الصفحة والتنسيق الاحترافي
# ==========================================
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

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 15px; margin-bottom: 20px;}
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 25px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-label { font-size: 14px; color: #7f8c8d; font-weight: bold; }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    .section-header { background: #f1f4f6; padding: 10px; border-radius: 10px; color: #2c3e50; font-weight: 900; margin: 15px 0; border-right: 5px solid #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. الثوابت وإدارة البيانات
# ==========================================
BRANCHES = ["المحل الأول", "المحل الثاني", "المحل الثالث"]
CATS = ["خضار وفواكه", "مكسرات", "ألبان وأجبان", "منظفات", "أخرى"]

def load_data():
    if 'sales_df' not in st.session_state:
        st.session_state.sales_df = pd.read_csv('sales_all_v4.csv') if os.path.exists('sales_all_v4.csv') else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch', 'cat'])
    if 'expenses_df' not in st.session_state:
        st.session_state.expenses_df = pd.read_csv('expenses_all_v4.csv') if os.path.exists('expenses_all_v4.csv') else pd.DataFrame(columns=['date', 'reason', 'amount', 'branch'])
    if 'inventory' not in st.session_state:
        if os.path.exists('inventory_all_v4.csv'):
            st.session_state.inventory = pd.read_csv('inventory_all_v4.csv').to_dict('records')
        else:
            st.session_state.inventory = []

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_all_v4.csv', index=False)
    st.session_state.sales_df.to_csv('sales_all_v4.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_all_v4.csv', index=False)

load_data()

# ==========================================
# 3. نظام بوابة الدخول
# ==========================================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🏢 نظام إدارة فروع أبو عمر</h1>", unsafe_allow_html=True)
    with st.container():
        col_main = st.columns([1, 2, 1])[1]
        with col_main:
            u_type = st.selectbox("نوع الحساب", ["أبو عمر (المدير العام)", "مسؤول فرع"])
            b_choice = "الكل"
            if u_type == "مسؤول فرع":
                b_choice = st.selectbox("اختر الفرع", BRANCHES)
            u_pwd = st.text_input("كلمة المرور", type="password")
            
            if st.button("🚀 دخول النظام", use_container_width=True):
                if (u_type == "أبو عمر (المدير العام)" and u_pwd == "admin") or (u_type == "مسؤول فرع" and u_pwd == "123"):
                    st.session_state.logged_in = True
                    st.session_state.user_role = u_type
                    st.session_state.my_branch = b_choice
                    st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# ==========================================
# 4. واجهة التحكم (بعد الدخول)
# ==========================================
role = st.session_state.user_role
my_br = st.session_state.my_branch

st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {role}</div>", unsafe_allow_html=True)

if role == "أبو عمر (المدير العام)":
    active_branch = st.sidebar.selectbox("🏠 استعراض فرع:", ["الكل"] + BRANCHES)
else:
    active_branch = my_br
    st.sidebar.success(f"📍 الفرع الحالي: {active_branch}")

menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.logged_in = False
    st.session_state.clear()
    st.rerun()

# ------------------------------------------
# أ. نقطة البيع
# ------------------------------------------
if menu == "🛒 نقطة البيع":
    if active_branch == "الكل":
        st.warning("⚠️ يرجى اختيار فرع محدد من القائمة الجانبية للبيع")
    else:
        st.markdown(f"<h1 class='main-title'>🛒 بيع بضاعة - {active_branch}</h1>", unsafe_allow_html=True)
        with st.expander("👤 بيانات الزبون (اختياري)"):
            c_name = st.text_input("الاسم", "زبون عام")
            c_phone = st.text_input("رقم الهاتف")

        search = st.text_input("🔍 ابحث عن صنف...")
        inv_list = [i for i in st.session_state.inventory if i['branch'] == active_branch]
        
        cart = []
        for item in inv_list:
            if search.lower() in item['item'].lower():
                c1, c2, c3 = st.columns([2,1,2])
                c1.markdown(f"**{item['item']}**\n<small>متوفر: {format_num(item['qty'])}</small>", unsafe_allow_html=True)
                m = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item['item']}", horizontal=True)
                v = clean_num(c3.text_input("المقدار", key=f"v_{item['item']}"))
                if v > 0:
                    qty_to_sell = v if m == "كجم" else v / item['sell']
                    cart.append({"item": item['item'], "qty": qty_to_sell, "amount": v if m == "₪" else v * item['sell'], "profit": (item['sell'] - item['buy']) * qty_to_sell, "cat": item.get('cat', 'أخرى')})
        
        if st.button("🚀 إتمام الفاتورة", type="primary") and cart:
            bid = str(uuid.uuid4())[:8]
            for e in cart:
                for i in st.session_state.inventory:
                    if i['item'] == e['item'] and i['branch'] == active_branch:
                        i['qty'] -= e['qty']
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': 'تطبيق' if c_phone else 'نقدي', 'branch': active_branch, 'bill_id': bid, 'customer_name': c_name, 'customer_phone': c_phone, 'cat': e['cat']}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            auto_save(); st.success("✅ تم تسجيل البيع بنجاح"); st.rerun()

# ------------------------------------------
# ب. التقارير المالية (شطارة أبو عمر)
# ------------------------------------------
elif menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية: {active_branch}</h1>", unsafe_allow_html=True)
    
    # تحضير البيانات المفلترة
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    if active_branch != "الكل":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]
    
    s_df['date_dt'] = pd.to_datetime(s_df['date'])
    today = datetime.now().date()
    start_week = today - timedelta(days=(today.weekday() + 2) % 7)

    # حساب الكروت
    d_profit = s_df[s_df['date_dt'].dt.date == today]['profit'].sum()
    d_exp = e_df[pd.to_datetime(e_df['date']).dt.date == today]['amount'].sum()
    
    w_profit = s_df[s_df['date_dt'].dt.date >= start_week]['profit'].sum()
    w_exp = e_df[pd.to_datetime(e_df['date']).dt.date >= start_week]['amount'].sum()

    inv_df = pd.DataFrame(st.session_state.inventory)
    if active_branch != "الكل" and not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]
    cap = (inv_df['buy'] * inv_df['qty']).sum() if not inv_df.empty else 0

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='metric-box'><div class='metric-label'>صافي ربح اليوم</div><div class='metric-value'>{format_num(d_profit - d_exp)} ₪</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-box'><div class='metric-label'>صافي ربح الأسبوع</div><div class='metric-value'>{format_num(w_profit - w_exp)} ₪</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-box' style='border-right-color:#e67e22'><div class='metric-label'>رأس مال البضاعة بالمخزن</div><div class='metric-value'>{format_num(cap)} ₪</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["💰 رأس مال الأقسام", "🗓️ سجل الأيام", "👤 سجل الزبائن"])

    with t1:
        if not inv_df.empty:
            cat_rep = inv_df.assign(v=inv_df['buy']*inv_df['qty']).groupby('cat')['v'].sum().reset_index()
            st.markdown("<div class='section-header'>توزيع رأس المال لكل قسم</div>", unsafe_allow_html=True)
            st.table(cat_rep.rename(columns={'cat':'القسم', 'v':'قيمة رأس المال (₪)'}))
        else: st.info("لا توجد بضاعة مسجلة.")

    with t2:
        if not s_df.empty:
            daily_rep = s_df[s_df['date_dt'].dt.date >= start_week].groupby(s_df['date_dt'].dt.date).agg({'amount':'sum','profit':'sum'}).reset_index()
            st.table(daily_rep.rename(columns={'date_dt':'التاريخ', 'amount':'المبيعات', 'profit':'الربح'}))

    with t3:
        cust_log = s_df[s_df['customer_phone'] != ""].copy()
        if not cust_log.empty:
            st.dataframe(cust_log[['date', 'customer_name', 'amount', 'item', 'branch']], use_container_width=True)
        else: st.info("لا يوجد سجل زبائن حالياً.")

# ------------------------------------------
# ج. المخزن والمصروفات والإعدادات
# ------------------------------------------
elif menu == "📦 المخزن":
    st.markdown(f"<h1 class='main-title'>📦 جرد بضاعة: {active_branch}</h1>", unsafe_allow_html=True)
    df = pd.DataFrame(st.session_state.inventory)
    if active_branch != "الكل": df = df[df['branch'] == active_branch]
    st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "💸 المصروفات":
    st.markdown(f"<h1 class='main-title'>💸 مصروفات: {active_branch}</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r = st.text_input("بيان المصروف")
        a = st.number_input("المبلغ", 0.0)
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date':datetime.now().strftime("%Y-%m-%d"), 'reason':r, 'amount':a, 'branch':active_branch if active_branch != "الكل" else "عام"}])], ignore_index=True)
            auto_save(); st.rerun()
    st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == active_branch] if active_branch != "الكل" else st.session_state.expenses_df, use_container_width=True)

elif menu == "⚙️ الإعدادات":
    if role != "أبو عمر (المدير العام)":
        st.error("🔒 صلاحية الإعدادات للمدير العام فقط.")
    else:
        st.markdown("<h1 class='main-title'>⚙️ إضافة أصناف وتوزيع الفروع</h1>", unsafe_allow_html=True)
        with st.form("add_new"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("اسم الصنف")
            br = c2.selectbox("توزيع لفرع:", BRANCHES)
            ct = c3.selectbox("القسم", CATS)
            q = c1.number_input("الكمية", 0.0)
            b = c2.number_input("تكلفة الشراء", 0.0)
            s = c3.number_input("سعر البيع", 0.0)
            if st.form_submit_button("إضافة للمخزن الموحد"):
                st.session_state.inventory.append({'item':n, 'branch':br, 'qty':q, 'buy':b, 'sell':s, 'cat':ct})
                auto_save(); st.success(f"تمت إضافة {n} لـ {br}"); st.rerun()
            
