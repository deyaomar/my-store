import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر - إدارة الفروع", layout="wide", page_icon="🏪")

def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# دالة قراءة الملفات بأمان
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# 2. إدارة البيانات
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = safe_read_csv('branches_config.csv', ['branch_name', 'user_name', 'password'])
    if st.session_state.branches_db.empty:
        st.session_state.branches_db = pd.DataFrame([{'branch_name': 'المحل الأول', 'user_name': 'user1', 'password': '123'}])

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

# 3. التنسيق (CSS) المطور خصيصاً لإدارة الفروع
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
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff; border-radius: 10px 10px 0 0;
        padding: 10px 20px; font-weight: bold; color: #4b5563;
    }
    .stTabs [aria-selected="true"] { background-color: #10b981 !important; color: white !important; }
    
    /* تحسين شكل المدخلات */
    .stTextInput input { border-radius: 10px !important; }
    .stButton button { width: 100%; border-radius: 10px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام أبو عمر - دخول</h1>", unsafe_allow_html=True)
    with st.container():
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
                        else: st.error("بيانات الدخول خاطئة")
    st.stop()

# 5. القائمة الجانبية
role = st.session_state.user_role
if role == "admin":
    st.sidebar.markdown(f"<div style='text-align:center; padding:15px; background:#10b981; color:white; border-radius:10px;'>👋 أهلاً أبو عمر<br><b>المدير العام</b></div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", ["🏪 إدارة الفروع", "📊 المراقبة الحية", "📦 توريد بضاعة"])
    if st.sidebar.button("🚨 تسجيل الخروج"):
        st.session_state.clear(); st.rerun()
else:
    st.sidebar.title(f"فرع: {st.session_state.my_branch}")
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    if st.sidebar.button("خروج"):
        st.session_state.clear(); st.rerun()

# --- تطوير صفحة إدارة الفروع حصرياً ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 مركز التحكم وإدارة الفروع</h1>", unsafe_allow_html=True)
    
    # الجزء العلوي: نظرة سريعة
    c1, c2, c3 = st.columns(3)
    num_branches = len(st.session_state.branches_db)
    c1.metric("إجمالي الفروع", f"{num_branches} فروع")
    c2.metric("الحالة", "متصل ✅")
    c3.metric("آخر تحديث", datetime.now().strftime("%H:%M"))

    st.markdown("---")

    # تقسيم الصفحة إلى قسمين: العمليات (يمين) وعرض الفروع (يسار)
    col_ops, col_view = st.columns([1.2, 2])

    with col_ops:
        st.markdown("<div class='branch-card'>", unsafe_allow_html=True)
        st.subheader("🛠️ العمليات")
        tab_add, tab_edit, tab_del = st.tabs(["➕ إضافة", "📝 تعديل", "❌ حذف"])
        
        with tab_add:
            with st.form("add_new"):
                b_name = st.text_input("اسم المحل الجديد")
                u_user = st.text_input("اسم مستخدم الموظف")
                p_pass = st.text_input("كلمة مرور الموظف")
                if st.form_submit_button("تفعيل الفرع"):
                    if b_name and u_user and p_pass:
                        if b_name in st.session_state.branches_db['branch_name'].values:
                            st.error("الاسم مستخدم مسبقاً")
                        else:
                            new_row = pd.DataFrame([{'branch_name':b_name, 'user_name':u_user, 'password':p_pass}])
                            st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_row], ignore_index=True)
                            auto_save(); st.success("تم الإضافة"); st.rerun()
        
        with tab_edit:
            if not st.session_state.branches_db.empty:
                target = st.selectbox("اختر الفرع للتعديل", st.session_state.branches_db['branch_name'].tolist())
                current = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].iloc[0]
                with st.form("edit_existing"):
                    new_b_name = st.text_input("تغيير الاسم", value=current['branch_name'])
                    new_u_user = st.text_input("تغيير المستخدم", value=current['user_name'])
                    new_p_pass = st.text_input("تغيير كلمة المرور", value=current['password'])
                    if st.form_submit_button("حفظ التغييرات"):
                        idx = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].index
                        st.session_state.branches_db.loc[idx, ['branch_name', 'user_name', 'password']] = [new_b_name, new_u_user, new_p_pass]
                        auto_save(); st.success("تم التعديل"); st.rerun()

        with tab_del:
            if not st.session_state.branches_db.empty:
                target_del = st.selectbox("فرع للحذف", st.session_state.branches_db['branch_name'].tolist(), key="del_box")
                st.error("❗ سيتم حذف كافة صلاحيات الدخول لهذا الفرع")
                if st.button("تأكيد حذف الفرع"):
                    st.session_state.branches_db = st.session_state.branches_db[st.session_state.branches_db['branch_name'] != target_del]
                    auto_save(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_view:
        st.markdown("<div class='branch-card'>", unsafe_allow_html=True)
        st.subheader("📋 قائمة الفروع والبيانات")
        
        # تحسين عرض الجدول
        styled_df = st.session_state.branches_db.copy()
        styled_df.columns = ["اسم الفرع", "اسم المستخدم", "كلمة المرور"]
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # تنبيه بسيط
        st.info("نصيحة: تأكد من إعطاء كلمات مرور مختلفة لكل فرع لضمان الأمان.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- بقية الأقسام (بدون تغيير في المحتوى حالياً) ---
elif menu == "📊 المراقبة الحية":
    st.markdown("<h1 class='main-title'>📊 المراقبة الحية</h1>", unsafe_allow_html=True)
elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد بضاعة</h1>", unsafe_allow_html=True)
