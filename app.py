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

# دالة قراءة أحدث بيانات الفروع لضمان تسجيل الدخول الفوري
def get_latest_branches():
    file_path = 'branches_config.csv'
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try: return pd.read_csv(file_path)
        except: pass
    return pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])

# 2. تحميل وإدارة البيانات (Session State)
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = get_latest_branches()

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch', 'cat']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        if os.path.exists(file) and os.path.getsize(file) > 0:
            st.session_state[state_key] = pd.read_csv(file)
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    if os.path.exists('inventory_final.csv') and os.path.getsize('inventory_final.csv') > 0:
        st.session_state.inventory = pd.read_csv('inventory_final.csv').to_dict('records')
    else:
        st.session_state.inventory = []

if 'categories' not in st.session_state:
    if os.path.exists('categories_final.csv'):
        st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist()
    else:
        st.session_state.categories = ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.branches_db.to_csv('branches_config.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق العالمي (CSS) - التصميم الذي اعتمدته
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    .stApp { background-color: #f0f2f5; }
    .main-title { 
        background: linear-gradient(90deg, #1e3a8a, #10b981);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; font-weight: 900; font-size: 40px; padding: 20px; margin-bottom: 20px;
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
                    # جلب أحدث البيانات من الملف مباشرة عند محاولة الدخول
                    current_branches = get_latest_branches()
                    match = current_branches[(current_branches['user_name'] == u) & (current_branches['password'] == p)]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_role = "shop"
                        st.session_state.my_branch = match.iloc[0]['branch_name']
                        st.session_state.active_user = u
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

# --- قسم 1: التقارير المالية ---
if menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية: {active_branch}</h1>", unsafe_allow_html=True)
    
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    inv_df = pd.DataFrame(st.session_state.inventory)
    
    if active_branch != "كافة الفروع":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]
        if not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='card'><p style='color:grey'>إجمالي المبيعات</p><h2>{format_num(s_df['amount'].sum())} ₪</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card' style='border-right-color:#3b82f6'><p style='color:grey'>صافي الأرباح</p><h2 style='color:#3b82f6'>{format_num(s_df['profit'].sum() - e_df['amount'].sum())} ₪</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='card' style='border-right-color:#f59e0b'><p style='color:grey'>قيمة المخزون</p><h2 style='color:#f59e0b'>{format_num((inv_df['شراء']*inv_df['كمية']).sum() if not inv_df.empty else 0)} ₪</h2></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='card' style='border-right-color:#ef4444'><p style='color:grey'>إجمالي المصاريف</p><h2 style='color:#ef4444'>{format_num(e_df['amount'].sum())} ₪</h2></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🛒 المبيعات", "💸 المصاريف", "📦 جرد المخزن"])
    with tab1:
        st.dataframe(s_df.rename(columns={'date':'التاريخ','item':'الصنف','amount':'المبلغ','profit':'الربح','branch':'المحل'}).sort_values(by='التاريخ', ascending=False), use_container_width=True)
    with tab2:
        st.dataframe(e_df.rename(columns={'date':'التاريخ','reason':'السبب','amount':'المبلغ','branch':'المحل'}).sort_values(by='التاريخ', ascending=False), use_container_width=True)
    with tab3:
        if not inv_df.empty:
            st.dataframe(inv_df.rename(columns={'item':'الصنف','branch':'المحل','قسم':'القسم','شراء':'الشراء','بيع':'البيع','كمية':'الكمية'}), use_container_width=True)

# --- قسم 2: إدارة الفروع ---
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
                if st.form_submit_button("اعتماد وحفظ"):
                    new_row = pd.DataFrame([{'branch_name':n, 'user_name':u, 'password':p}])
                    st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_row], ignore_index=True)
                    auto_save(); st.success("✅ تم الحفظ بنجاح!"); st.rerun()
        with t_edit:
            if not st.session_state.branches_db.empty:
                target = st.selectbox("اختر الفرع", st.session_state.branches_db['branch_name'].tolist())
                curr = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].iloc[0]
                with st.form("edit_f"):
                    en = st.text_input("الاسم", value=curr['branch_name'])
                    eu = st.text_input("المستخدم", value=curr['user_name'])
                    ep = st.text_input("الكلمة", value=curr['password'])
                    if st.form_submit_button("تحديث"):
                        idx = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].index
                        st.session_state.branches_db.loc[idx, ['branch_name', 'user_name', 'password']] = [en, eu, ep]
                        auto_save(); st.success("تم التحديث"); st.rerun()
        with t_del:
            d_target = st.selectbox("حذف فرع", st.session_state.branches_db['branch_name'].tolist())
            if st.button("تأكيد الحذف النهائي"):
                st.session_state.branches_db = st.session_state.branches_db[st.session_state.branches_db['branch_name'] != d_target]
                auto_save(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_list:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.table(st.session_state.branches_db.rename(columns={'branch_name':'المحل','user_name':'المستخدم','password':'الكلمة'}))
        st.markdown("</div>", unsafe_allow_html=True)

# --- قسم 3: توريد بضاعة ---
elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد أصناف للمحلات</h1>", unsafe_allow_html=True)
    with st.markdown("<div class='card'>", unsafe_allow_html=True):
        with st.form("supply"):
            c1, c2, c3 = st.columns(3)
            item = c1.text_input("اسم الصنف")
            br = c2.selectbox("المحل المستلم", st.session_state.branches_db['branch_name'].tolist())
            ct = c3.selectbox("القسم", st.session_state.categories)
            buy = c1.number_input("تكلفة الشراء", 0.0); sell = c2.number_input("سعر البيع", 0.0); qty = c3.number_input("الكمية", 0.0)
            if st.form_submit_button("ترحيل للمخزن"):
                st.session_state.inventory.append({'item':item, 'branch':br, 'قسم':ct, 'شراء':buy, 'بيع':sell, 'كمية':qty})
                auto_save(); st.success("تم التوريد بنجاح")

# --- قسم 4: الإعدادات ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات العامة</h1>", unsafe_allow_html=True)
    with st.markdown("<div class='card'>", unsafe_allow_html=True):
        new_c = st.text_input("إضافة قسم بضاعة جديد")
        if st.button("حفظ القسم"):
            if new_c and new_c not in st.session_state.categories:
                st.session_state.categories.append(new_c); auto_save(); st.rerun()
        st.write("الأقسام الحالية:", st.session_state.categories)
