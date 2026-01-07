import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="🍏")

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

# 2. إدارة البيانات
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
    </style>
    """, unsafe_allow_html=True)

# 4. النظام
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    st.sidebar.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])

    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة بيع البضاعة</h1>")
        # (بقية كود البيع الأصلي كما هو بدون تغيير)
        # ... [هنا يتم وضع كود البيع الأصلي] ...

    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية والتفصيلية</h1>", unsafe_allow_html=True)
        
        # تحويل التواريخ للمعالجة
        sales = st.session_state.sales_df.copy(); sales['date_dt'] = pd.to_datetime(sales['date'])
        exps = st.session_state.expenses_df.copy(); exps['date_dt'] = pd.to_datetime(exps['date'])
        wastes = st.session_state.waste_df.copy(); wastes['date_dt'] = pd.to_datetime(wastes['date'])
        adjs = st.session_state.adjust_df.copy(); adjs['date_dt'] = pd.to_datetime(adjs['date'])

        today = datetime.now().date()
        start_week = today - timedelta(days=today.weekday())

        # --- الجزء الأول: مبيعات اليوم والأسبوع ---
        c1, c2 = st.columns(2)
        day_total = sales[sales['date_dt'].dt.date == today]['amount'].sum()
        week_total = sales[sales['date_dt'].dt.date >= start_week]['amount'].sum()
        c1.metric("💰 مبيعات اليوم", f"{format_num(day_total)} ₪")
        c2.metric("📅 مبيعات الأسبوع", f"{format_num(week_total)} ₪")

        # --- الجزء الثاني: صافي ربح الأسبوع ---
        w_profit = sales[sales['date_dt'].dt.date >= start_week]['profit'].sum()
        w_exp = exps[exps['date_dt'].dt.date >= start_week]['amount'].sum()
        w_waste = wastes[wastes['date_dt'].dt.date >= start_week]['loss_value'].sum()
        w_adj = adjs[adjs['date_dt'].dt.date >= start_week]['loss_value'].sum()
        net_week = w_profit - w_exp - w_waste - w_adj
        st.subheader(f"📈 صافي ربح الأسبوع الحالي: {format_num(net_week)} ₪")
        
        st.divider()

        # --- الجزء الثالث: البحث بتاريخ محدد ---
        st.markdown("### 🔍 جرد يوم محدد")
        search_date = st.date_input("اختر اليوم:", today)
        day_sales = sales[sales['date_dt'].dt.date == search_date]
        day_p = day_sales['profit'].sum()
        day_a = day_sales['amount'].sum()
        st.write(f"في تاريخ {search_date}: المبيعات **{format_num(day_a)} ₪** | الأرباح الخام **{format_num(day_p)} ₪**")
        if not day_sales.empty:
            st.dataframe(day_sales[['item', 'amount', 'profit', 'method']], use_container_width=True)

        st.divider()

        # --- الجزء الرابع: تقرير الأسبوع المنفصل ---
        st.markdown("### 📋 تقرير الأسبوع الحالي (يومي)")
        week_report = sales[sales['date_dt'].dt.date >= start_week].copy()
        if not week_report.empty:
            week_report['اليوم'] = week_report['date_dt'].dt.date
            daily_summary = week_report.groupby('اليوم').agg({'amount': 'sum', 'profit': 'sum'}).reset_index()
            st.table(daily_summary.rename(columns={'amount': 'إجمالي المبيعات', 'profit': 'الأرباح'}))
        else:
            st.write("لا توجد مبيعات لهذا الأسبوع بعد.")

    # (بقية الأقسام: المخزن، المصروفات، الإعدادات تبقى كما هي تماماً)
