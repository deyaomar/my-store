import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
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

# 2. إدارة ملفات البيانات
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        if os.path.exists(file):
            df = pd.read_csv(file)
            for c in cols: 
                if c not in df.columns: df[c] = 0.0 if 'amount' in c or 'profit' in c or 'loss' in c or 'qty' in c else ""
            st.session_state[state_key] = df
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv('inventory_final.csv', index_col=0).to_dict('index') if os.path.exists('inventory_final.csv') else {}
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

# حالات التشغيل
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv('inventory_final.csv')
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. واجهة المستخدم
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 900; font-size: 20px; padding: 10px; border-radius: 5px; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 26px; text-align: center; margin-bottom: 25px; border-bottom: 3px solid #27ae60; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; border-radius: 10px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-label { font-size: 15px; color: #7f8c8d; font-weight: bold; }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    .capital-box { border-right-color: #e67e22; background-color: #fff9f4; }
    .section-header { background: #f1f4f6; padding: 10px; border-radius: 10px; color: #2c3e50; font-weight: 900; margin: 15px 0; border-right: 5px solid #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    st.sidebar.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج آمن"):
        st.session_state.clear(); st.rerun()

    # --- 1. نقطة البيع (بدون تعديل) ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة بيع البضاعة</h1>", unsafe_allow_html=True)
        if st.session_state.show_cust_fields:
            with st.status("✅ تم حفظ الفاتورة!"):
                c_n = st.text_input("اسم الزبون")
                c_p = st.text_input("رقم الهاتف")
                if st.button("💾 حفظ وربط"):
                    mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                    st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                    auto_save(); st.session_state.show_cust_fields = False; st.rerun()
                if st.button("⏩ تخطي"): st.session_state.show_cust_fields = False; st.rerun()
        else:
            st.session_state.p_method = st.radio("طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
            search_q = st.text_input("🔍 ابحث عن صنف...")
            bill_items = []
            for cat in st.session_state.categories:
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                if search_q: items = {k: v for k, v in items.items() if search_q in k}
                if items:
                    with st.expander(f"📂 {cat}", expanded=True):
                        for item, data in items.items():
                            c1, c2, c3 = st.columns([2, 1, 2])
                            c1.markdown(f"**{item}**\n<small>متوفر: {format_num(data['كمية'])}</small>", unsafe_allow_html=True)
                            mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item}", horizontal=True)
                            val = clean_num(c3.text_input("المقدار", key=f"v_{item}"))
                            if val > 0:
                                qty = val if mode == "كجم" else val / data["بيع"]
                                bill_items.append({"item": item, "qty": qty, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * qty})
            if st.button("🚀 إتمام البيع", type="primary"):
                if bill_items:
                    b_id = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save(); st.session_state.show_cust_fields = True; st.rerun()

    # --- 2. المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        t_list, t_jard, t_waste = st.tabs(["📋 الرصيد", "⚖️ الجرد", "🗑️ التالف"])
        with t_list: st.dataframe(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية": v['كمية']} for k, v in st.session_state.inventory.items()]), use_container_width=True)
        with t_jard:
            new_counts = {}
            for item, data in st.session_state.inventory.items():
                c1, c2, c3 = st.columns([2, 1, 2])
                c1.write(f"**{item}**")
                res = c3.text_input("الوزن الحقيقي", key=f"j_{item}")
                if res != "": new_counts[item] = clean_num(res)
            if st.button("✔️ اعتماد الجرد"):
                for it, rq in new_counts.items():
                    diff = st.session_state.inventory[it]['كمية'] - rq
                    st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': it, 'diff_qty': diff, 'loss_value': diff * st.session_state.inventory[it]['شراء']}])], ignore_index=True)
                    st.session_state.inventory[it]['كمية'] = rq
                auto_save(); st.rerun()

    # --- 3. التقارير المالية (التعديلات المطلوبة) ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية ورأس المال</h1>", unsafe_allow_html=True)
        
        # تحضير البيانات
        sales = st.session_state.sales_df.copy(); sales['date_dt'] = pd.to_datetime(sales['date'])
        exps = st.session_state.expenses_df.copy(); exps['date_dt'] = pd.to_datetime(exps['date'])
        wastes = st.session_state.waste_df.copy(); wastes['date_dt'] = pd.to_datetime(wastes['date'])
        adjs = st.session_state.adjust_df.copy(); adjs['date_dt'] = pd.to_datetime(adjs['date'])

        today = datetime.now().date()
        start_week = today - timedelta(days=(today.weekday() + 2) % 7)

        # حساب صافي اليوم
        d_sales = sales[sales['date_dt'].dt.date == today]
        d_exps = exps[exps['date_dt'].dt.date == today]['amount'].sum()
        d_loss = wastes[wastes['date_dt'].dt.date == today]['loss_value'].sum() + adjs[adjs['date_dt'].dt.date == today]['loss_value'].sum()
        d_net = d_sales['profit'].sum() - d_exps - d_loss

        # حساب صافي الأسبوع
        w_sales = sales[sales['date_dt'].dt.date >= start_week]
        w_exps = exps[exps['date_dt'].dt.date >= start_week]['amount'].sum()
        w_loss = wastes[wastes['date_dt'].dt.date >= start_week]['loss_value'].sum() + adjs[adjs['date_dt'].dt.date >= start_week]['loss_value'].sum()
        w_net = w_sales['profit'].sum() - w_exps - w_loss

        # حساب رأس المال الحالي من المخزن
        inv_df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index()
        inv_df.columns = ['item', 'قسم', 'شراء', 'بيع', 'كمية']
        inv_df['total_capital'] = inv_df['شراء'] * inv_df['كمية']
        total_market_capital = inv_df['total_capital'].sum()

        # عرض الكروت العلوية (الأرباح ورأس المال)
        row1 = st.columns(4)
        row1[0].markdown(f"<div class='metric-box'><div class='metric-label'>صافي ربح اليوم</div><div class='metric-value'>{format_num(d_net)} ₪</div></div>", unsafe_allow_html=True)
        row1[1].markdown(f"<div class='metric-box'><div class='metric-label'>صافي ربح الأسبوع</div><div class='metric-value'>{format_num(w_net)} ₪</div></div>", unsafe_allow_html=True)
        row1[2].markdown(f"<div class='metric-box capital-box'><div class='metric-label'>إجمالي رأس المال بالمخزن</div><div class='metric-value'>{format_num(total_market_capital)} ₪</div></div>", unsafe_allow_html=True)
        row1[3].markdown(f"<div class='metric-box capital-box'><div class='metric-label'>مبيعات الأسبوع (خام)</div><div class='metric-value'>{format_num(w_sales['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        t_capital, t_daily, t_cust = st.tabs(["💰 رأس مال الأقسام", "📈 التقارير اليومية", "👥 سجل الزبائن"])

        with t_capital:
            st.markdown("<div class='section-header'>تفصيل رأس مال كل قسم على حدة</div>", unsafe_allow_html=True)
            cat_cap = inv_df.groupby('قسم')['total_capital'].sum().reset_index()
            c_cols = st.columns(len(cat_cap))
            for i, row in cat_cap.iterrows():
                with c_cols[i]:
                    st.markdown(f"<div class='metric-box' style='border-right-color: #9b59b6;'><div class='metric-label'>رأس مال {row['قسم']}</div><div class='metric-value'>{format_num(row['total_capital'])} ₪</div></div>", unsafe_allow_html=True)
            
            st.markdown("#### 📋 جرد تفصيلي لرأس المال لكل صنف")
            for cat in st.session_state.categories:
                with st.expander(f"تفاصيل بضاعة قسم: {cat}"):
                    cat_data = inv_df[inv_df['قسم'] == cat][['item', 'كمية', 'شراء', 'total_capital']]
                    st.table(cat_data.rename(columns={'item':'الصنف', 'كمية':'الكمية المتوفرة', 'شراء':'سعر التكلفة', 'total_capital':'قيمة رأس المال'}))

        with t_daily:
            st.markdown("<div class='section-header'>الأداء اليومي المفصل</div>", unsafe_allow_html=True)
            days_map = {'Monday': 'الإثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء', 'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'}
            week_days = sales[sales['date_dt'].dt.date >= start_week].sort_values('date_dt', ascending=False)
            for d in week_days['date_dt'].dt.date.unique():
                d_name = days_map[pd.to_datetime(d).strftime('%A')]
                with st.expander(f"تقرير يوم {d_name} - {d}"):
                    d_data = sales[sales['date_dt'].dt.date == d]
                    st.write(f"**إجمالي المبيعات:** {format_num(d_data['amount'].sum())} ₪")
                    st.table(d_data.groupby('item').agg({'amount':'sum', 'profit':'sum'}).reset_index())

        with t_cust:
            st.markdown("<div class='section-header'>سجل الزبائن (تطبيق)</div>", unsafe_allow_html=True)
            cust_sales = sales[sales['customer_name'] != 'زبون عام'].copy()
            bills = cust_sales.groupby('bill_id').agg({'date':'first', 'customer_name':'first', 'amount':'sum'}).reset_index().sort_values('date', ascending=False)
            for _, row in bills.iterrows():
                with st.expander(f"👤 {row['customer_name']} | {format_num(row['amount'])} ₪"):
                    st.table(cust_sales[cust_sales['bill_id'] == row['bill_id']][['item', 'amount']])

    # --- 4. المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp_f"):
            r = st.text_input("البيان"); a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                auto_save(); st.rerun()
        st.dataframe(st.session_state.expenses_df.sort_index(ascending=False), use_container_width=True)

    # --- 5. الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
        with st.form("add_i"):
            n = st.text_input("الصنف"); cat = st.selectbox("القسم", st.session_state.categories)
            b = st.text_input("شراء"); s = st.text_input("بيع"); q = st.text_input("الكمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.rerun()
