import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل - الفروع", layout="wide", page_icon="📊")

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

# 2. تعريف الفروع (عدلها حسب أسماء محلاتك)
BRANCHES = ["المحل الأول", "المحل الثاني", "المحل الثالث"]

# 3. إدارة البيانات
def load_data():
    if 'sales_df' not in st.session_state:
        st.session_state.sales_df = pd.read_csv('sales_v3.csv') if os.path.exists('sales_v3.csv') else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch', 'cat'])
    if 'expenses_df' not in st.session_state:
        st.session_state.expenses_df = pd.read_csv('expenses_v3.csv') if os.path.exists('expenses_v3.csv') else pd.DataFrame(columns=['date', 'reason', 'amount', 'branch'])
    if 'inventory' not in st.session_state:
        if os.path.exists('inventory_v3.csv'):
            st.session_state.inventory = pd.read_csv('inventory_v3.csv').to_dict('records')
        else:
            st.session_state.inventory = [] # [{item, branch, qty, buy, sell, cat}]
    if 'categories' not in st.session_state:
        st.session_state.categories = ["خضار وفواكه", "مكسرات", "أخرى"]

load_data()

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_v3.csv', index=False)
    st.session_state.sales_df.to_csv('sales_v3.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_v3.csv', index=False)

# 4. التنسيق الجمالي (نفس الستايل اللي بنحبه)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 26px; text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 15px; margin-bottom: 20px;}
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 25px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-label { font-size: 15px; color: #7f8c8d; font-weight: bold; }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    .section-header { background: #f1f4f6; padding: 10px; border-radius: 10px; color: #2c3e50; font-weight: 900; margin: 15px 0; border-right: 5px solid #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# 5. الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام أبو عمر لإدارة الفروع</h1>", unsafe_allow_html=True)
    user_type = st.selectbox("من أنت؟", ["أبو عمر (المدير العام)", "مسؤول محل"])
    branch_choice = "الكل"
    if user_type == "مسؤول محل":
        branch_choice = st.selectbox("اختر المحل الخاص بك", BRANCHES)
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول للنظام"):
        if (user_type == "أبو عمر (المدير العام)" and pwd == "admin") or (user_type == "مسؤول محل" and pwd == "123"):
            st.session_state.logged_in = True
            st.session_state.user_role = user_type
            st.session_state.my_branch = branch_choice
            st.rerun()
else:
    role = st.session_state.get('user_role', '')
    st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {role}</div>", unsafe_allow_html=True)
    
    if role == "أبو عمر (المدير العام)":
        active_branch = st.sidebar.selectbox("🏠 التحكم في فرع:", ["الكل"] + BRANCHES)
    else:
        active_branch = st.session_state.get('my_branch')
        st.sidebar.info(f"📍 أنت في: {active_branch}")

    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج آمن"):
        st.session_state.clear(); st.rerun()

    # --- 1. نقطة البيع (بنفس نظام الربط بالزبون) ---
    if menu == "🛒 نقطة البيع":
        if active_branch == "الكل":
            st.warning("الرجاء اختيار فرع محدد من القائمة الجانبية للبيع")
        else:
            st.markdown(f"<h1 class='main-title'>🛒 بيع بضاعة - {active_branch}</h1>", unsafe_allow_html=True)
            # نظام إدخال بيانات الزبون (التطبيق)
            with st.expander("👤 بيانات الزبون (اختياري - مبيعات التطبيق)"):
                c_name = st.text_input("اسم الزبون", value="زبون عام")
                c_phone = st.text_input("رقم الهاتف")

            search = st.text_input("🔍 بحث عن صنف في هذا المحل...")
            branch_inv = [i for i in st.session_state.inventory if i['branch'] == active_branch]
            
            bill_items = []
            for item in branch_inv:
                if search.lower() in item['item'].lower():
                    c1, c2, c3 = st.columns([2,1,2])
                    c1.markdown(f"**{item['item']}**\n<small>متوفر: {format_num(item['qty'])} ({item['cat']})</small>", unsafe_allow_html=True)
                    mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item['item']}_{active_branch}", horizontal=True)
                    val = clean_num(c3.text_input("المقدار", key=f"v_{item['item']}_{active_branch}"))
                    if val > 0:
                        qty = val if mode == "كجم" else val / item['sell']
                        bill_items.append({"item": item['item'], "qty": qty, "amount": val if mode == "₪" else val * item['sell'], "profit": (item['sell'] - item['buy']) * qty, "cat": item['cat']})
            
            if st.button("🚀 تنفيذ عملية البيع", type="primary") and bill_items:
                b_id = str(uuid.uuid4())[:8]
                for e in bill_items:
                    for inv_item in st.session_state.inventory:
                        if inv_item['item'] == e['item'] and inv_item['branch'] == active_branch:
                            inv_item['qty'] -= e['qty']
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': 'تطبيق' if c_phone else 'نقدي', 'branch': active_branch, 'bill_id': b_id, 'customer_name': c_name, 'customer_phone': c_phone, 'cat': e['cat']}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.success("✅ تم تسجيل البيع!"); st.rerun()

    # --- 2. المخزن ---
    elif menu == "📦 المخزن":
        st.markdown(f"<h1 class='main-title'>📦 بضاعة {active_branch}</h1>", unsafe_allow_html=True)
        if st.session_state.inventory:
            df_inv = pd.DataFrame(st.session_state.inventory)
            if active_branch != "الكل": df_inv = df_inv[df_inv['branch'] == active_branch]
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
        else: st.info("المخزن فارغ حالياً.")

    # --- 3. التقارير المالية (رجوع "شطارتي" بكامل قوتها) ---
    elif menu == "📊 التقارير المالية":
        st.markdown(f"<h1 class='main-title'>📊 التقارير المالية: {active_branch}</h1>", unsafe_allow_html=True)
        
        # فلترة البيانات
        sales = st.session_state.sales_df.copy()
        exps = st.session_state.expenses_df.copy()
        if active_branch != "الكل":
            sales = sales[sales['branch'] == active_branch]
            exps = exps[exps['branch'] == active_branch]
        
        sales['date_dt'] = pd.to_datetime(sales['date'])
        today = datetime.now().date()
        start_week = today - timedelta(days=(today.weekday() + 2) % 7)

        # حساب الصافي (أرباح - مصروفات)
        d_profit = sales[sales['date_dt'].dt.date == today]['profit'].sum()
        d_exp = exps[pd.to_datetime(exps['date']).dt.date == today]['amount'].sum()
        
        w_profit = sales[sales['date_dt'].dt.date >= start_week]['profit'].sum()
        w_exp = exps[pd.to_datetime(exps['date']).dt.date >= start_week]['amount'].sum()

        # حساب رأس المال من المخزن
        inv_df = pd.DataFrame(st.session_state.inventory)
        if active_branch != "الكل" and not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]
        cap_val = (inv_df['buy'] * inv_df['qty']).sum() if not inv_df.empty else 0

        # الكروت اللي بتحبها يا أبو عمر
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric-box'><div class='metric-label'>صافي ربح اليوم</div><div class='metric-value'>{format_num(d_profit - d_exp)} ₪</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-box'><div class='metric-label'>صافي ربح الأسبوع</div><div class='metric-value'>{format_num(w_profit - w_exp)} ₪</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-box' style='border-right-color:#e67e22'><div class='metric-label'>رأس مال المخزن حالياً</div><div class='metric-value'>{format_num(cap_val)} ₪</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        t_capital, t_daily, t_cust = st.tabs(["💰 رأس مال الأقسام", "🗓️ تقارير الأيام", "👥 سجل الزبائن"])

        with t_capital:
            if not inv_df.empty:
                st.markdown("<div class='section-header'>توزيع رأس المال حسب الأقسام</div>", unsafe_allow_html=True)
                cat_cap = inv_df.assign(cap=inv_df['buy']*inv_df['qty']).groupby('cat')['cap'].sum().reset_index()
                c_cols = st.columns(len(cat_cap) if len(cat_cap) > 0 else 1)
                for i, row in cat_cap.iterrows():
                    with c_cols[i]: st.markdown(f"<div class='metric-box' style='border-color:#9b59b6'><div class='metric-label'>{row['cat']}</div><div class='metric-value'>{format_num(row['cap'])} ₪</div></div>", unsafe_allow_html=True)
            else: st.info("لا توجد بضاعة لحساب رأس مالها.")

        with t_daily:
            st.markdown("<div class='section-header'>ملخص مبيعات كل يوم</div>", unsafe_allow_html=True)
            days_map = {'Monday': 'الإثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء', 'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'}
            if not sales.empty:
                unique_days = sales[sales['date_dt'].dt.date >= start_week]['date_dt'].dt.date.unique()
                for d in unique_days:
                    d_name = days_map[pd.to_datetime(d).strftime('%A')]
                    with st.expander(f"تقرير يوم {d_name} - {d}"):
                        day_data = sales[sales['date_dt'].dt.date == d]
                        st.table(day_data.groupby('item').agg({'amount':'sum', 'profit':'sum'}).reset_index())

        with t_cust:
            st.markdown("<div class='section-header'>سجل مشتريات الزبائن</div>", unsafe_allow_html=True)
            cust_sales = sales[sales['customer_phone'] != ""].copy()
            if not cust_sales.empty:
                bills = cust_sales.groupby('bill_id').agg({'date':'first', 'customer_name':'first', 'amount':'sum'}).reset_index().sort_values('date', ascending=False)
                for _, row in bills.iterrows():
                    with st.expander(f"👤 {row['customer_name']} | 💰 {format_num(row['amount'])} ₪"):
                        st.table(cust_sales[cust_sales['bill_id'] == row['bill_id']][['item', 'amount', 'date']])
            else: st.info("لا يوجد زبائن مسجلين.")

    # --- 4. المصروفات والإعدادات (كما كانت) ---
    elif menu == "💸 المصروفات":
        st.markdown(f"<h1 class='main-title'>💸 مصروفات {active_branch}</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("البيان"); a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': active_branch}])], ignore_index=True)
                auto_save(); st.rerun()
        st.dataframe(st.session_state.expenses_df, use_container_width=True)

    elif menu == "⚙️ الإعدادات":
        if role != "أبو عمر (المدير العام)": st.error("للمدير فقط")
        else:
            st.markdown("<h1 class='main-title'>⚙️ إضافة أصناف للفروع</h1>", unsafe_allow_html=True)
            with st.form("add"):
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("اسم الصنف")
                br = c2.selectbox("لأي محل؟", BRANCHES)
                ct = c3.selectbox("القسم", st.session_state.categories)
                q = c1.number_input("الكمية", min_value=0.0)
                b = c2.number_input("سعر الشراء", min_value=0.0)
                s = c3.number_input("سعر البيع", min_value=0.0)
                if st.form_submit_button("إضافة للمحل"):
                    st.session_state.inventory.append({'item': n, 'branch': br, 'qty': q, 'buy': b, 'sell': s, 'cat': ct})
                    auto_save(); st.success("تم الإضافة"); st.rerun()
