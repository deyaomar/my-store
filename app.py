import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل", layout="wide", page_icon="👑")

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

# 3. التنسيق الكلاسيكي (بدون تعقيد)
st.markdown("""
    <style>
    .main-title { color: #1e3a8a; text-align: center; font-weight: bold; font-size: 30px; border-bottom: 2px solid #10b981; padding-bottom: 10px; margin-bottom: 20px; }
    .stTabs [aria-selected="true"] { color: #10b981 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>دخول النظام</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("المستخدم")
        p = st.text_input("الكلمة", type="password")
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
                else: st.error("خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية (بترتيب أبو عمر المفضل)
if st.session_state.user_role == "admin":
    st.sidebar.title(f"المدير: {st.session_state.active_user}")
    menu = st.sidebar.radio("القائمة الرئيسية", ["📊 التقارير المالية", "🏪 إدارة الفروع", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    active_branch = st.sidebar.selectbox("تصفية حسب الفرع:", ["كافة المحلات"] + st.session_state.branches_db['branch_name'].tolist())
else:
    st.sidebar.title(f"فرع: {st.session_state.my_branch}")
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()

# --- قسم 1: التقارير المالية (بالتفصيل المطلوب) ---
if menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
    
    # تحضير البيانات
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    i_df = pd.DataFrame(st.session_state.inventory)
    
    if active_branch != "كافة المحلات":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]
        if not i_df.empty: i_df = i_df[i_df['branch'] == active_branch]

    # ملخص سريع
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي المبيعات", f"{format_num(s_df['amount'].sum())} ₪")
    c2.metric("إجمالي المصروفات", f"{format_num(e_df['amount'].sum())} ₪")
    c3.metric("صافي الربح", f"{format_num(s_df['profit'].sum() - e_df['amount'].sum())} ₪")
    c4.metric("قيمة البضاعة", f"{format_num((i_df['شراء'] * i_df['كمية']).sum() if not i_df.empty else 0)} ₪")

    st.markdown("---")
    # جداول تفصيلية مثل صفحة الموظف
    t1, t2, t3 = st.tabs(["📄 كشف المبيعات", "💸 كشف المصروفات", "📦 بضاعة المحل"])
    
    with t1:
        st.dataframe(s_df.sort_values(by='date', ascending=False), use_container_width=True)
    with t2:
        st.dataframe(e_df.sort_values(by='date', ascending=False), use_container_width=True)
    with t3:
        if not i_df.empty:
            st.dataframe(i_df, use_container_width=True)
        else:
            st.info("لا توجد بضاعة مسجلة")

# --- قسم 2: إدارة الفروع ---
elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>إدارة المحلات</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.subheader("إضافة / تعديل")
        with st.form("br_form"):
            bn = st.text_input("اسم المحل")
            un = st.text_input("المستخدم")
            pn = st.text_input("الكلمة")
            if st.form_submit_button("حفظ"):
                st.session_state.branches_db = pd.concat([st.session_state.branches_db, pd.DataFrame([{'branch_name':bn, 'user_name':un, 'password':pn}])], ignore_index=True)
                auto_save(); st.rerun()
    with col2:
        st.table(st.session_state.branches_db)

# --- قسم 3: توريد بضاعة ---
elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>توريد بضاعة</h1>", unsafe_allow_html=True)
    with st.form("sup"):
        c1, c2, c3 = st.columns(3)
        it = c1.text_input("الصنف")
        br = c2.selectbox("للمحل", st.session_state.branches_db['branch_name'].tolist())
        ct = c3.selectbox("القسم", st.session_state.categories)
        b = c1.number_input("شراء", 0.0)
        s = c2.number_input("بيع", 0.0)
        q = c3.number_input("كمية", 0.0)
        if st.form_submit_button("تأكيد"):
            st.session_state.inventory.append({'item':it, 'branch':br, 'قسم':ct, 'شراء':b, 'بيع':s, 'كمية':q})
            auto_save(); st.success("تم!")

# --- قسم 4: الإعدادات ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>الإعدادات</h1>", unsafe_allow_html=True)
    nc = st.text_input("إضافة قسم جديد")
    if st.button("إضافة"):
        st.session_state.categories.append(nc); auto_save(); st.rerun()
