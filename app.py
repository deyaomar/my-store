import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try: return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# 2. تحميل البيانات
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = safe_read_csv('branches_config.csv', ['branch_name', 'user_name', 'password'])
    if st.session_state.branches_db.empty:
        st.session_state.branches_db = pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch', 'cat']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
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

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.branches_db.to_csv('branches_config.csv', index=False)

# 3. التنسيق (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    .stApp { background-color: #f8f9fa; }
    .main-title { 
        background: #1e3a8a; color: white; text-align: center; 
        font-weight: 900; padding: 20px; border-radius: 15px; margin-bottom: 25px;
    }
    .metric-card {
        background: white; padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #10b981;
        text-align: center; margin-bottom: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("المستخدم").strip()
            p = st.text_input("الكلمة", type="password").strip()
            if st.form_submit_button("دخول"):
                if u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                else:
                    db = st.session_state.branches_db
                    match = db[(db['user_name'] == u) & (db['password'] == p)]
                    if not match.empty:
                        st.session_state.logged_in, st.session_state.user_role, st.session_state.my_branch, st.session_state.active_user = True, "shop", match.iloc[0]['branch_name'], u
                        st.rerun()
                    else: st.error("بيانات خاطئة")
    st.stop()

# 5. القائمة الجانبية (ترتيب أبو عمر الجديد)
if st.session_state.user_role == "admin":
    st.sidebar.markdown(f"<div style='background:#1e3a8a; padding:15px; color:white; border-radius:10px; text-align:center;'>👑 المدير: {st.session_state.active_user}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", ["📊 التقارير المالية", "🏪 إدارة الفروع", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    active_branch = st.sidebar.selectbox("فلترة حسب المحل:", ["كافة المحلات"] + st.session_state.branches_db['branch_name'].tolist())
else:
    st.sidebar.title(f"فرع: {st.session_state.my_branch}")
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚨 خروج"): st.session_state.clear(); st.rerun()

# --- قسم التقارير المالية (نسخة مسؤول القسم المطورة للمدير) ---
if menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية التفصيلية - {active_branch}</h1>", unsafe_allow_html=True)
    
    # 1. تجهيز البيانات حسب الفلتر
    sales_df = st.session_state.sales_df.copy()
    exp_df = st.session_state.expenses_df.copy()
    inv_df = pd.DataFrame(st.session_state.inventory)
    
    if active_branch != "كافة المحلات":
        sales_df = sales_df[sales_df['branch'] == active_branch]
        exp_df = exp_df[exp_df['branch'] == active_branch]
        if not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]

    # 2. ملخص الأرقام (Cards)
    total_sales = sales_df['amount'].sum()
    total_profit = sales_df['profit'].sum()
    total_exp = exp_df['amount'].sum()
    net_capital = (inv_df['شراء'] * inv_df['كمية']).sum() if not inv_df.empty else 0
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'>🔹 المبيعات<br><h2>{format_num(total_sales)} ₪</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'>🔸 المصروفات<br><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'>📈 صافي الربح<br><h2>{format_num(total_profit - total_exp)} ₪</h2></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'>📦 قيمة المخزون<br><h2>{format_num(net_capital)} ₪</h2></div>", unsafe_allow_html=True)

    # 3. عرض الجداول التفصيلية (مثل صفحة الموظف تماماً)
    tab1, tab2, tab3 = st.tabs(["📄 كشف المبيعات", "💸 كشف المصروفات", "📦 جرد بضاعة المحل"])
    
    with tab1:
        st.subheader("سجل المبيعات التفصيلي")
        st.dataframe(sales_df.sort_values(by='date', ascending=False), use_container_width=True)
        
    with tab2:
        st.subheader("سجل المصروفات")
        st.dataframe(exp_df.sort_values(by='date', ascending=False), use_container_width=True)
        
    with tab3:
        st.subheader("البضاعة المتبقية في المستودع/المحل")
        if not inv_df.empty:
            st.dataframe(inv_df, use_container_width=True)
            st.info(f"إجمالي رأس المال المربوط في البضاعة حالياً: {format_num(net_capital)} ₪")
        else:
            st.warning("لا توجد بيانات بضاعة لهذا الفلتر.")

# --- بقية الأقسام ---
elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة وتعديل المحلات</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1.5])
    with col1:
        with st.form("branch_ops"):
            st.subheader("إضافة / تعديل")
            bn = st.text_input("اسم المحل")
            un = st.text_input("المستخدم")
            pn = st.text_input("الكلمة")
            if st.form_submit_button("حفظ البيانات"):
                new_b = pd.DataFrame([{'branch_name':bn, 'user_name':un, 'password':pn}])
                st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_b], ignore_index=True)
                auto_save(); st.rerun()
    with col2:
        st.dataframe(st.session_state.branches_db, use_container_width=True)

elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد بضاعة جديدة</h1>", unsafe_allow_html=True)
    with st.form("supply"):
        c1, c2, c3 = st.columns(3)
        item = c1.text_input("اسم الصنف")
        target_b = c2.selectbox("المحل المستلم", st.session_state.branches_db['branch_name'].tolist())
        cat = c3.selectbox("القسم", st.session_state.categories)
        buy = c1.number_input("تكلفة الشراء", 0.0)
        sell = c2.number_input("سعر البيع", 0.0)
        qty = c3.number_input("الكمية", 0.0)
        if st.form_submit_button("تأكيد العملية"):
            st.session_state.inventory.append({'item':item, 'branch':target_b, 'قسم':cat, 'شراء':buy, 'بيع':sell, 'كمية':qty})
            auto_save(); st.success("تم التوريد بنجاح")

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إعدادات الأقسام</h1>", unsafe_allow_html=True)
    nc = st.text_input("إضافة قسم جديد")
    if st.button("إضافة"):
        st.session_state.categories.append(nc); auto_save(); st.rerun()
    st.write("الأقسام الحالية:", st.session_state.categories)
