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

# 2. تحميل البيانات الأساسية
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

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    existing_cats = cat_df['name'].tolist() if not cat_df.empty else []
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + existing_cats))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم الأصلي (الذي نال إعجابك)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-left: 2px solid #27ae60; }
    [data-testid="stSidebar"] .stRadio div label { background-color: #334155; border-radius: 10px; padding: 12px 20px !important; margin-bottom: 10px; border-right: 5px solid transparent; transition: 0.3s; }
    [data-testid="stSidebar"] .stRadio div label[data-selected="true"] { background-color: #27ae60 !important; border-right: 5px solid #14532d; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; margin-bottom: 25px; border-bottom: 2px solid #334155; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; border-radius: 10px; }
    .sale-card { background: #f8fafc; padding: 15px; border-radius: 10px; border-right: 5px solid #27ae60; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("👤 اسم المستخدم").strip()
        p = st.text_input("🔑 كلمة المرور", type="password").strip()
        if st.form_submit_button("دخول"):
            db = pd.read_csv(get_db_path())
            m = db[(db['user_name'] == u) & (db['password'] == p)]
            if not m.empty:
                st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, m.iloc[0]['role'], u
                st.session_state.my_branch = m.iloc[0]['branch_name']; st.rerun()
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)
menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف"])

# --- 🛒 نقطة البيع (رجعت متل ما كانت) ---
if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع المباشر</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    search = st.text_input("🔍 ابحث عن صنف أو دخان...")
    
    bill_items = []
    for it in my_inv:
        if not search or search.lower() in it['item'].lower():
            st.markdown(f"""<div class='sale-card'>""", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{it['item']}** | <small>{it['قسم']}</small>", unsafe_allow_html=True)
            
            # خيار التجزئة يظهر فقط للدخان أو ما له سعر قطعة
            opts = ["وحدة كاملة", "تجزئة/سيجارة"] if it.get('سعر_القطعة', 0) > 0 else ["وحدة كاملة"]
            mode = c2.selectbox("النوع", opts, key=f"m_{it['item']}_{it['branch']}")
            
            price_to_use = it['بيع'] if mode == "وحدة كاملة" else it['سعر_القطعة']
            val = clean_num(c3.text_input(f"المبلغ (سعرها: {price_to_use} ₪)", key=f"p_{it['item']}_{it['branch']}"))
            
            if val > 0:
                if mode == "تجزئة/سيجارة":
                    # إذا كان سجائر، السيجارة هي 1/20 من العلبة
                    qty = (val / it['سعر_القطعة']) / 20 if it['قسم'] == "سجائر" else (val / it['سعر_القطعة'])
                    cost = it['شراء'] / 20 if it['قسم'] == "سجائر" else it['شراء']
                    profit = val - (cost * (val / it['سعر_القطعة']))
                else:
                    qty = val / it['بيع']
                    profit = (it['بيع'] - it['شراء']) * qty
                bill_items.append({"item": it['item'], "qty": qty, "amount": val, "profit": profit})
            st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🚀 تنفيذ العملية وطباعة") and bill_items:
        for e in bill_items:
            for idx, inv_item in enumerate(st.session_state.inventory):
                if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                    st.session_state.inventory[idx]['كمية'] -= e['qty']
            new_sale = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': 'نقداً', 'customer_name': 'عام', 'customer_phone': '', 'bill_id': str(uuid.uuid4())[:8], 'branch': st.session_state.my_branch}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
        auto_save(); st.success("✅ تمت العملية بنجاح"); st.rerun()

# --- 📦 المخزن والجرد (رجعت متل ما كانت) ---
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 جرد المخزن الحالي</h1>", unsafe_allow_html=True)
    my_data = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    if my_data:
        df_display = pd.DataFrame(my_data)
        st.table(df_display[['item', 'قسم', 'كمية', 'بيع', 'شراء']])
        
        # ملخص رأس المال في المخزن
        total_stock_value = sum(i['كمية'] * i['شراء'] for i in my_data)
        st.info(f"💰 إجمالي قيمة البضاعة في المخزن (بسعر الشراء): {format_num(total_stock_value)} ₪")
    else:
        st.warning("المخزن فارغ حالياً.")

# --- 📊 التقارير المالية (رجعت متل ما كانت) ---
elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 الأداء المالي</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df[st.session_state.sales_df['branch'] == st.session_state.my_branch]
    e_df = st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي المبيعات", f"{format_num(s_df['amount'].sum())} ₪")
    col2.metric("صافي الأرباح", f"{format_num(s_df['profit'].sum())} ₪")
    col3.metric("المصروفات", f"{format_num(e_df['amount'].sum())} ₪")
    
    st.write("### سجل المبيعات التفصيلي")
    st.dataframe(s_df.sort_values(by='date', ascending=False), use_container_width=True)

# --- ⚙️ إدارة الأصناف (مع ميزة السجائر المحمية) ---
elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ الإدارة والتحكم</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ إضافة أصناف", "🛠️ تعديل", "📂 الأقسام"])
    
    with tab1:
        cat_sel = st.selectbox("القسم:", st.session_state.categories)
        with st.form("add_f", clear_on_submit=True):
            name = st.text_input("اسم الصنف")
            if cat_sel == "سجائر":
                c1, c2 = st.columns(2)
                q1 = c1.text_input("علب كاملة", "0")
                q2 = c2.text_input("فرط (سجائر)", "0")
                b = st.text_input("سعر شراء العلبة")
                s = st.text_input("سعر بيع العلبة")
                sp = st.text_input("سعر السيجارة الواحدة")
            else:
                q1 = st.text_input("الكمية")
                q2 = "0"; sp = "0"
                b = st.text_input("سعر الشراء")
                s = st.text_input("سعر البيع")
            
            if st.form_submit_button("إضافة"):
                qty = clean_num(q1) + (clean_num(q2)/20 if cat_sel == "سجائر" else 0)
                st.session_state.inventory.append({"item": name, "قسم": cat_sel, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": qty, "branch": st.session_state.my_branch, "سعر_القطعة": clean_num(sp)})
                auto_save(); st.rerun()

    with tab2:
        my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
        if my_inv:
            edited = st.data_editor(pd.DataFrame(my_inv))
            if st.button("حفظ التعديلات"):
                st.session_state.inventory = [i for i in st.session_state.inventory if i.get('branch') != st.session_state.my_branch] + edited.to_dict('records')
                auto_save(); st.rerun()

    with tab3:
        for c in st.session_state.categories:
            c1, c2 = st.columns([4,1]); c1.write(c)
            if c != "سجائر" and c2.button("❌", key=f"del_{c}"):
                st.session_state.categories.remove(c); auto_save(); st.rerun()

# --- 💸 المصروفات ---
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 إدارة المصاريف</h1>", unsafe_allow_html=True)
    with st.form("exp_f"):
        r = st.text_input("السبب")
        a = st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
            auto_save(); st.rerun()
