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

# دالة قراءة الملفات المحصنة
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
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق العالمي الحديث (Advanced CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    .main-title { 
        background: linear-gradient(90deg, #1e3a8a, #10b981);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; font-weight: 900; font-size: 40px; 
        padding: 20px; margin-bottom: 20px;
    }
    .card {
        background: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        border-right: 10px solid #10b981; margin-bottom: 20px;
    }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    .stSidebar [data-testid="stMarkdownContainer"] { color: white; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3em;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white; font-weight: bold; border: none; transition: 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("👤 اسم المستخدم").strip()
            p = st.text_input("🔑 كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول النظام"):
                if u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                else:
                    match = st.session_state.branches_db[(st.session_state.branches_db['user_name'] == u) & (st.session_state.branches_db['password'] == p)]
                    if not match.empty:
                        st.session_state.logged_in, st.session_state.user_role, st.session_state.my_branch, st.session_state.active_user = True, "shop", match.iloc[0]['branch_name'], u
                        st.rerun()
                    else: st.error("❌ البيانات غير صحيحة")
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

# --- قسم 1: التقارير المالية (المطورة بطلب أبو عمر) ---
if menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية التفصيلية: {active_branch}</h1>", unsafe_allow_html=True)
    
    # تحضير البيانات المطلوبة
    sales_df = st.session_state.sales_df.copy()
    exp_df = st.session_state.expenses_df.copy()
    inv_df = pd.DataFrame(st.session_state.inventory)
    
    if active_branch != "كافة الفروع":
        sales_df = sales_df[sales_df['branch'] == active_branch]
        exp_df = exp_df[exp_df['branch'] == active_branch]
        if not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]

    # عرض البطاقات العلوية
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='card'><p style='color:grey'>إجمالي المبيعات</p><h2>{format_num(sales_df['amount'].sum())} ₪</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card' style='border-right-color:#3b82f6'><p style='color:grey'>صافي الأرباح</p><h2 style='color:#3b82f6'>{format_num(sales_df['profit'].sum() - exp_df['amount'].sum())} ₪</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='card' style='border-right-color:#f59e0b'><p style='color:grey'>قيمة المخزون</p><h2 style='color:#f59e0b'>{format_num((inv_df['شراء']*inv_df['كمية']).sum() if not inv_df.empty else 0)} ₪</h2></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='card' style='border-right-color:#ef4444'><p style='color:grey'>إجمالي المصاريف</p><h2 style='color:#ef4444'>{format_num(exp_df['amount'].sum())} ₪</h2></div>", unsafe_allow_html=True)

    # جداول تفصيلية (مثل صفحة الموظف)
    st.markdown("### 📄 الجداول والبيانات التفصيلية")
    tab_sales, tab_exp, tab_inv = st.tabs(["🛒 سجل المبيعات", "💸 سجل المصاريف", "📦 جرد بضاعة المحل"])
    
    with tab_sales:
        st.dataframe(sales_df.sort_values(by='date', ascending=False), use_container_width=True)
    with tab_exp:
        st.dataframe(exp_df.sort_values(by='date', ascending=False), use_container_width=True)
    with tab_inv:
        if not inv_df.empty:
            st.dataframe(inv_df, use_container_width=True)
        else:
            st.info("لا توجد بضاعة مسجلة في هذا القسم حالياً.")

# --- بقية الأقسام (إدارة الفروع، التوريد، الإعدادات) تظل كما هي في الكود الأساسي ---
elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة وتعديل الفروع</h1>", unsafe_allow_html=True)
    col_edit, col_list = st.columns([1, 1.5])
    with col_edit:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        t_add, t_edit, t_del = st.tabs(["➕ إضافة", "📝 تعديل", "❌ حذف"])
        with t_add:
            with st.form("add_f"):
                n = st.text_input("اسم المحل")
                u = st.text_input("اسم المستخدم")
                p = st.text_input("كلمة المرور")
                if st.form_submit_button("اعتماد الفرع الجديد"):
                    st.session_state.branches_db = pd.concat([st.session_state.branches_db, pd.DataFrame([{'branch_name':n, 'user_name':u, 'password':p}])], ignore_index=True)
                    auto_save(); st.success("تمت الإضافة!"); st.rerun()
        with t_edit:
            if not st.session_state.branches_db.empty:
                sel = st.selectbox("فرع للتعديل", st.session_state.branches_db['branch_name'].tolist())
                curr = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == sel].iloc[0]
                with st.form("edit_f"):
                    en = st.text_input("الاسم الجديد", value=curr['branch_name'])
                    eu = st.text_input("المستخدم الجديد", value=curr['user_name'])
                    ep = st.text_input("كلمة المرور الجديدة", value=curr['password'])
                    if st.form_submit_button("حفظ التعديلات"):
                        idx = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == sel].index
                        st.session_state.branches_db.loc[idx, ['branch_name', 'user_name', 'password']] = [en, eu, ep]
                        auto_save(); st.success("تم التعديل!"); st.rerun()
        with t_del:
            sel_d = st.selectbox("فرع للحذف", st.session_state.branches_db['branch_name'].tolist(), key="del")
            if st.button("تأكيد الحذف النهائي"):
                st.session_state.branches_db = st.session_state.branches_db[st.session_state.branches_db['branch_name'] != sel_d]
                auto_save(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_list:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📋 قائمة الفروع النشطة")
        st.table(st.session_state.branches_db)
        st.markdown("</div>", unsafe_allow_html=True)

elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد أصناف للمحلات</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        with st.form("supply"):
            c1, c2, c3 = st.columns(3)
            item = c1.text_input("اسم الصنف")
            br = c2.selectbox("المحل المستلم", st.session_state.branches_db['branch_name'].tolist())
            ct = c3.selectbox("القسم", st.session_state.categories)
            buy = c1.number_input("تكلفة الشراء", 0.0)
            sell = c2.number_input("سعر البيع", 0.0)
            qty = c3.number_input("الكمية الموردة", 0.0)
            if st.form_submit_button("تأكيد التوريد والترحيل"):
                st.session_state.inventory.append({'item':item, 'branch':br, 'قسم':ct, 'شراء':buy, 'بيع':sell, 'كمية':qty})
                auto_save(); st.success(f"تم توريد {item} لفرع {br}")
        st.markdown("</div>", unsafe_allow_html=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إعدادات النظام</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("إدارة الأقسام")
        new_c = st.text_input("إضافة قسم جديد")
        if st.button("حفظ القسم"):
            if new_c and new_c not in st.session_state.categories:
                st.session_state.categories.append(new_c); auto_save(); st.rerun()
        st.write("الأقسام الحالية:", st.session_state.categories)
        st.markdown("</div>", unsafe_allow_html=True)
