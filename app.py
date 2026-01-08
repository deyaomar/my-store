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

# 2. إدارة البيانات
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
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق الملكي (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-title { 
        color: #1e3a8a; text-align: center; font-weight: 900; font-size: 32px; 
        padding: 20px; background: white; border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px;
        border-bottom: 5px solid #10b981;
    }
    .metric-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-top: 5px solid #10b981;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام أبو عمر - تسجيل الدخول</h1>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 1.5, 1])
    with col_center:
        with st.form("login"):
            u = st.text_input("المستخدم").strip()
            p = st.text_input("كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول", use_container_width=True):
                if u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                else:
                    match = st.session_state.branches_db[(st.session_state.branches_db['user_name'] == u) & (st.session_state.branches_db['password'] == p)]
                    if not match.empty:
                        st.session_state.logged_in, st.session_state.user_role, st.session_state.my_branch, st.session_state.active_user = True, "shop", match.iloc[0]['branch_name'], u
                        st.rerun()
                    else: st.error("خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية
role = st.session_state.user_role
if role == "admin":
    st.sidebar.markdown(f"<div style='text-align:center; padding:15px; background:#10b981; color:white; border-radius:10px;'>👋 أهلاً أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", ["🏪 إدارة الفروع", "📊 التقارير المالية", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    active_branch = st.sidebar.selectbox("تصفية لفرع معين:", ["كافة الفروع"] + st.session_state.branches_db['branch_name'].tolist())
    if st.sidebar.button("🚨 تسجيل خروج"): st.session_state.clear(); st.rerun()
else:
    st.sidebar.title(f"فرع: {st.session_state.my_branch}")
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    active_branch = st.session_state.my_branch
    if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()

# --- 1. إدارة الفروع ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
    c_ops, c_view = st.columns([1, 1.5])
    with c_ops:
        tab_add, tab_edit, tab_del = st.tabs(["إضافة", "تعديل", "حذف"])
        with tab_add:
            with st.form("add_f"):
                bn = st.text_input("اسم الفرع")
                un = st.text_input("المستخدم")
                pn = st.text_input("الكلمة")
                if st.form_submit_button("حفظ"):
                    new_row = pd.DataFrame([{'branch_name':bn, 'user_name':un, 'password':pn}])
                    st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_row], ignore_index=True)
                    auto_save(); st.rerun()
        with tab_edit:
            if not st.session_state.branches_db.empty:
                target = st.selectbox("اختر الفرع", st.session_state.branches_db['branch_name'].tolist())
                curr = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].iloc[0]
                with st.form("edit_f"):
                    eb = st.text_input("الاسم", value=curr['branch_name'])
                    eu = st.text_input("المستخدم", value=curr['user_name'])
                    ep = st.text_input("الكلمة", value=curr['password'])
                    if st.form_submit_button("تعديل"):
                        idx = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].index
                        st.session_state.branches_db.loc[idx, ['branch_name', 'user_name', 'password']] = [eb, eu, ep]
                        auto_save(); st.rerun()
        with tab_del:
            target_d = st.selectbox("حذف فرع", st.session_state.branches_db['branch_name'].tolist(), key="del")
            if st.button("تأكيد الحذف النهائي"):
                st.session_state.branches_db = st.session_state.branches_db[st.session_state.branches_db['branch_name'] != target_d]
                auto_save(); st.rerun()
    with c_view:
        st.dataframe(st.session_state.branches_db, use_container_width=True)

# --- 2. التقارير المالية (تم الإصلاح) ---
elif menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
    
    sales = st.session_state.sales_df.copy()
    if active_branch != "كافة الفروع": sales = sales[sales['branch'] == active_branch]
    sales['date'] = pd.to_datetime(sales['date'])
    
    # فلترة مبيعات اليوم
    today_sales = sales[sales['date'].dt.date == datetime.now().date()]
    
    inv_df = pd.DataFrame(st.session_state.inventory)
    if active_branch != "كافة الفروع" and not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]
    stock_value = (inv_df['شراء'] * inv_df['كمية']).sum() if not inv_df.empty else 0

    # عرض البطاقات
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"<div class='metric-card'><h3>💰 مبيعات اليوم</h3><h2>{format_num(today_sales['amount'].sum())} ₪</h2></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='metric-card'><h3>📈 أرباح اليوم</h3><h2>{format_num(today_sales['profit'].sum())} ₪</h2></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='metric-card'><h3>📦 قيمة المخزن</h3><h2>{format_num(stock_value)} ₪</h2></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📑 كشف فواتير المبيعات")
    st.dataframe(sales.sort_values(by='date', ascending=False), use_container_width=True)

# --- 3. توريد بضاعة ---
elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد بضاعة</h1>", unsafe_allow_html=True)
    with st.form("supply"):
        c1, c2, c3 = st.columns(3)
        item = c1.text_input("الصنف")
        br = c2.selectbox("للفرع", st.session_state.branches_db['branch_name'].tolist())
        ct = c3.selectbox("القسم", st.session_state.categories)
        buy = c1.number_input("شراء", 0.0)
        sell = c2.number_input("بيع", 0.0)
        qty = c3.number_input("كمية", 0.0)
        if st.form_submit_button("إرسال للمخزن"):
            st.session_state.inventory.append({'item':item, 'branch':br, 'قسم':ct, 'شراء':buy, 'بيع':sell, 'كمية':qty})
            auto_save(); st.success("تم التوريد")

# --- 4. الإعدادات ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
    new_cat = st.text_input("أضف قسماً جديداً (مثل: مجمدات)")
    if st.button("إضافة"):
        st.session_state.categories.append(new_cat); auto_save(); st.rerun()
    st.write("الأقسام الحالية:", st.session_state.categories)
