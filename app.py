import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر للمحاسبة 2026", layout="wide", page_icon="🍏")

def تنسيق_رقم(قيمة):
    try:
        if قيمة == int(قيمة): return str(int(قيمة))
        return str(round(قيمة, 2))
    except: return str(قيمة)

def تنظيف_رقم(نص):
    try:
        if نص is None or نص == "": return 0.0
        return float(str(نص).replace(',', '.').replace('،', '.'))
    except: return 0.0

# 2. ملفات البيانات
الملفات = {
    'المبيعات': ('sales_v3.csv', ['التاريخ', 'الصنف', 'المبلغ', 'الربح', 'الطريقة', 'اسم_الزبون', 'هاتف_الزبون', 'رقم_الفاتورة']),
    'المصروفات': ('expenses_v3.csv', ['التاريخ', 'البيان', 'المبلغ']),
    'التالف': ('waste_v3.csv', ['التاريخ', 'الصنف', 'الكمية', 'قيمة_الخسارة']),
    'تسويات_الجرد': ('adjust_v3.csv', ['التاريخ', 'الصنف', 'الفارق_الوزني', 'الفارق_المالي'])
}

for key, (file, cols) in الملفات.items():
    state_key = f"data_{key}"
    if state_key not in st.session_state:
        if os.path.exists(file):
            df = pd.read_csv(file)
            st.session_state[state_key] = df
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv('inventory_v3.csv', index_col=0).to_dict('index') if os.path.exists('inventory_v3.csv') else {}
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_v3.csv')['name'].tolist() if os.path.exists('categories_v3.csv') else ["خضار وفواكه", "مكسرات"]

def حفظ_تلقائي():
    pd.DataFrame(st.session_state.inventory).T.to_csv('inventory_v3.csv')
    st.session_state.data_المبيعات.to_csv('sales_v3.csv', index=False)
    st.session_state.data_المصروفات.to_csv('expenses_v3.csv', index=False)
    st.session_state.data_التالف.to_csv('waste_v3.csv', index=False)
    st.session_state.data_تسويات_الجرد.to_csv('adjust_v3.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_v3.csv', index=False)

# 3. الواجهة والتنسيق
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .report-card { background-color: #f1f3f4; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.container():
        _, col_login, _ = st.columns([1,1,1])
        with col_login:
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("دخول"):
                if pwd == "123": st.session_state.logged_in = True; st.rerun()
                else: st.error("خطأ!")
else:
    st.sidebar.markdown("<h2 style='color:#27ae60; text-align:center;'>أهلاً أبو عمر</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المتقدمة", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
        if 'p_method' not in st.session_state: st.session_state.p_method = "نقداً"
        
        col_pay1, col_pay2 = st.columns([3,1])
        with col_pay2:
            st.session_state.p_method = st.radio("الدفع:", ["نقداً", "تطبيق"], horizontal=True)
        
        search_q = st.text_input("🔍 ابحث عن صنف...")
        cart = []
        for name, data in st.session_state.inventory.items():
            if search_q.lower() in name.lower():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{name}**")
                mode = c2.radio("بـ", ["₪", "كجم"], key=f"t_{name}", horizontal=True)
                val = تنظيف_رقم(c3.text_input("المقدار", key=f"v_{name}"))
                if val > 0:
                    qty = val if mode == "كجم" else val / data["بيع"]
                    cart.append({"name": name, "qty": qty, "amt": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"]-data["شراء"])*qty})
        
        if st.button("✅ تأكيد البيع"):
            if cart:
                bill_id = str(uuid.uuid4())
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                for item in cart:
                    st.session_state.inventory[item["name"]]["كمية"] -= item["qty"]
                    new_sale = {'التاريخ': now_str, 'الصنف': item['name'], 'المبلغ': item['amt'], 'الربح': item['profit'], 'الطريقة': st.session_state.p_method, 'اسم_الزبون': 'زبون عام', 'رقم_الفاتورة': bill_id}
                    st.session_state.data_المبيعات = pd.concat([st.session_state.data_المبيعات, pd.DataFrame([new_sale])], ignore_index=True)
                حفظ_تلقائي(); st.success("✅ تم حفظ العملية بنجاح"); st.rerun()

    # --- 4. التقارير المتقدمة ---
    elif menu == "📊 التقارير المتقدمة":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية والتحليلية</h1>", unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns([1, 2])
        period = col_f1.selectbox("اختر الفترة الزمنية:", ["اليوم", "آخر 7 أيام (أسبوعي)", "تاريخ مخصص"])
        
        start_d = datetime.now().date()
        end_d = datetime.now().date()
        
        if period == "آخر 7 أيام (أسبوعي)":
            start_d = datetime.now().date() - timedelta(days=7)
        elif period == "تاريخ مخصص":
            c_date1, c_date2 = col_f2.columns(2)
            start_d = c_date1.date_input("من تاريخ:", datetime.now().date() - timedelta(days=30))
            end_d = c_date2.date_input("إلى تاريخ:", datetime.now().date())

        def filter_df(df):
            if df.empty: return df
            df['temp_date'] = pd.to_datetime(df['التاريخ']).dt.date
            return df[(df['temp_date'] >= start_d) & (df['temp_date'] <= end_d)]

        sales_f = filter_df(st.session_state.data_المبيعات)
        exp_f = filter_df(st.session_state.data_المصروفات)
        waste_f = filter_df(st.session_state.data_التالف)
        adj_f = filter_df(st.session_state.data_تسويات_الجرد)

        net_profit = sales_f['الربح'].sum() - exp_f['المبلغ'].sum() - waste_f['قيمة_الخسارة'].sum() - adj_f['الفارق_المالي'].sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='report-card'><h3>المبيعات</h3><h2>{تنسيق_رقم(sales_f['المبلغ'].sum())} ₪</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h3>المصروفات</h3><h2>{تنسيق_رقم(exp_f['المبلغ'].sum())} ₪</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h3>العجز والتالف</h3><h2>{تنسيق_رقم(waste_f['قيمة_الخسارة'].sum() + adj_f['الفارق_المالي'].sum())} ₪</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div style='background-color:#27ae60; color:white;' class='report-card'><h3>الربح الصافي</h3><h2>{تنسيق_رقم(net_profit)} ₪</h2></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 تفاصيل الفواتير")
        if not sales_f.empty:
            bills = sales_f.groupby('رقم_الفاتورة').agg({'التاريخ':'first','اسم_الزبون':'first','الطريقة':'first','المبلغ':'sum','الربح':'sum'}).sort_values('التاريخ', ascending=False)
            st.table(bills.rename(columns={'التاريخ':'التاريخ والوقت','اسم_الزبون':'الزبون','الطريقة':'طريقة الدفع','المبلغ':'القيمة','الربح':'الربح'}))
