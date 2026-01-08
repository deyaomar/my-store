import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# دالة ذكية لقراءة الملفات بأمان لتجنب خطأ EmptyDataError
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# 2. إدارة البيانات (المحسنة ضد أخطاء الملفات الفارغة)
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

# 3. التنسيق (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    [data-testid="stSidebar"] { background-color: #0e1117 !important; color: white; }
    .main-title { color: #1e3a8a; text-align: center; font-weight: 900; font-size: 35px; border-bottom: 3px solid #10b981; padding-bottom: 15px; margin-bottom: 30px; }
    .admin-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border-right: 8px solid #10b981; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول (يدعم Enter والماوس)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول النظام</h1>", unsafe_allow_html=True)
    with st.container():
        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            with st.form("login_form"):
                u_in = st.text_input("اسم المستخدم").strip()
                p_in = st.text_input("كلمة المرور", type="password").strip()
                if st.form_submit_button("دخول", use_container_width=True):
                    if u_in == "أبو عمر" and p_in == "admin":
                        st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                        st.rerun()
                    else:
                        db = st.session_state.branches_db
                        match = db[(db['user_name'] == u_in) & (db['password'] == p_in)]
                        if not match.empty:
                            st.session_state.logged_in, st.session_state.user_role, st.session_state.my_branch, st.session_state.active_user = True, "shop", match.iloc[0]['branch_name'], u_in
                            st.rerun()
                        else: st.error("خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية
role = st.session_state.user_role
if role == "admin":
    st.sidebar.markdown(f"<div style='text-align:center; padding:20px; background:#10b981; border-radius:10px; margin-bottom:20px;'>👑 المدير العام<br><b>{st.session_state.active_user}</b></div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("التحكم الرئيسي", ["📊 المراقبة الحية", "🏪 إدارة الفروع", "📦 توريد بضاعة", "📑 التقارير الختامية"])
    if st.sidebar.button("🚨 خروج"):
        st.session_state.clear()
        st.rerun()
else:
    st.sidebar.title(f"فرع: {st.session_state.my_branch}")
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    if st.sidebar.button("خروج"):
        st.session_state.clear()
        st.rerun()

# --- قسم إدارة الفروع المتطور ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 مركز التحكم في الفروع</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ إضافة فرع", "📝 تعديل فرع", "❌ حذف فرع"])
    
    with tab1:
        st.subheader("إضافة فرع جديد للنظام")
        with st.form("add_branch_form"):
            new_b = st.text_input("اسم المحل الجديد")
            new_u = st.text_input("اسم المستخدم للموظف")
            new_p = st.text_input("كلمة مرور الموظف")
            if st.form_submit_button("إضافة الفرع"):
                if new_b and new_u and new_p:
                    if new_b in st.session_state.branches_db['branch_name'].values:
                        st.error("هذا الفرع موجود مسبقاً!")
                    else:
                        new_data = pd.DataFrame([{'branch_name':new_b, 'user_name':new_u, 'password':new_p}])
                        st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_data], ignore_index=True)
                        auto_save()
                        st.success(f"تم إضافة فرع {new_b} بنجاح!")
                        st.rerun()
                else: st.warning("يرجى ملء جميع الحقول")

    with tab2:
        st.subheader("تعديل بيانات فرع حالي")
        if not st.session_state.branches_db.empty:
            branch_to_edit = st.selectbox("اختر الفرع المراد تعديله:", st.session_state.branches_db['branch_name'].tolist())
            current_data = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == branch_to_edit].iloc[0]
            with st.form("edit_branch_form"):
                edit_b = st.text_input("اسم المحل", value=current_data['branch_name'])
                edit_u = st.text_input("اسم المستخدم", value=current_data['user_name'])
                edit_p = st.text_input("كلمة المرور", value=current_data['password'])
                if st.form_submit_button("حفظ التعديلات"):
                    idx = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == branch_to_edit].index
                    st.session_state.branches_db.loc[idx, ['branch_name', 'user_name', 'password']] = [edit_b, edit_u, edit_p]
                    auto_save()
                    st.success("تم تحديث البيانات بنجاح")
                    st.rerun()
        else: st.info("لا يوجد فروع مسجلة")

    with tab3:
        st.subheader("حذف فرع من النظام")
        if not st.session_state.branches_db.empty:
            branch_to_del = st.selectbox("اختر الفرع المراد حذفه نهائياً:", st.session_state.branches_db['branch_name'].tolist(), key="del_select")
            st.warning(f"انتبه يا أبو عمر! حذف فرع '{branch_to_del}' سيزيله من قائمة الدخول.")
            if st.button("تأكيد الحذف النهائي"):
                st.session_state.branches_db = st.session_state.branches_db[st.session_state.branches_db['branch_name'] != branch_to_del]
                auto_save()
                st.error(f"تم حذف فرع {branch_to_del} من النظام")
                st.rerun()
        else: st.info("لا يوجد فروع لحذفها")

    st.markdown("---")
    st.subheader("📋 قائمة الفروع الحالية")
    st.dataframe(st.session_state.branches_db, use_container_width=True)

# --- باقي الأقسام ---
elif menu == "📊 المراقبة الحية":
    st.markdown("<h1 class='main-title'>📊 المراقبة الحية</h1>", unsafe_allow_html=True)
    st.info("هنا تظهر إحصائيات الفروع الحالية.")

elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد بضاعة للمخازن</h1>", unsafe_allow_html=True)
    with st.form("inventory_form"):
        c1, c2, c3 = st.columns(3)
        item = c1.text_input("اسم الصنف")
        branch_list = st.session_state.branches_db['branch_name'].tolist() if not st.session_state.branches_db.empty else []
        branch = c2.selectbox("توجيه إلى فرع:", branch_list)
        cat = c3.selectbox("القسم:", st.session_state.categories)
        buy = c1.number_input("سعر التكلفة", min_value=0.0)
        sell = c2.number_input("سعر البيع", min_value=0.0)
        qty = c3.number_input("الكمية الموردة", min_value=0.0)
        if st.form_submit_button("تأكيد التوريد"):
            st.session_state.inventory.append({'item':item, 'branch':branch, 'قسم':cat, 'شراء':buy, 'بيع':sell, 'كمية':qty})
            auto_save()
            st.success("تمت الإضافة بنجاح")

else:
    st.info("أهلاً بك يا أبو عمر في نظامك.")
