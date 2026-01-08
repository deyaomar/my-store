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

# --- نظام تسجيل الدخول المحصن ---
def get_db_path(): return 'branches_config.csv'

def force_init_db():
    path = get_db_path()
    default_data = [
        {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
        {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
    ]
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        pd.DataFrame(default_data).to_csv(path, index=False, encoding='utf-8-sig')
    return pd.read_csv(path, encoding='utf-8-sig').assign(
    role=lambda df: df['role'] if 'role' in df.columns else 'shop'
)


# 2. تحميل البيانات الأساسية
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
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + (cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"])))

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
    [data-testid="stSidebar"] .stRadio div label[data-selected="true"] { background-color: #10b981 !important; border-color: #059669; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 700 !important; font-size: 16px !important; }
    .main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-container { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #10b981; text-align: center; margin-bottom: 20px; }
    .sale-card { background: #f8fafc; padding: 15px; border-radius: 12px; border-right: 6px solid #10b981; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)

    with st.form("login_form"):
        u_in = st.text_input("👤 اسم المستخدم").strip()
        p_in = st.text_input("🔑 كلمة المرور", type="password").strip()

        if st.form_submit_button("دخول"):
            db = force_init_db()

            # تنظيف القيم من أي فراغات أو أحرف مخفية
            db['user_name'] = db['user_name'].astype(str).str.strip()
            db['password'] = db['password'].astype(str).str.strip()
            db['role'] = db['role'].astype(str).str.strip()

            # مطابقة المستخدم
            match = db[
                (db['user_name'] == u_in) &
                (db['password'] == p_in)
            ]

            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.active_user = u_in
                st.session_state.my_branch = match.iloc[0]['branch_name']
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة")

    st.stop()


# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='nav-label'>🧭 التنقل السريع</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"], label_visibility="collapsed")
    st.sidebar.markdown("<div class='nav-label'>🏠 تصفية حسب الفرع:</div>", unsafe_allow_html=True)
    active_branch = st.sidebar.selectbox("", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist(), label_visibility="collapsed")
else:
    menu = st.sidebar.radio("", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"], label_visibility="collapsed")
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- الصفحات ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع الاحترافية</h1>", unsafe_allow_html=True)
    search = st.text_input("🔍 بحث سريع عن صنف...")
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    current_bill = []
    bill_id = str(uuid.uuid4())[:8]

    for it in my_inv:
        if not search or search.lower() in it['item'].lower():
            st.markdown(f"<div class='sale-card'>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{it['item']}** \n <small>المتوفر: {format_num(it['كمية'])}</small>", unsafe_allow_html=True)
            
            opts = ["وحدة/علبة"]
            if it.get('سعر_القطعة', 0) > 0: opts.append("تجزئة/فرط")
            stype = c2.selectbox("النوع", opts, key=f"st_{it['item']}")
            
            amt = clean_num(c3.text_input("المبلغ ₪", key=f"amt_{it['item']}"))
            if amt > 0:
                price = it['بيع'] if stype == "وحدة/علبة" else it.get('سعر_القطعة', it['بيع'])
                qty = (amt/price)/20 if (stype=="تجزئة/فرط" and it.get('قسم')=="سجائر") else (amt/price)
                current_bill.append({'item': it['item'], 'amount': amt, 'profit': amt - (it['شراء']*qty), 'qty_sub': qty, 'branch': it['branch']})
            st.markdown("</div>", unsafe_allow_html=True)

    if current_bill:
        st.write("---")
        if st.button("🚀 إتمام واعتماد الفاتورة", use_container_width=True):
            st.session_state.checkout_active = True

    if st.session_state.get('checkout_active'):
        with st.expander("🏁 بيانات الزبون النهائية", expanded=True):
            c_name = st.text_input("اسم الزبون")
            c_phone = st.text_input("رقم الهاتف")
            c_method = st.selectbox("طريقة الدفع", ["نقدي", "دين/آجل", "تحويل"])
            if st.button("✅ حفظ وإتمام"):
                dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                for b in current_bill:
                    for i, inv in enumerate(st.session_state.inventory):
                        if inv['item'] == b['item'] and inv['branch'] == b['branch']:
                            st.session_state.inventory[i]['كمية'] -= b['qty_sub']
                    new_sale = {'date': dt, 'item': b['item'], 'amount': b['amount'], 'profit': b['profit'], 'method': c_method, 'customer_name': c_name, 'customer_phone': c_phone, 'bill_id': bill_id, 'branch': b['branch']}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
                auto_save(); st.session_state.checkout_active = False; st.success("تم بنجاح"); st.rerun()

elif menu in ["📊 التقارير المالية العامة", "📊 التقارير المالية"]:
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    if active_branch != "كافة الفروع":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-container'><div>💰 المبيعات</div><div style='font-size:24px; font-weight:900;'>{format_num(s_df['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-container'><div>📈 الربح</div><div style='font-size:24px; font-weight:900;'>{format_num(s_df['profit'].sum())} ₪</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-container'><div>📉 المصاريف</div><div style='font-size:24px; font-weight:900;'>{format_num(e_df['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
    with c4:
        net = s_df['profit'].sum() - e_df['amount'].sum()
        st.markdown(f"<div class='metric-container'><div>⚖️ الصافي</div><div style='font-size:24px; font-weight:900; color:{'#10b981' if net >= 0 else '#ef4444'}'>{format_num(net)} ₪</div></div>", unsafe_allow_html=True)
    st.dataframe(s_df.sort_values(by='date', ascending=False), use_container_width=True)

elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
    target_br = st.session_state.my_branch if st.session_state.user_role != "admin" else st.selectbox("المحل:", pd.read_csv(get_db_path())['branch_name'].tolist())
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        n = col1.text_input("اسم الصنف")
        cat = col2.selectbox("القسم", st.session_state.categories)
        b, s, p = st.text_input("سعر الشراء"), st.text_input("سعر البيع"), st.text_input("سعر الفرط/تجزئة (اختياري)")
        q = st.text_input("الكمية")
        if st.form_submit_button("➕ إضافة للمخزن"):
            if n:
                st.session_state.inventory.append({"item": n, "قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q), "branch": target_br, "سعر_القطعة": clean_num(p)})
                auto_save(); st.success("تم الإضافة"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 جرد المخزن</h1>", unsafe_allow_html=True)
    st.table(pd.DataFrame([i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]))

elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)

    db = pd.read_csv(get_db_path())

    st.subheader("➕ إضافة فرع جديد")
    with st.form("add_branch"):
        bn = st.text_input("اسم الفرع")
        un = st.text_input("اسم المستخدم")
        pw = st.text_input("كلمة المرور")
        if st.form_submit_button("إضافة"):
            if bn and un and pw:
                db = pd.concat([db, pd.DataFrame([{
                    'branch_name': bn,
                    'user_name': un,
                    'password': pw,
                    'role': 'shop'
                }])], ignore_index=True)
                db.to_csv(get_db_path(), index=False)
                st.success("تمت الإضافة")
                st.rerun()

    st.divider()
    st.subheader("✏️ تعديل / حذف الفروع")

    for i, row in db.iterrows():
        if row['role'] != 'shop':
            continue

        with st.expander(f"🏬 {row['branch_name']}"):
            new_bn = st.text_input("اسم الفرع", row['branch_name'], key=f"bn_{i}")
            new_un = st.text_input("اسم المستخدم", row['user_name'], key=f"un_{i}")
            new_pw = st.text_input("كلمة المرور", row['password'], key=f"pw_{i}")

            c1, c2 = st.columns(2)

            if c1.button("💾 حفظ التعديلات", key=f"save_{i}"):
                db.loc[i, ['branch_name', 'user_name', 'password']] = [new_bn, new_un, new_pw]
                db.to_csv(get_db_path(), index=False)
                st.success("تم التعديل")
                st.rerun()

            if c2.button("🗑️ حذف الفرع", key=f"del_{i}"):
                db = db.drop(i)
                db.to_csv(get_db_path(), index=False)
                st.warning("تم الحذف")
                st.rerun()


elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصاريف</h1>", unsafe_allow_html=True)
    with st.form("exp_f"):
        r, a = st.text_input("البيان"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()

elif menu == "👤 ملفي الشخصي":
    st.markdown("<h1 class='main-title'>👤 بيانات الحساب</h1>", unsafe_allow_html=True)
    st.write(f"المستخدم: {st.session_state.active_user}")
