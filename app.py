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

# --- نظام تسجيل الدخول ---
def get_db_path(): return 'branches_config.csv'

def force_init_db():
    path = get_db_path()
    default_data = [
        {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
        {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
    ]
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        pd.DataFrame(default_data).to_csv(path, index=False, encoding='utf-8-sig')
    return pd.read_csv(path, encoding='utf-8-sig')

# 2. تحميل البيانات
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = force_init_db()

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
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + (cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات", "ألبان"])))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم (CSS الأصلي)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; direction: rtl; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-left: 3px solid #10b981; }
    .sidebar-user { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white !important; font-weight: 900; font-size: 22px; text-align: center; padding: 20px; border-radius: 15px; margin: 10px; }
    .nav-label { color: #94a3b8; font-size: 14px; margin: 20px 10px 10px 0; font-weight: bold; }
    [data-testid="stSidebar"] .stRadio div label { background-color: #1e293b; border-radius: 12px; padding: 10px 15px !important; margin-bottom: 8px; border: 1px solid #334155; }
    [data-testid="stSidebar"] .stRadio div label[data-selected="true"] { background-color: #10b981 !important; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 700 !important; font-size: 16px !important; }
    .main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .sale-card { background: #f8fafc; padding: 15px; border-radius: 12px; border-right: 6px solid #10b981; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("👤 اسم المستخدم").strip()
        p = st.text_input("🔑 كلمة المرور", type="password").strip()
        if st.form_submit_button("دخول"):
            db = force_init_db()
            m = db[(db['user_name'] == u) & (db['password'] == p)]
            if not m.empty:
                st.session_state.logged_in, st.session_state.user_role = True, m.iloc[0]['role']
                st.session_state.active_user, st.session_state.my_branch = u, m.iloc[0]['branch_name']
                st.rerun()
    st.stop()

# 5. القائمة الجانبية (التنقل بالترتيب المطلوب)
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='nav-label'>🧭 التنقل</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"], label_visibility="collapsed")
else:
    # الترتيب الذي طلبه أبو عمر بالضبط
    menu = st.sidebar.radio("", [
        "🛒 نقطة البيع", 
        "📦 المخزن والجرد", 
        "💸 المصروفات", 
        "📊 التقارير المالية", 
        "⚙️ إدارة الأصناف", 
        "👤 ملفي الشخصي"
    ], label_visibility="collapsed")

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- محتوى الصفحات ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    search = st.text_input("🔍 بحث عن صنف...")
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    current_bill = []
    
    for it in my_inv:
        if not search or search.lower() in it['item'].lower():
            st.markdown(f"<div class='sale-card'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{it['item']}** \n <small>المتوفر: {format_num(it['كمية'])}</small>", unsafe_allow_html=True)
            opts = ["وحدة/علبة", "تجزئة/فرط"] if it.get('سعر_القطعة', 0) > 0 else ["وحدة/علبة"]
            stype = c2.selectbox("النوع", opts, key=f"st_{it['item']}")
            amt = clean_num(c3.text_input("المبلغ ₪", key=f"amt_{it['item']}"))
            if amt > 0:
                p = it['بيع'] if stype == "وحدة/علبة" else it.get('سعر_القطعة', it['بيع'])
                qty = (amt/p)/20 if (stype=="تجزئة/فرط" and it.get('قسم')=="سجائر") else (amt/p)
                current_bill.append({'item': it['item'], 'amount': amt, 'profit': amt - (it['شراء']*qty), 'qty_sub': qty})
            st.markdown("</div>", unsafe_allow_html=True)

    if current_bill and st.button("🚀 إتمام الفاتورة"):
        st.session_state.checkout = True

    if st.session_state.get('checkout'):
        with st.expander("📝 بيانات الزبون", expanded=True):
            c_name = st.text_input("اسم الزبون")
            c_method = st.selectbox("طريقة الدفع", ["نقدي", "دين/آجل"])
            if st.button("✅ تأكيد الحفظ"):
                dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                b_id = str(uuid.uuid4())[:8]
                for b in current_bill:
                    for i, inv in enumerate(st.session_state.inventory):
                        if inv['item'] == b['item'] and inv['branch'] == st.session_state.my_branch:
                            st.session_state.inventory[i]['كمية'] -= b['qty_sub']
                    new_sale = {'date': dt, 'item': b['item'], 'amount': b['amount'], 'profit': b['profit'], 'method': c_method, 'customer_name': c_name, 'bill_id': b_id, 'branch': st.session_state.my_branch}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
                auto_save(); st.session_state.checkout = False; st.success("تم بنجاح"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🛠️ تعديل وحذف الأصناف", "📋 الجرد اليدوي"])
    
    with tab1:
        for i, it in enumerate(st.session_state.inventory):
            if it.get('branch') == st.session_state.my_branch:
                with st.expander(f"📦 {it['item']} - الكمية الحالية: {format_num(it['كمية'])}"):
                    c1, c2, c3, c4 = st.columns(4)
                    n_n = c1.text_input("الاسم", it['item'], key=f"n_{i}")
                    n_q = c2.text_input("الكمية", format_num(it['كمية']), key=f"q_{i}")
                    n_b = c3.text_input("شراء", format_num(it['شراء']), key=f"b_{i}")
                    n_s = c4.text_input("بيع", format_num(it['بيع']), key=f"s_{i}")
                    if st.button("💾 حفظ", key=f"sv_{i}"):
                        st.session_state.inventory[i].update({'item': n_n, 'كمية': clean_num(n_q), 'شراء': clean_num(n_b), 'بيع': clean_num(n_s)})
                        auto_save(); st.rerun()
                    if st.button("🗑️ حذف", key=f"dl_{i}"):
                        st.session_state.inventory.pop(i); auto_save(); st.rerun()

    with tab2:
        st.subheader("الجرد الأسبوعي الفعلي")
        diffs = []
        for i, it in enumerate(st.session_state.inventory):
            if it.get('branch') == st.session_state.my_branch:
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{it['item']}** (مسجل: {format_num(it['كمية'])})")
                act = c2.text_input("الكمية الفعلية", key=f"act_{i}")
                if act: diffs.append({'item': it['item'], 'diff': clean_num(act) - it['كمية']})
        if st.button("📊 عرض الفروقات"):
            for d in diffs: st.write(f"{d['item']}: {d['diff']}")

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r, a = st.text_input("البيان"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()

elif menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {st.session_state.my_branch}</h1>", unsafe_allow_html=True)
    st.dataframe(st.session_state.sales_df[st.session_state.sales_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إضافة أصناف جديدة</h1>", unsafe_allow_html=True)
    with st.form("add_new"):
        n = st.text_input("اسم الصنف")
        cat = st.selectbox("القسم", st.session_state.categories)
        b, s, p, q = st.text_input("شراء"), st.text_input("بيع"), st.text_input("فرط"), st.text_input("الكمية")
        if st.form_submit_button("إضافة"):
            st.session_state.inventory.append({'item': n, 'قسم': cat, 'شراء': clean_num(b), 'بيع': clean_num(s), 'كمية': clean_num(q), 'branch': st.session_state.my_branch, 'سعر_القطعة': clean_num(p)})
            auto_save(); st.rerun()

elif menu == "👤 ملفي الشخصي":
    st.markdown("<h1 class='main-title'>👤 بيانات الحساب</h1>", unsafe_allow_html=True)
    st.write(f"اسم المستخدم: {st.session_state.active_user}")
    st.write(f"الفرع: {st.session_state.my_branch}")
