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

if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
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
    [data-testid="stSidebar"] .stRadio div label { background-color: #334155; border-radius: 10px; padding: 12px 20px !important; margin-bottom: 10px; border-right: 5px solid transparent; transition: 0.3s; }
    [data-testid="stSidebar"] .stRadio div label[data-selected="true"] { background-color: #27ae60 !important; border-right: 5px solid #14532d; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 700 !important; font-size: 18px !important; }
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
                    st.session_state.user_role = m.iloc[0]['role'] if 'role' in m.columns else "shop"
                    st.session_state.active_user = u
                    st.session_state.my_branch = m.iloc[0]['branch_name']
                    st.rerun()
                elif u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.session_state.my_branch = "المدير العام"
                    st.rerun()
                else: st.error("❌ خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية وتوزيع الصلاحيات
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التحكم المركزي", ["📊 التقارير العامة", "🏪 إدارة الفروع", "⚙️ إدارة أصناف الفروع", "📂 إدارة الأقسام", "👤 ملفي"])
    active_branch = st.sidebar.selectbox("🏠 عرض بيانات فرع:", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("قائمة المحل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير", "⚙️ إدارة الأصناف", "👤 ملفي"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# ---------------------------------------------------------
# الجزء الأول: إدارة أصناف الفروع (خاص بالمدير العام)
# ---------------------------------------------------------
if menu == "⚙️ إدارة أصناف الفروع" and st.session_state.user_role == "admin":
    st.markdown("<h1 class='main-title'>🏬 التحكم المركزي بأصناف الفروع</h1>", unsafe_allow_html=True)
    
    # 1. فلترة واختيار الفرع
    branches_list = pd.read_csv(get_db_path())['branch_name'].tolist()
    target_br = st.selectbox("🏗️ اختر الفرع لإدارة أصنافه:", branches_list)
    
    # تصفية البضاعة
    branch_inv = [i for i in st.session_state.inventory if i.get('branch') == target_br]

    # 2. إضافة صنف للفرع المختار
    with st.expander(f"➕ إضافة صنف جديد لفرع: {target_br}"):
        with st.form("admin_add_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("اسم المنتج")
            cat = c2.selectbox("القسم", st.session_state.categories)
            c3, c4, c5 = st.columns(3)
            buy = c3.number_input("سعر الشراء", min_value=0.0, step=1.0)
            sell = c4.number_input("سعر البيع", min_value=0.0, step=1.0)
            qty = c5.number_input("الكمية", min_value=0.0, step=1.0)
            if st.form_submit_button("إضافة للمخزن المركز"):
                if name:
                    st.session_state.inventory.append({'item': name, 'قسم': cat, 'شراء': buy, 'بيع': sell, 'كمية': qty, 'branch': target_br})
                    auto_save(); st.success("تم الإضافة"); st.rerun()

    st.divider()

    # 3. عرض وتعديل بضاعة الفرع
    if branch_inv:
        for idx, item in enumerate(branch_inv):
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                col1.write(f"**{item['item']}**")
                col2.write(f"شراء: {item['شراء']}")
                col3.write(f"بيع: {item['بيع']}")
                col4.write(f"الكمية: {item['كمية']}")
                if col5.button("🗑️", key=f"global_del_{idx}"):
                    st.session_state.inventory = [i for i in st.session_state.inventory if not (i['item'] == item['item'] and i['branch'] == target_br)]
                    auto_save(); st.rerun()
    else:
        st.info("لا توجد أصناف حالياً لهذا الفرع.")

# ---------------------------------------------------------
# الجزء الثاني: إدارة الأصناف (خاص بمدير الفرع)
# ---------------------------------------------------------
elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>📦 إدارة أصناف المحل</h1>", unsafe_allow_html=True)
    
    # تصفية بضاعة فرعي فقط
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]

    # 1. إضافة
    with st.expander("➕ إضافة صنف جديد"):
        with st.form("shop_add_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("اسم الصنف")
            cat = c2.selectbox("القسم", st.session_state.categories)
            c3, c4, c5 = st.columns(3)
            buy = c3.number_input("الشراء", min_value=0.0)
            sell = c4.number_input("البيع", min_value=0.0)
            qty = c5.number_input("الكمية", min_value=0.0)
            if st.form_submit_button("حفظ"):
                if name:
                    st.session_state.inventory.append({'item': name, 'قسم': cat, 'شراء': buy, 'بيع': sell, 'كمية': qty, 'branch': st.session_state.my_branch})
                    auto_save(); st.success("تم الحفظ"); st.rerun()

    # 2. عرض وتعديل وحذف
    for idx, item in enumerate(my_inv):
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.write(f"**{item['item']}**")
            col2.write(f"شراء: {item['شراء']} | بيع: {item['بيع']}")
            col3.write(f"📦: {item['كمية']}")
            
            sub_c1, sub_c2 = col4.columns(2)
            if sub_c1.button("📝", key=f"edit_{idx}"):
                st.session_state[f"edit_mode_{idx}"] = True
            if sub_c2.button("🗑️", key=f"del_{idx}"):
                st.session_state.inventory = [i for i in st.session_state.inventory if not (i['item'] == item['item'] and i['branch'] == st.session_state.my_branch)]
                auto_save(); st.rerun()
            
            # نافذة التعديل
            if st.session_state.get(f"edit_mode_{idx}", False):
                with st.form(f"f_edit_{idx}"):
                    nb = st.number_input("شراء جديد", value=float(item['شراء']))
                    ns = st.number_input("بيع جديد", value=float(item['بيع']))
                    nq = st.number_input("كمية جديدة", value=float(item['كمية']))
                    if st.form_submit_button("تحديث"):
                        for i, it in enumerate(st.session_state.inventory):
                            if it['item'] == item['item'] and it['branch'] == st.session_state.my_branch:
                                st.session_state.inventory[i].update({'شراء': nb, 'بيع': ns, 'كمية': nq})
                        auto_save(); st.session_state[f"edit_mode_{idx}"] = False; st.rerun()

# ---------------------------------------------------------
# الجزء الثالث: إدارة الأقسام (حل مشكلة with t_cats)
# ---------------------------------------------------------
elif menu == "📂 إدارة الأقسام":
    st.markdown("<h1 class='main-title'>📂 إدارة أقسام المنتجات</h1>", unsafe_allow_html=True)
    with st.form("new_cat"):
        new_c = st.text_input("اسم القسم الجديد")
        if st.form_submit_button("إضافة"):
            if new_c and new_c not in st.session_state.categories:
                st.session_state.categories.append(new_c); auto_save(); st.rerun()
    
    st.write("### الأقسام الحالية")
    for c in st.session_state.categories:
        c_col1, c_col2 = st.columns([4, 1])
        c_col1.write(c)
        if c_col2.button("❌", key=f"cat_del_{c}"):
            st.session_state.categories.remove(c); auto_save(); st.rerun()

# --- استكمال باقي الأقسام الأصلية كما هي ---
elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع الاحترافية</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    if st.session_state.get('show_cust_fields', False):
        with st.container(border=True):
            st.subheader("📱 بيانات دفع التطبيق")
            c_n = st.text_input("👤 اسم الزبون")
            c_p = st.text_input("📞 رقم الهاتف")
            if st.button("✅ إتمام", use_container_width=True):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                auto_save(); st.session_state.show_cust_fields = False; st.success("تم!"); st.rerun()
    else:
        p_method = st.radio("وسيلة الدفع", ["تطبيق", "نقداً", "دين / آجل"], horizontal=True)
        st.divider()
        bill_items = []
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i.get('قسم') == cat]
            if items:
                st.write(f"### {cat}")
                grid = st.columns(3)
                for i, it in enumerate(items):
                    with grid[i % 3]:
                        with st.container(border=True):
                            st.write(f"**{it['item']}** ({it['بيع']} ₪)")
                            val = st.number_input(f"المبلغ", min_value=0.0, key=f"s_{it['item']}_{i}")
                            if val > 0:
                                qty = val / it['بيع']
                                if qty <= it['كمية']:
                                    bill_items.append({"item": it['item'], "qty": qty, "amount": val, "profit": (it['بيع'] - it['شراء']) * qty})
                                else: st.error("المخزن لا يكفي")

        if bill_items:
            total = sum(i['amount'] for i in bill_items)
            st.write(f"## الإجمالي: {total} ₪")
            if st.button("🚀 تأكيد البيع", use_container_width=True):
                b_id = str(uuid.uuid4())[:8]
                for e in bill_items:
                    for idx, inv_item in enumerate(st.session_state.inventory):
                        if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                            st.session_state.inventory[idx]['كمية'] -= e['qty']
                    new_sale = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id, 'branch': st.session_state.my_branch}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
                auto_save(); st.session_state.current_bill_id = b_id
                if p_method == "تطبيق": st.session_state.show_cust_fields = True
                st.rerun()

elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
    with st.form("br"):
        bn = st.text_input("المحل"); un = st.text_input("المستخدم"); pw = st.text_input("المرور")
        if st.form_submit_button("حفظ"):
            new_br = pd.DataFrame([{'branch_name':bn,'user_name':un,'password':pw, 'role': 'shop'}])
            st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_br], ignore_index=True)
            st.session_state.branches_db.to_csv(get_db_path(), index=False)
            st.success("تم إضافة الفرع"); st.rerun()
    st.table(st.session_state.branches_db)

elif menu in ["📊 التقارير المالية العامة", "📊 التقارير"]:
    st.markdown(f"<h1 class='main-title'>📊 التقارير - {active_branch}</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    if active_branch != "كافة الفروع":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]
    
    st.metric("صافي الأرباح", f"{format_num(s_df['profit'].sum() - e_df['amount'].sum())} ₪")
    st.dataframe(s_df, use_container_width=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 جرد مخزن: " + st.session_state.my_branch + "</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    if my_inv:
        st.dataframe(pd.DataFrame(my_inv), use_container_width=True)
    else: st.warning("المخزن فارغ")

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 تسجيل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r = st.text_input("السبب"); a = st.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ"):
            new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
            auto_save(); st.success("تم التسجيل"); st.rerun()

elif menu == "👤 ملفي الشخصي" or menu == "👤 ملفي":
    st.markdown("<h1 class='main-title'>👤 بيانات الحساب</h1>", unsafe_allow_html=True)
    st.write(f"**المستخدم:** {st.session_state.active_user}")
    st.write(f"**الرتبة:** {st.session_state.user_role}")
    st.write(f"**الفرع:** {st.session_state.my_branch}")
