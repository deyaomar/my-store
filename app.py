import streamlit as st
import pandas as pd
import os

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

# دالة لتنظيف وتنسيق الأرقام
def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# --- نظام الإدارة المباشر للملفات ---
def get_db_path():
    return 'branches_config.csv'

def initialize_db():
    path = get_db_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])
        df.to_csv(path, index=False)
    return pd.read_csv(path)

# 2. تحميل البيانات الأساسية
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

# 3. التنسيق (ستايل أبو عمر الفخم)
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

# 4. بوابة الدخول (النظام المباشر)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_form"):
            u_input = st.text_input("👤 اسم المستخدم").strip()
            p_input = st.text_input("🔑 كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول النظام"):
                # التحقق المباشر من الملف (أقوى وسيلة لضمان رؤية المستخدمين الجدد)
                current_data = pd.read_csv(get_db_path())
                # تنظيف البيانات
                current_data['user_name'] = current_data['user_name'].astype(str).str.strip()
                current_data['password'] = current_data['password'].astype(str).str.strip()
                
                # فحص الأدمن (أبو عمر)
                if u_input == "أبو عمر" and p_input == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                
                # فحص الفروع
                match = current_data[(current_data['user_name'] == u_input) & (current_data['password'] == p_input)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "shop"
                    st.session_state.my_branch = match.iloc[0]['branch_name']
                    st.session_state.active_user = u_input
                    st.session_state.branches_db = current_data # تحديث الذاكرة
                    st.rerun()
                else:
                    st.error("❌ فشل الدخول. الحساب غير موجود في الملف حالياً.")
    st.stop()

# 5. القائمة الجانبية
if st.session_state.user_role == "admin":
    st.sidebar.markdown(f"<div style='background:#10b981; padding:20px; border-radius:15px; text-align:center; margin-bottom:20px;'>👑 <b>المدير العام</b><br>{st.session_state.active_user}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("📋 المهام الرئيسية", ["📊 التقارير المالية", "🏪 إدارة الفروع", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    # تحديث قائمة الفروع في السايد بار باستمرار
    st.session_state.branches_db = pd.read_csv(get_db_path())
    active_branch = st.sidebar.selectbox("🏠 عرض فرع محدد:", ["كافة الفروع"] + st.session_state.branches_db['branch_name'].tolist())
else:
    st.sidebar.markdown(f"<div style='background:#3b82f6; padding:20px; border-radius:15px; text-align:center; margin-bottom:20px;'>🏪 <b>فرع: {st.session_state.my_branch}</b></div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("📋 القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚨 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- صفحة إدارة الفروع ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة وتعديل الفروع</h1>", unsafe_allow_html=True)
    col_edit, col_list = st.columns([1, 1.5])
    
    with col_edit:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        t_add, t_edit, t_del = st.tabs(["➕ إضافة", "📝 تعديل", "❌ حذف"])
        
        with t_add:
            with st.form("add_form"):
                n = st.text_input("اسم المحل").strip()
                u = st.text_input("اسم المستخدم").strip()
                p = st.text_input("كلمة المرور").strip()
                if st.form_submit_button("حفظ واعتماد"):
                    if n and u and p:
                        df = pd.read_csv(get_db_path())
                        new_row = pd.DataFrame([{'branch_name': n, 'user_name': u, 'password': p}])
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_csv(get_db_path(), index=False)
                        st.success("✅ تم الحفظ في الملف بنجاح!")
                        st.rerun()
        
        with t_edit:
            # دائماً نقرأ من الملف للتعديل
            db_edit = pd.read_csv(get_db_path())
            target = st.selectbox("اختر للتعديل", db_edit['branch_name'].tolist())
            curr = db_edit[db_edit['branch_name'] == target].iloc[0]
            with st.form("edit_form"):
                en = st.text_input("الاسم الجديد", value=curr['branch_name'])
                eu = st.text_input("المستخدم الجديد", value=curr['user_name'])
                ep = st.text_input("كلمة المرور الجديدة", value=curr['password'])
                if st.form_submit_button("تحديث"):
                    db_edit.loc[db_edit['branch_name'] == target, ['branch_name', 'user_name', 'password']] = [en, eu, ep]
                    db_edit.to_csv(get_db_path(), index=False)
                    st.rerun()

    with col_list:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📋 حالة الملف الحالية")
        st.table(pd.read_csv(get_db_path()))
        st.markdown("</div>", unsafe_allow_html=True)

# بقية الأقسام (تقارير، توريد...)
elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
    st.info("التقارير المالية تعمل وتعتمد على بيانات المبيعات والمصاريف.")
