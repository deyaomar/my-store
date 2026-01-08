import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# دالة ذكية لقراءة الملفات وتجنب الأخطاء
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            df = pd.read_csv(file_path)
            # تنظيف البيانات من أي مسافات زائدة قد تسبب فشل الدخول
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
            return df
        except:
            return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# 2. تحميل البيانات الأولية في الذاكرة
if 'branches_db' not in st.session_state:
    db = safe_read_csv('branches_config.csv', ['branch_name', 'user_name', 'password'])
    if db.empty:
        db = pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])
    st.session_state.branches_db = db

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

# 3. التصميم الفخم (أبو عمر)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    .stApp { background-color: #f0f2f5; }
    .main-title { 
        background: linear-gradient(90deg, #1e3a8a, #10b981);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; font-weight: 900; font-size: 40px; padding: 20px;
    }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-right: 10px solid #10b981; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    .stSidebar [data-testid="stMarkdownContainer"] { color: white; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول (تم تقويتها بشكل كبير)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_form"):
            u_input = st.text_input("👤 اسم المستخدم").strip()
            p_input = st.text_input("🔑 كلمة المرور", type="password").strip()
            
            if st.form_submit_button("دخول النظام"):
                # 1. فحص المدير العام (أبو عمر)
                if u_input == "أبو عمر" and p_input == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                
                # 2. فحص الفروع (قراءة حيّة ومنظفة)
                live_db = safe_read_csv('branches_config.csv', ['branch_name', 'user_name', 'password'])
                
                # البحث عن مطابقة
                user_match = live_db[
                    (live_db['user_name'] == u_input) & 
                    (live_db['password'] == p_input)
                ]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "shop"
                    st.session_state.my_branch = user_match.iloc[0]['branch_name']
                    st.session_state.active_user = u_input
                    st.session_state.branches_db = live_db
                    st.rerun()
                else:
                    st.error("❌ البيانات غير صحيحة. تأكد من كتابة الاسم وكلمة السر كما أدخلتهما في لوحة الإدارة.")
    st.stop()

# 5. القائمة الجانبية
if st.session_state.user_role == "admin":
    st.sidebar.markdown(f"<div style='background:#10b981; padding:20px; border-radius:15px; text-align:center; margin-bottom:20px;'>👑 <b>المدير العام</b><br>{st.session_state.active_user}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("📋 المهام الرئيسية", ["📊 التقارير المالية", "🏪 إدارة الفروع", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    active_branch = st.sidebar.selectbox("🏠 عرض فرع محدد:", ["كافة الفروع"] + st.session_state.branches_db['branch_name'].tolist())
else:
    st.sidebar.markdown(f"<div style='background:#3b82f6; padding:20px; border-radius:15px; text-align:center; margin-bottom:20px;'>🏪 <b>فرع: {st.session_state.my_branch}</b></div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("📋 القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚨 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- قسم إدارة الفروع (للتأكد من الإضافة الصحيحة) ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة وتعديل الفروع</h1>", unsafe_allow_html=True)
    col_edit, col_list = st.columns([1, 1.5])
    with col_edit:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        t_add, t_edit, t_del = st.tabs(["➕ إضافة", "📝 تعديل", "❌ حذف"])
        with t_add:
            with st.form("add_f"):
                n = st.text_input("اسم المحل").strip()
                u = st.text_input("اسم المستخدم (للدخول)").strip()
                p = st.text_input("كلمة المرور").strip()
                if st.form_submit_button("اعتماد وحفظ"):
                    if n and u and p:
                        new_row = pd.DataFrame([{'branch_name':n, 'user_name':u, 'password':p}])
                        st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_row], ignore_index=True)
                        auto_save()
                        st.success(f"✅ تم إنشاء حساب {u} لفرع {n}")
                        st.rerun()
        with t_edit:
            if not st.session_state.branches_db.empty:
                target = st.selectbox("اختر فرع", st.session_state.branches_db['branch_name'].tolist())
                curr = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].iloc[0]
                with st.form("edit_f"):
                    en = st.text_input("الاسم", value=curr['branch_name']).strip()
                    eu = st.text_input("المستخدم", value=curr['user_name']).strip()
                    ep = st.text_input("الكلمة", value=curr['password']).strip()
                    if st.form_submit_button("تحديث"):
                        idx = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].index
                        st.session_state.branches_db.loc[idx, ['branch_name', 'user_name', 'password']] = [en, eu, ep]
                        auto_save(); st.success("تم التحديث"); st.rerun()
        with t_del:
            d_target = st.selectbox("حذف فرع", st.session_state.branches_db['branch_name'].tolist())
            if st.button("تأكيد الحذف"):
                st.session_state.branches_db = st.session_state.branches_db[st.session_state.branches_db['branch_name'] != d_target]
                auto_save(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_list:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.table(st.session_state.branches_db.rename(columns={'branch_name':'المحل','user_name':'المستخدم','password':'الكلمة'}))
        st.markdown("</div>", unsafe_allow_html=True)

# --- بقية الأقسام (التقارير، التوريد، الإعدادات) ---
elif menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية: {active_branch}</h1>", unsafe_allow_html=True)
    # ... (نفس كود التقارير السابق المعرب)
    st.write("استخدم الجداول أعلاه لمراجعة أداء الفروع.")

elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد بضاعة للمخزن</h1>", unsafe_allow_html=True)
    # ... (نفس كود التوريد السابق)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات العامة</h1>", unsafe_allow_html=True)
    # ... (نفس كود الإعدادات السابق)
