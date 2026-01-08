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
        if val == int(val) or val == float(int(val)): return str(int(val))
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

# --- إدارة الفروع والقاعدة (تعديل بيانات الدخول الافتراضية لضمان العمل) ---
def get_db_path(): return 'branches_config.csv'

def initialize_db():
    path = get_db_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame([
            # تم تحويل اسم المستخدم للإنجليزية لضمان عدم حدوث خطأ في الترميز عند الدخول الأول
            {'branch_name': 'المدير العام', 'user_name': 'abu_omar', 'password': 'admin', 'role': 'admin'},
            {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
        ])
        df.to_csv(path, index=False, encoding='utf-8-sig')
    return pd.read_csv(path, encoding='utf-8-sig')

# 2. تحميل البيانات الأساسية
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

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
    existing_cats = cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + existing_cats))

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
    .nav-label { color: #94a3b8; font-size: 14px; margin: 20px 10px 10px 0; font-weight: bold; }
    [data-testid="stSidebar"] .stRadio div label { background-color: #1e293b; border-radius: 12px; padding: 10px 15px !important; margin-bottom: 8px; border: 1px solid #334155; }
    [data-testid="stSidebar"] .stRadio div label[data-selected="true"] { background-color: #10b981 !important; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 700 !important; font-size: 16px !important; }
    .main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-container { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #10b981; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("👤 اسم المستخدم (جرب abu_omar)").strip()
        p = st.text_input("🔑 كلمة المرور", type="password").strip()
        if st.form_submit_button("دخول"):
            db = initialize_db()
            m = db[(db['user_name'] == u) & (db['password'] == p)]
            if not m.empty:
                st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, m.iloc[0]['role'], u
                st.session_state.my_branch = m.iloc[0]['branch_name']; st.rerun()
            else: st.error("❌ خطأ في اسم المستخدم أو كلمة المرور")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
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

# --- بقية أقسام الكود (كما هي بدون أي تغيير) ---
if menu in ["📊 التقارير المالية العامة", "📊 التقارير المالية"]:
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    if active_branch != "كافة الفروع":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-container'><div style='color:#64748b'>💰 المبيعات</div><div style='font-size:24px; font-weight:900;'>{format_num(s_df['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-container'><div style='color:#64748b'>📈 الربح</div><div style='font-size:24px; font-weight:900;'>{format_num(s_df['profit'].sum())} ₪</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-container'><div style='color:#64748b'>📉 المصاريف</div><div style='font-size:24px; font-weight:900;'>{format_num(e_df['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
    with c4: 
        net = s_df['profit'].sum() - e_df['amount'].sum()
        st.markdown(f"<div class='metric-container'><div style='color:#64748b'>⚖️ الصافي</div><div style='font-size:24px; font-weight:900; color:{'#10b981' if net >= 0 else '#ef4444'}'>{format_num(net)} ₪</div></div>", unsafe_allow_html=True)
    tab_s, tab_e = st.tabs(["📑 سجل المبيعات", "💸 سجل المصروفات"])
    tab_s.dataframe(s_df.sort_values(by='date', ascending=False), use_container_width=True)
    tab_e.dataframe(e_df.sort_values(by='date', ascending=False), use_container_width=True)

elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف والأقسام</h1>", unsafe_allow_html=True)
    target_branch = st.session_state.my_branch if st.session_state.user_role != "admin" else st.selectbox("🏬 المحل:", pd.read_csv(get_db_path())['branch_name'].tolist())
    tab_add, tab_manage, tab_cats = st.tabs(["➕ إضافة أصناف", "🛠️ تعديل المخزن", "📂 إدارة الأقسام"])
    with tab_add:
        cat_selection = st.selectbox("القسم:", st.session_state.categories)
        with st.form("admin_add_i", clear_on_submit=True):
            if cat_selection == "سجائر":
                n = st.text_input("اسم الدخان")
                c1, c2 = st.columns(2)
                q_box, q_singles = c1.text_input("كمية العلب", "0"), c2.text_input("سجائر فرط", "0")
                b, s, sub_p = st.text_input("تكلفة العلبة"), st.text_input("بيع العلبة"), st.text_input("بيع السيجارة")
            else:
                n, q_box, q_singles = st.text_input("اسم الصنف"), st.text_input("الكمية"), "0"
                b, s, sub_p = st.text_input("سعر الشراء"), st.text_input("سعر البيع"), "0"
            if st.form_submit_button("➕ حفظ"):
                if n:
                    total_qty = clean_num(q_box) + (clean_num(q_singles) / 20)
                    st.session_state.inventory.append({"item": n, "قسم": cat_selection, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": total_qty, "branch": target_branch, "سعر_القطعة": clean_num(sub_p)})
                    auto_save(); st.success(f"✅ تم حفظ {n}"); st.rerun()
    with tab_cats:
        with st.form("c_f"):
            nc = st.text_input("قسم جديد")
            if st.form_submit_button("إضافة"):
                if nc and nc not in st.session_state.categories: st.session_state.categories.append(nc); auto_save(); st.rerun()
        for c in st.session_state.categories:
            c1, c2 = st.columns([4,1]); c1.write(f"📂 {c}")
            if c != "سجائر" and c2.button("❌", key=f"d_{c}"):
                st.session_state.categories.remove(c); auto_save(); st.rerun()

elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    search = st.text_input("🔍 ابحث...")
    bill = []
    for it in my_inv:
        if not search or search.lower() in it['item'].lower():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{it['item']}**")
            opts = ["وحدة", "تجزئة"] if it.get('سعر_القطعة',0) > 0 else ["وحدة"]
            m = c2.selectbox("النوع", opts, key=f"m_{it['item']}")
            v = clean_num(c3.text_input("₪", key=f"v_{it['item']}"))
            if v > 0:
                p = it['بيع'] if m == "وحدة" else it['سعر_القطعة']
                q = (v/p)/20 if (m=="تجزئة" and it['قسم']=="سجائر") else (v/p)
                bill.append({"item": it['item'], "qty": q, "amount": v, "profit": v - (it['شراء']*q)})
    if st.button("🚀 تنفيذ") and bill:
        for e in bill:
            for i, item in enumerate(st.session_state.inventory):
                if item['item'] == e['item'] and item['branch'] == st.session_state.my_branch: st.session_state.inventory[i]['كمية'] -= e['qty']
            new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'branch': st.session_state.my_branch}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
        auto_save(); st.rerun()

elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
    with st.form("br_add"):
        bn, un, pw = st.text_input("اسم المحل"), st.text_input("المستخدم"), st.text_input("المرور")
        if st.form_submit_button("إضافة"):
            new_db = pd.concat([pd.read_csv(get_db_path()), pd.DataFrame([{'branch_name':bn,'user_name':un,'password':pw,'role':'shop'}])])
            new_db.to_csv(get_db_path(), index=False); st.rerun()
    st.dataframe(pd.read_csv(get_db_path()), use_container_width=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 المخزن</h1>", unsafe_allow_html=True)
    st.table(pd.DataFrame([i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]))

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_f"):
        r, a = st.text_input("البيان"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()

elif menu == "👤 ملفي الشخصي":
    st.markdown("<h1 class='main-title'>👤 ملفي الشخصي</h1>", unsafe_allow_html=True)
    st.write(f"المستخدم: {st.session_state.active_user}")
