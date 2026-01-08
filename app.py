import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

# دالات التنسيق والتنظيف
def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

# دالة القراءة الآمنة
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try: return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# --- نظام تسجيل الدخول (الحل النهائي والمضمون) ---
def get_db_path(): return 'branches_config.csv'

def initialize_auth():
    path = get_db_path()
    # البيانات الأساسية التي لا تتغير
    admin_data = {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'}
    shop_data = {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
    
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame([admin_data, shop_data])
        df.to_csv(path, index=False, encoding='utf-8-sig')
    
    # القراءة مع معالجة الترميز لضمان قراءة "أبو عمر" بشكل صحيح
    try:
        return pd.read_csv(path, encoding='utf-8-sig')
    except:
        return pd.DataFrame([admin_data, shop_data])

# 2. تحميل البيانات
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_auth()

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        st.session_state[state_key] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية', 'سعر_القطعة'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + (cat_df['name'].tolist() if not cat_df.empty else ["مواد غذائية"])))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; direction: rtl; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-left: 3px solid #10b981; }
    .sidebar-user { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white !important; font-weight: 900; font-size: 22px; text-align: center; padding: 20px; border-radius: 15px; margin: 10px; }
    .item-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-right: 6px solid #10b981; margin-bottom: 15px; }
    .main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة تسجيل الدخول (التعديل الجذري هنا)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        u_input = st.text_input("👤 اسم المستخدم (أبو عمر)").strip()
        p_input = st.text_input("🔑 كلمة المرور", type="password").strip()
        
        if st.form_submit_button("دخول"):
            # التحقق المباشر كخيار أول لضمان تخطي أي خطأ في الملفات
            if u_input == "أبو عمر" and p_input == "admin":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.active_user = "أبو عمر"
                st.session_state.my_branch = "المدير العام"
                st.rerun()
            elif u_input == "admin" and p_input == "123":
                st.session_state.logged_in = True
                st.session_state.user_role = "shop"
                st.session_state.active_user = "admin"
                st.session_state.my_branch = "المحل الرئيسي"
                st.rerun()
            else:
                # التحقق من قاعدة البيانات للفروع الأخرى
                db = initialize_auth()
                m = db[(db['user_name'] == u_input) & (db['password'] == p_input)]
                if not m.empty:
                    st.session_state.logged_in, st.session_state.user_role = True, m.iloc[0]['role']
                    st.session_state.active_user, st.session_state.my_branch = u_input, m.iloc[0]['branch_name']
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل", ["📊 التقارير العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.sidebar.selectbox("تصفية الفرع", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("التنقل", ["🛒 شاشة البيع", "📦 المخزن", "💸 المصروفات", "📊 التقارير", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- شاشة البيع ---
if menu == "🛒 شاشة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    search = st.text_input("🔍 ابحث...")
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    current_bill = []
    
    for it in my_inv:
        if not search or search.lower() in it['item'].lower():
            st.markdown(f"<div class='item-card'><b>{it['item']}</b> (المتوفر: {format_num(it['كمية'])})</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            opts = ["وحدة/علبة"]
            if it.get('سعر_القطعة', 0) > 0: opts.append("تجزئة/فرط")
            stype = c1.selectbox("النوع", opts, key=f"st_{it['item']}")
            val = clean_num(c2.text_input("المبلغ ₪", key=f"v_{it['item']}"))
            if val > 0:
                p = it['بيع'] if stype == "وحدة/علبة" else it.get('سعر_القطعة', it['بيع'])
                qty = (val/p)/20 if (stype=="تجزئة/فرط" and it.get('قسم')=="سجائر") else (val/p)
                current_bill.append({'item': it['item'], 'amount': val, 'profit': val - (it['شراء']*qty), 'qty_sub': qty})

    if current_bill and st.button("✅ إتمام الفاتورة"):
        st.session_state.show_checkout = True

    if st.session_state.get('show_checkout'):
        with st.expander("🏁 بيانات الزبون", expanded=True):
            c_name = st.text_input("الاسم")
            c_method = st.selectbox("الدفع", ["نقدي", "دين/آجل"])
            if st.button("🚀 حفظ"):
                for b in current_bill:
                    for i, inv in enumerate(st.session_state.inventory):
                        if inv['item'] == b['item'] and inv['branch'] == st.session_state.my_branch:
                            st.session_state.inventory[i]['كمية'] -= b['qty_sub']
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': b['item'], 'amount': b['amount'], 'profit': b['profit'], 'method': c_method, 'customer_name': c_name, 'branch': st.session_state.my_branch}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.session_state.show_checkout = False; st.rerun()

elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
    with st.form("add"):
        n = st.text_input("الصنف")
        b, s, p, qty = st.text_input("شراء"), st.text_input("بيع"), st.text_input("فرط"), st.text_input("الكمية")
        if st.form_submit_button("حفظ"):
            st.session_state.inventory.append({"item": n, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(qty), "branch": st.session_state.my_branch, "سعر_القطعة": clean_num(p)})
            auto_save(); st.rerun()

elif menu in ["📊 التقارير العامة", "📊 التقارير"]:
    st.markdown("<h1 class='main-title'>📊 التقارير</h1>", unsafe_allow_html=True)
    st.dataframe(st.session_state.sales_df, use_container_width=True)

elif menu == "📦 المخزن":
    st.table(pd.DataFrame([i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]))
