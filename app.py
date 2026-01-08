import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

# دالة قراءة الملفات لضمان جلب أحدث البيانات
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try: return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# تحميل الفروع بشكل مباشر من الملف لضمان عمل المستخدمين الجدد فوراً
def get_latest_branches():
    df = safe_read_csv('branches_config.csv', ['branch_name', 'user_name', 'password'])
    if df.empty:
        df = pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])
    return df

# تحديث بيانات الفروع في الـ session_state
st.session_state.branches_db = get_latest_branches()

def auto_save_branches():
    st.session_state.branches_db.to_csv('branches_config.csv', index=False)

# 2. التنسيق (نفس التصميم المطلوب)
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
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-right: 10px solid #10b981; }
    </style>
    """, unsafe_allow_html=True)

# 3. بوابة الدخول (تم إصلاحها لتقرأ المستخدمين الجدد)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("👤 اسم المستخدم").strip()
            p = st.text_input("🔑 كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول النظام"):
                # التأكد من أدمن النظام (أبو عمر)
                if u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                else:
                    # البحث في الفروع المضافة حديثاً
                    branches = get_latest_branches()
                    match = branches[(branches['user_name'] == u) & (branches['password'] == p)]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_role = "shop"
                        st.session_state.my_branch = match.iloc[0]['branch_name']
                        st.session_state.active_user = u
                        st.rerun()
                    else: st.error("❌ بيانات الدخول غير مسجلة أو خاطئة")
    st.stop()

# 4. القائمة الجانبية
if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("📋 المهام", ["🏪 إدارة الفروع", "📊 التقارير المالية"])
else:
    st.write(f"مرحباً بك في فرع: {st.session_state.my_branch}")
    if st.button("خروج"): st.session_state.clear(); st.rerun()
    st.stop()

# --- التركيز بالكامل على إدارة الفروع ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة وتعديل الفروع</h1>", unsafe_allow_html=True)
    
    col_edit, col_list = st.columns([1, 1.5])
    
    with col_edit:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        t_add, t_edit, t_del = st.tabs(["➕ إضافة فرع", "📝 تعديل", "❌ حذف"])
        
        with t_add:
            with st.form("add_branch_final"):
                new_bn = st.text_input("اسم المحل الجديد")
                new_un = st.text_input("اسم المستخدم للفرع")
                new_pn = st.text_input("كلمة المرور")
                if st.form_submit_button("اعتماد وحفظ"):
                    if new_bn and new_un and new_pn:
                        new_row = pd.DataFrame([{'branch_name': new_bn, 'user_name': new_un, 'password': new_pn}])
                        st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_row], ignore_index=True)
                        auto_save_branches()
                        st.success(f"✅ تم إنشاء فرع {new_bn} بنجاح. يمكنه الدخول الآن.")
                        st.rerun()
                    else: st.warning("الرجاء تعبئة كافة الحقول")

        with t_edit:
            if not st.session_state.branches_db.empty:
                branch_list = st.session_state.branches_db['branch_name'].tolist()
                target = st.selectbox("اختر الفرع لتعديله", branch_list)
                current_data = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].iloc[0]
                
                with st.form("edit_branch_form"):
                    edit_bn = st.text_input("الاسم", value=current_data['branch_name'])
                    edit_un = st.text_input("المستخدم", value=current_data['user_name'])
                    edit_pn = st.text_input("الكلمة", value=current_data['password'])
                    if st.form_submit_button("تحديث البيانات"):
                        idx = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].index
                        st.session_state.branches_db.loc[idx, ['branch_name', 'user_name', 'password']] = [edit_bn, edit_un, edit_pn]
                        auto_save_branches()
                        st.success("تم التحديث!")
                        st.rerun()

        with t_del:
            target_del = st.selectbox("اختر الفرع لحذفه نهائياً", st.session_state.branches_db['branch_name'].tolist(), key="del_box")
            if st.button("تأكيد الحذف"):
                st.session_state.branches_db = st.session_state.branches_db[st.session_state.branches_db['branch_name'] != target_del]
                auto_save_branches()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_list:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📋 كشف المستخدمين والفروع")
        # عرض الجدول بأسماء عربية
        display_df = st.session_state.branches_db.rename(columns={
            'branch_name': 'اسم الفرع',
            'user_name': 'اسم المستخدم',
            'password': 'كلمة المرور'
        })
        st.table(display_df)
        st.markdown("</div>", unsafe_allow_html=True)
