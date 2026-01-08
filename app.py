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
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية', 'سعر_القطعة'])
    st.session_state.inventory = inv_df.to_dict('records')

# --- ضمان ظهور قسم سجائر دائماً ---
if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    existing_cats = cat_df['name'].tolist() if not cat_df.empty else []
    all_cats = list(dict.fromkeys(["سجائر"] + existing_cats))
    st.session_state.categories = all_cats

if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم (CSS الأصلي)
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
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, m.iloc[0]['role'], u
                    st.session_state.my_branch = m.iloc[0]['branch_name']
                    st.rerun()
                elif u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.session_state.my_branch = "الإدارة"
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

# --- قسم إدارة الأصناف (هنا التعديل الأساسي) ---
if menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة التحكم الشامل بالأصناف</h1>", unsafe_allow_html=True)
    if st.session_state.user_role == "admin":
        branch_list = pd.read_csv(get_db_path())['branch_name'].tolist()
        target_branch = st.selectbox("🏬 اختر الفرع للتحكم ببياناته:", branch_list)
    else: target_branch = st.session_state.my_branch

    t_add, t_manage, t_cats = st.tabs(["➕ إضافة أصناف للفرع", "🛠️ جرد وتعديل مخزن الفرع", "📂 إدارة الأقسام"])

    with t_add:
        st.info(f"إضافة بضاعة لفرع: {target_branch}")
        
        # التأكد من اختيار القسم لتحديث شكل الحقول بالأسفل
        cat_selection = st.selectbox("اختر القسم لفتح تعليمات التسجيل:", st.session_state.categories)
        
        with st.form("admin_add_i", clear_on_submit=True):
            if cat_selection == "سجائر":
                st.warning("🚬 تعليمات السجائر: أدخل البيانات بالعلبة، وحدد سعر السيجارة الفردي")
                n = st.text_input("اسم نوع الدخان")
                q = st.text_input("الكمية (عدد العلب)")
                b = st.text_input("سعر التكلفة للعلبة الواحدة")
                s = st.text_input("سعر بيع العلبة كاملة")
                sub_p = st.text_input("سعر بيع السيجارة الواحدة (تجزئة)")
            else:
                n = st.text_input("اسم الصنف")
                q = st.text_input("الكمية")
                b = st.text_input("سعر شراء الوحدة")
                s = st.text_input("سعر البيع")
                sub_p = "0"

            if st.form_submit_button("➕ تنفيذ الإضافة"):
                if n:
                    st.session_state.inventory.append({
                        "item": n, "قسم": cat_selection, "شراء": clean_num(b), 
                        "بيع": clean_num(s), "كمية": clean_num(q), 
                        "branch": target_branch, "سعر_القطعة": clean_num(sub_p)
                    })
                    auto_save(); st.success(f"✅ تم إضافة {n}"); st.rerun()

    with t_manage:
        branch_data = [i for i in st.session_state.inventory if i.get('branch') == target_branch]
        if branch_data:
            df_branch = pd.DataFrame(branch_data)
            edited_df = st.data_editor(df_branch[['item', 'قسم', 'شراء', 'بيع', 'سعر_القطعة', 'كمية']], use_container_width=True)
            if st.button("💾 حفظ التعديلات"):
                new_inv = [i for i in st.session_state.inventory if i.get('branch') != target_branch]
                for _, row in edited_df.iterrows():
                    new_inv.append({**row.to_dict(), "branch": target_branch})
                st.session_state.inventory = new_inv
                auto_save(); st.success("✅ تم الحفظ!"); st.rerun()

    with t_cats:
        st.subheader("إدارة الأقسام")
        with st.form("c_form", clear_on_submit=True):
            nc = st.text_input("إضافة قسم جديد")
            if st.form_submit_button("حفظ"):
                if nc and nc not in st.session_state.categories:
                    st.session_state.categories.append(nc); auto_save(); st.rerun()
        for c in st.session_state.categories:
            c1, c2 = st.columns([4,1]); c1.write(f"📂 {c}")
            if c != "سجائر" and c2.button("❌", key=f"del_{c}"):
                st.session_state.categories.remove(c); auto_save(); st.rerun()

# --- بقية الأقسام ---
elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    search = st.text_input("🔍 بحث سريـع...")
    bill_items = []
    for it in my_inv:
        if not search or search.lower() in it['item'].lower():
            with st.container():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{it['item']}**")
                mode = c2.selectbox("النوع", ["بالوحدة", "بالتجزئة"] if it.get('سعر_القطعة', 0) > 0 else ["بالوحدة"], key=f"m_{it['item']}")
                val = clean_num(c3.text_input("المبلغ ₪", key=f"p_{it['item']}"))
                if val > 0:
                    if mode == "بالتجزئة":
                        qty = (val / it['سعر_القطعة']) / 20 if it['قسم'] == "سجائر" else (val / it['سعر_القطعة'])
                        profit = val - ((it['شراء'] / 20) * (val / it['سعر_القطعة']))
                    else:
                        qty = val / it['بيع']; profit = (it['بيع'] - it['شراء']) * qty
                    bill_items.append({"item": it['item'], "qty": qty, "amount": val, "profit": profit})
    if st.button("🚀 اعتماد البيع") and bill_items:
        for e in bill_items:
            for idx, inv_item in enumerate(st.session_state.inventory):
                if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                    st.session_state.inventory[idx]['كمية'] -= e['qty']
            new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': 'نقداً', 'customer_name': 'عام', 'customer_phone': '', 'bill_id': str(uuid.uuid4())[:8], 'branch': st.session_state.my_branch}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
        auto_save(); st.success("✅ تمت العملية!"); st.rerun()

elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
    st.table(pd.read_csv(get_db_path()))

elif menu in ["📊 التقارير المالية العامة", "📊 التقارير المالية"]:
    st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df.copy()
    if active_branch != "كافة الفروع": s_df = s_df[s_df['branch'] == active_branch]
    st.metric("إجمالي المبيعات", f"{format_num(s_df['amount'].sum())} ₪")
    st.dataframe(s_df, use_container_width=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 المخزن</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    st.table(pd.DataFrame(my_inv))

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "👤 ملفي الشخصي":
    st.markdown("<h1 class='main-title'>👤 ملفي الشخصي</h1>", unsafe_allow_html=True)
    st.write(f"المستخدم الحالي: {st.session_state.active_user}")
