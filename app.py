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

# --- إدارة الفروع والقاعدة ---
def get_db_path(): return 'branches_config.csv'

def initialize_db():
    path = get_db_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame([
            {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
            {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
        ])
        df.to_csv(path, index=False)
    return pd.read_csv(path)

# 2. تحميل البيانات الأساسية (Session State)
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value', 'branch']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value', 'branch'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        st.session_state[state_key] = safe_read_csv(file, cols)

# إصلاح مهم: التأكد من تحميل المخزن كـ List of Dicts
if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False

# دالة الحفظ التلقائي مع فرض التحديث
def auto_save():
    df_to_save = pd.DataFrame(st.session_state.inventory)
    df_to_save.to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-left: 2px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; margin-bottom: 25px; border-bottom: 2px solid #334155; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; border-radius: 10px; }
    .rep-card { background: white; border-radius: 15px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #27ae60; }
    .rep-label { color: #7f8c8d; font-size: 1rem; font-weight: bold; margin-bottom: 10px; }
    .rep-value { color: #2c3e50; font-size: 1.8rem; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("👤 اسم المستخدم").strip()
            p = st.text_input("🔑 كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول"):
                db = pd.read_csv(get_db_path())
                m = db[(db['user_name'] == u) & (db['password'] == p)]
                if not m.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = m.iloc[0]['role']
                    st.session_state.active_user = u
                    st.session_state.my_branch = m.iloc[0]['branch_name']
                    st.rerun()
                elif u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.session_state.my_branch = "المدير العام"
                    st.rerun()
                else: st.error("❌ خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)
if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل السريع", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.sidebar.selectbox("🏠 اختيار الفرع للعرض:", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# --- قسم إدارة الأصناف ---
if menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة التحكم الشامل بالأصناف</h1>", unsafe_allow_html=True)
    
    if st.session_state.user_role == "admin":
        branch_list = pd.read_csv(get_db_path())['branch_name'].tolist()
        target_branch = st.selectbox("🏬 اختر الفرع للتحكم ببياناته:", branch_list)
    else:
        target_branch = st.session_state.my_branch

    t_add, t_manage, t_cats = st.tabs(["➕ إضافة أصناف للفرع", "🛠️ جرد وتعديل مخزن الفرع", "📂 إدارة الأقسام"])

    with t_add:
        with st.form("admin_add_i", clear_on_submit=True):
            st.info(f"إضافة صنف جديد إلى: {target_branch}")
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            b = st.number_input("سعر التكلفة (شراء)", min_value=0.0, step=0.1)
            s = st.number_input("سعر البيع", min_value=0.0, step=0.1)
            q = st.number_input("الكمية المتوفرة", min_value=0.0, step=1.0)
            if st.form_submit_button("➕ تنفيذ الإضافة"):
                if n:
                    # إضافة الصنف للـ Session State وللقائمة
                    new_item = {
                        "item": n, "branch": target_branch, "قسم": cat, 
                        "شراء": b, "بيع": s, "كمية": q
                    }
                    st.session_state.inventory.append(new_item)
                    auto_save() # الحفظ الفوري في الملف
                    st.success(f"✅ تم إضافة {n} بنجاح!")
                    st.rerun()

    with t_manage:
        st.subheader(f"قائمة بضائع فرع: {target_branch}")
        branch_data = [i for i in st.session_state.inventory if i.get('branch') == target_branch]
        if branch_data:
            df_branch = pd.DataFrame(branch_data)
            edited_df = st.data_editor(
                df_branch,
                column_config={
                    "item": "اسم الصنف",
                    "قسم": st.column_config.SelectboxColumn("القسم", options=st.session_state.categories),
                    "شراء": "سعر الشراء",
                    "بيع": "سعر البيع",
                    "كمية": "الكمية"
                },
                num_rows="dynamic", use_container_width=True, key="inv_editor"
            )
            if st.button("💾 حفظ التعديلات"):
                # تحديث المخزن الرئيسي باستثناء الفرع الحالي ثم إضافة الجديد
                other_branches = [i for i in st.session_state.inventory if i.get('branch') != target_branch]
                updated_branch = edited_df.to_dict('records')
                st.session_state.inventory = other_branches + updated_branch
                auto_save()
                st.success("✅ تم التحديث"); st.rerun()
        else:
            st.warning("المخزن فارغ.")

    with t_cats:
        st.subheader("إدارة الأقسام")
        with st.form("c_form", clear_on_submit=True):
            nc = st.text_input("اسم القسم")
            if st.form_submit_button("حفظ"):
                if nc and nc not in st.session_state.categories:
                    st.session_state.categories.append(nc); auto_save(); st.rerun()
        for c in st.session_state.categories:
            c1, c2 = st.columns([4,1])
            c1.write(f"📂 {c}")
            if c2.button("❌", key=f"del_{c}"):
                st.session_state.categories.remove(c); auto_save(); st.rerun()

# --- قسم نقطة البيع ---
elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    # تصفية الأصناف لهذا الفرع فقط
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    if not my_inv:
        st.error("⚠️ لا توجد أصناف في مخزنك! اذهب لإدارة الأصناف وأضف بضاعة أولاً.")
    else:
        # (بقية كود نقطة البيع كما هي لكن تم التأكد من ربط my_inv)
        if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
        p_cols = st.columns(3)
        if p_cols[0].button("📱 تطبيق", use_container_width=True, type="primary" if st.session_state.p_method == "تطبيق" else "secondary"): st.session_state.p_method = "تطبيق"
        if p_cols[1].button("💵 نقداً", use_container_width=True, type="primary" if st.session_state.p_method == "نقداً" else "secondary"): st.session_state.p_method = "نقداً"
        if p_cols[2].button("📝 دين", use_container_width=True, type="primary" if st.session_state.p_method == "دين / آجل" else "secondary"): st.session_state.p_method = "دين / آجل"

        bill_items = []
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i.get('قسم') == cat]
            if items:
                st.markdown(f"#### 📂 {cat}")
                grid = st.columns(3)
                for idx, it in enumerate(items):
                    with grid[idx % 3]:
                        with st.container(border=True):
                            st.write(f"**{it['item']}** (السعر: {it['بيع']})")
                            val = st.number_input(f"المبلغ {it['item']}", min_value=0.0, step=1.0, key=f"sale_{it['item']}_{idx}")
                            if val > 0:
                                qty = val / it['بيع']
                                if qty <= it['كمية']:
                                    bill_items.append({"item": it['item'], "qty": qty, "amount": val, "profit": (it['بيع'] - it['شراء']) * qty})
                                else: st.error("عجز!")

        if bill_items and st.button("🚀 إتمام العملية"):
            b_id = str(uuid.uuid4())[:8]
            for e in bill_items:
                for idx, inv_item in enumerate(st.session_state.inventory):
                    if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                        st.session_state.inventory[idx]['كمية'] -= e['qty']
                new_sale = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون', 'customer_phone': '', 'bill_id': b_id, 'branch': st.session_state.my_branch}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
            auto_save(); st.success("تم الحفظ"); st.rerun()

# --- بقية الأقسام (المخزن، التقارير) تعمل تلقائياً مع auto_save ---
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 المخزن</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    if my_inv:
        st.dataframe(pd.DataFrame(my_inv), use_container_width=True)
    else:
        st.info("المخزن فارغ.")

elif menu in ["📊 التقارير المالية العامة", "📊 التقارير المالية"]:
    st.markdown("<h1 class='main-title'>📊 التقارير</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df.copy()
    if active_branch != "كافة الفروع": s_df = s_df[s_df['branch'] == active_branch]
    st.metric("إجمالي المبيعات", f"{s_df['amount'].sum()} ₪")
    st.dataframe(s_df, use_container_width=True)

elif menu == "🏪 إدارة الفروع":
    st.table(pd.read_csv(get_db_path()))

elif menu == "💸 المصروفات":
    st.write("إدارة المصروفات")
    # ... كود المصروفات البسيط ...

elif menu == "👤 ملفي الشخصي":
    st.write(f"المستخدم: {st.session_state.active_user}")
