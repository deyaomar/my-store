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

# دالة قراءة الملفات بأمان لتجنب الأخطاء
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except:
            return pd.DataFrame(columns=default_cols)
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

# 3. التنسيق (CSS) الشامل
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-title { 
        color: #1e3a8a; text-align: center; font-weight: 900; font-size: 32px; 
        padding: 20px; background: white; border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px;
        border-bottom: 5px solid #10b981;
    }
    .branch-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-right: 5px solid #3b82f6;
        margin-bottom: 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #10b981 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول نظام أبو عمر المتكامل</h1>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 1.5, 1])
    with col_center:
        with st.form("login_form"):
            u_in = st.text_input("اسم المستخدم").strip()
            p_in = st.text_input("كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول النظام"):
                if u_in == "أبو عمر" and p_in == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                else:
                    db = st.session_state.branches_db
                    match = db[(db['user_name'] == u_in) & (db['password'] == p_in)]
                    if not match.empty:
                        st.session_state.logged_in, st.session_state.user_role, st.session_state.my_branch, st.session_state.active_user = True, "shop", match.iloc[0]['branch_name'], u_in
                        st.rerun()
                    else: st.error("بيانات خاطئة")
    st.stop()

# 5. القائمة الجانبية
role = st.session_state.user_role
if role == "admin":
    st.sidebar.markdown(f"<div style='text-align:center; padding:15px; background:#10b981; color:white; border-radius:10px;'>👋 أهلاً أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", ["🏪 إدارة الفروع", "📊 المراقبة الحية", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    active_branch_filter = st.sidebar.selectbox("تصفية البيانات لفرع:", ["كافة الفروع"] + st.session_state.branches_db['branch_name'].tolist())
    if st.sidebar.button("🚨 خروج"): st.session_state.clear(); st.rerun()
else:
    st.sidebar.title(f"فرع: {st.session_state.my_branch}")
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    active_branch_filter = st.session_state.my_branch
    if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()

# --- قسم إدارة الفروع (المحسن) ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 مركز التحكم في الفروع</h1>", unsafe_allow_html=True)
    col_ops, col_view = st.columns([1.2, 2])
    with col_ops:
        st.markdown("<div class='branch-card'>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["➕ إضافة", "📝 تعديل", "❌ حذف"])
        with t1:
            with st.form("add"):
                bn = st.text_input("اسم المحل")
                un = st.text_input("المستخدم")
                pn = st.text_input("الكلمة")
                if st.form_submit_button("حفظ"):
                    new_b = pd.DataFrame([{'branch_name':bn, 'user_name':un, 'password':pn}])
                    st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_b], ignore_index=True)
                    auto_save(); st.rerun()
        with t2:
            if not st.session_state.branches_db.empty:
                target = st.selectbox("فرع للتعديل", st.session_state.branches_db['branch_name'].tolist())
                curr = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].iloc[0]
                with st.form("edit"):
                    eb = st.text_input("الاسم", value=curr['branch_name'])
                    eu = st.text_input("المستخدم", value=curr['user_name'])
                    ep = st.text_input("الكلمة", value=curr['password'])
                    if st.form_submit_button("تعديل"):
                        idx = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].index
                        st.session_state.branches_db.loc[idx, ['branch_name', 'user_name', 'password']] = [eb, eu, ep]
                        auto_save(); st.rerun()
        with t3:
            target_del = st.selectbox("حذف فرع", st.session_state.branches_db['branch_name'].tolist())
            if st.button("تأكيد الحذف"):
                st.session_state.branches_db = st.session_state.branches_db[st.session_state.branches_db['branch_name'] != target_del]
                auto_save(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_view:
        st.markdown("<div class='branch-card'>", unsafe_allow_html=True)
        st.subheader("📋 الفروع المسجلة")
        st.dataframe(st.session_state.branches_db, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- قسم المراقبة الحية (إرجاع الميزات المفقودة) ---
elif menu == "📊 المراقبة الحية":
    st.markdown(f"<h1 class='main-title'>📊 مراقبة الأداء: {active_branch_filter}</h1>", unsafe_allow_html=True)
    sales = st.session_state.sales_df.copy()
    if active_branch_filter != "كافة الفروع": sales = sales[sales['branch'] == active_branch_filter]
    
    sales['date'] = pd.to_datetime(sales['date'])
    today_s = sales[sales['date'].dt.date == datetime.now().date()]
    
    inv_df = pd.DataFrame(st.session_state.inventory)
    if active_branch_filter != "كافة الفروع" and not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch_filter]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("مبيعات اليوم", f"{format_num(today_s['amount'].sum())} ₪")
    c2.metric("أرباح اليوم", f"{format_num(today_s['profit'].sum())} ₪")
    c3.metric("رأس مال البضاعة", f"{format_num((inv_df['شراء']*inv_df['كمية']).sum() if not inv_df.empty else 0)} ₪")

# --- قسم توريد البضاعة (إرجاع الميزات المفقودة) ---
elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد وتوزيع البضاعة</h1>", unsafe_allow_html=True)
    with st.form("supply_form"):
        c1, c2, c3 = st.columns(3)
        item_n = c1.text_input("اسم الصنف")
        target_b = c2.selectbox("إرسال إلى فرع", st.session_state.branches_db['branch_name'].tolist())
        item_cat = c3.selectbox("القسم", st.session_state.categories)
        b_price = c1.number_input("سعر الشراء", min_value=0.0)
        s_price = c2.number_input("سعر البيع", min_value=0.0)
        i_qty = c3.number_input("الكمية", min_value=0.0)
        if st.form_submit_button("تأكيد العملية"):
            st.session_state.inventory.append({'item':item_n, 'branch':target_b, 'قسم':item_cat, 'شراء':b_price, 'بيع':s_price, 'كمية':i_qty})
            auto_save(); st.success("تم التوريد!")

# --- قسم الإعدادات (الأقسام) ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إعدادات النظام</h1>", unsafe_allow_html=True)
    st.subheader("إدارة الأقسام (خضار، مسكرات، إلخ)")
    new_cat = st.text_input("أضف قسماً جديداً")
    if st.button("إضافة القسم"):
        if new_cat not in st.session_state.categories:
            st.session_state.categories.append(new_cat)
            auto_save(); st.rerun()
    st.write("الأقسام الحالية:", st.session_state.categories)

else:
    st.info("أهلاً بك يا أبو عمر.")
