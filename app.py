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
            {'branch_name': 'الإدارة العامة', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
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
    st.session_state.categories = cat_df['name'].tolist() if not cat_df.empty else ["عام"]

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
                    st.session_state.user_role = m.iloc[0]['role']
                    st.session_state.active_user = u
                    st.session_state.my_branch = m.iloc[0]['branch_name']
                    st.rerun()
                else: st.error("❌ خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل السريع", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف الشاملة", "👤 ملفي الشخصي"])
    branch_options = ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist()
    active_branch = st.sidebar.selectbox("🏠 اختيار الفرع للعرض:", branch_options)
else:
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# --- قسم إدارة الأصناف (المنفصل) ---
if menu in ["⚙️ إدارة الأصناف الشاملة", "⚙️ إدارة الأصناف"]:
    st.markdown(f"<h1 class='main-title'>⚙️ إدارة الأصناف - {st.session_state.my_branch}</h1>", unsafe_allow_html=True)
    
    # تحديد الفرع المستهدف بناءً على الرتبة
    if st.session_state.user_role == "admin":
        branch_list = pd.read_csv(get_db_path())['branch_name'].tolist()
        target_branch = st.selectbox("🏬 اختر الفرع الذي تريد التحكم بأصنافه:", branch_list)
    else:
        target_branch = st.session_state.my_branch
        st.info(f"إدارة أصناف فرع: {target_branch}")

    t_add, t_manage, t_cats = st.tabs(["➕ إضافة أصناف", "🛠️ جرد وتعديل مخزن الفرع", "📂 إدارة الأقسام"])

    with t_add:
        with st.form("add_item_form", clear_on_submit=True):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            c_b, c_s, c_q = st.columns(3)
            b = c_b.number_input("سعر التكلفة", min_value=0.0, step=0.1)
            s = c_s.number_input("سعر البيع", min_value=0.0, step=0.1)
            q = c_q.number_input("الكمية الأولية", min_value=0.0, step=1.0)
            
            if st.form_submit_button("➕ حفظ الصنف"):
                if n and s > 0:
                    st.session_state.inventory.append({
                        "item": n, "قسم": cat, "شراء": b, "بيع": s, "كمية": q, "branch": target_branch
                    })
                    auto_save()
                    st.success(f"✅ تم إضافة {n} بنجاح!")
                    st.rerun()

    with t_manage:
        branch_data = [i for i in st.session_state.inventory if i.get('branch') == target_branch]
        if branch_data:
            df_branch = pd.DataFrame(branch_data)
            edited_df = st.data_editor(
                df_branch[['item', 'قسم', 'شراء', 'بيع', 'كمية']],
                num_rows="dynamic", use_container_width=True, key=f"editor_{target_branch}"
            )
            if st.button("💾 حفظ التعديلات"):
                # حذف القديم للفرع المحدد وحفظ الجديد
                new_inv = [i for i in st.session_state.inventory if i.get('branch') != target_branch]
                for _, row in edited_df.iterrows():
                    new_inv.append({
                        "item": row['item'], "قسم": row['قسم'], "شراء": clean_num(row['شراء']),
                        "بيع": clean_num(row['بيع']), "كمية": clean_num(row['كمية']), "branch": target_branch
                    })
                st.session_state.inventory = new_inv
                auto_save(); st.rerun()
        else: st.warning("لا يوجد أصناف في هذا الفرع.")

    with t_cats:
        with st.form("cat_f"):
            nc = st.text_input("قسم جديد")
            if st.form_submit_button("إضافة"):
                if nc and nc not in st.session_state.categories:
                    st.session_state.categories.append(nc); auto_save(); st.rerun()
        for c in st.session_state.categories:
            st.write(f"📂 {c}")

# --- نقطة البيع ---
elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    if not my_inv:
        st.error("⚠️ لا يوجد بضاعة في مخزنك! اذهب لـ 'إدارة الأصناف' وأضف منتجاتك أولاً.")
    else:
        # اختيار طريقة الدفع
        p_method = st.radio("وسيلة الدفع:", ["نقداً", "تطبيق", "دين / آجل"], horizontal=True)
        bill_items = []
        
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i.get('قسم') == cat]
            if items:
                st.subheader(f"📂 {cat}")
                cols = st.columns(4)
                for idx, it in enumerate(items):
                    with cols[idx % 4]:
                        with st.container(border=True):
                            st.write(f"**{it['item']}**")
                            st.caption(f"السعر: {it['بيع']} | المتوفر: {it['كمية']}")
                            val = st.number_input(f"المبلغ ({it['item']})", min_value=0.0, step=1.0, key=f"sale_{it['item']}")
                            if val > 0:
                                qty = val / it['بيع']
                                if qty <= it['كمية']:
                                    bill_items.append({"item": it['item'], "qty": qty, "amount": val, "profit": (it['بيع'] - it['شراء']) * qty})
                                else: st.error("الكمية لا تكفي!")

        if bill_items:
            total = sum(i['amount'] for i in bill_items)
            st.markdown(f"### الإجمالي: {total} ₪")
            if st.button("🚀 إتمام البيع"):
                b_id = str(uuid.uuid4())[:8]
                for e in bill_items:
                    # خصم من المخزن
                    for idx, inv_item in enumerate(st.session_state.inventory):
                        if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                            st.session_state.inventory[idx]['كمية'] -= e['qty']
                    
                    # تسجيل البيع
                    new_sale = {
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'item': e['item'], 'amount': e['amount'], 'profit': e['profit'],
                        'method': p_method, 'customer_name': 'عميل', 'customer_phone': '',
                        'bill_id': b_id, 'branch': st.session_state.my_branch
                    }
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
                
                auto_save(); st.success("تم البيع!"); st.rerun()

# --- التقارير ---
elif menu in ["📊 التقارير المالية العامة", "📊 التقارير المالية"]:
    st.markdown(f"<h1 class='main-title'>📊 التقارير - {active_branch}</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df
    if active_branch != "كافة الفروع":
        s_df = s_df[s_df['branch'] == active_branch]
    
    st.metric("إجمالي المبيعات", f"{s_df['amount'].sum()} ₪")
    st.dataframe(s_df, use_container_width=True)

# --- إدارة الفروع (للمدير العام فقط) ---
elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع والمستخدمين</h1>", unsafe_allow_html=True)
    with st.form("branch_form"):
        bn = st.text_input("اسم الفرع / المحل")
        un = st.text_input("اسم المستخدم")
        pw = st.text_input("كلمة المرور")
        role = st.selectbox("الصلاحية", ["shop", "admin"])
        if st.form_submit_button("إضافة فرع جديد"):
            new_br = pd.DataFrame([{'branch_name':bn, 'user_name':un, 'password':pw, 'role':role}])
            new_db = pd.concat([pd.read_csv(get_db_path()), new_br], ignore_index=True)
            new_db.to_csv(get_db_path(), index=False)
            st.success("تمت الإضافة!"); st.rerun()
    st.table(pd.read_csv(get_db_path()))

# --- المصروفات ---
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_f"):
        r = st.text_input("البيان"); a = st.number_input("المبلغ")
        if st.form_submit_button("حفظ المصروف"):
            new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
            auto_save(); st.rerun()
    st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch])

elif menu == "👤 ملفي الشخصي":
    st.write(f"أهلاً بك يا {st.session_state.active_user}")
    st.write(f"رتبتك في النظام: {st.session_state.user_role}")
    st.write(f"الفرع التابع لك: {st.session_state.my_branch}")
