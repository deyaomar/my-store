import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime, timedelta

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
        df = pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])
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

# 3. واجهة المستخدم
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 26px; text-align: center; margin-bottom: 25px; border-bottom: 3px solid #27ae60; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; border-radius: 10px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 10px; }
    .metric-label { font-size: 15px; color: #7f8c8d; font-weight: bold; }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    .capital-box { border-right-color: #e67e22; background-color: #fff9f4; }
    .section-header { background: #f1f4f6; padding: 10px; border-radius: 10px; color: #2c3e50; font-weight: 900; margin: 15px 0; border-right: 5px solid #27ae60; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; }
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
                if u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                db = pd.read_csv(get_db_path())
                m = db[(db['user_name'] == u) & (db['password'] == p)]
                if not m.empty:
                    st.session_state.logged_in, st.session_state.user_role = True, "shop"
                    st.session_state.my_branch, st.session_state.active_user = m.iloc[0]['branch_name'], u
                    st.rerun()
                else: st.error("❌ خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل السريع", ["📊 التقارير العامة", "🏪 إدارة الفروع", "⚙️ الإعدادات"])
    active_branch = st.sidebar.selectbox("🏠 عرض فرع:", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# --- محتوى الأقسام ---

if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة وتعديل الفروع</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.5])
    with c1:
        with st.form("add_br"):
            bn = st.text_input("اسم المحل")
            un = st.text_input("المستخدم")
            pw = st.text_input("المرور")
            if st.form_submit_button("حفظ"):
                df = pd.read_csv(get_db_path())
                pd.concat([df, pd.DataFrame([{'branch_name':bn,'user_name':un,'password':pw}])]).to_csv(get_db_path(), index=False)
                st.rerun()
    with c2: st.table(pd.read_csv(get_db_path()))

elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة بيع البضاعة</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    if st.session_state.show_cust_fields:
        with st.status("✅ تم حفظ الفاتورة!"):
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الهاتف")
            if st.button("💾 حفظ وربط"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                auto_save(); st.session_state.show_cust_fields = False; st.rerun()
            if st.button("⏩ تخطي"): st.session_state.show_cust_fields = False; st.rerun()
    else:
        st.session_state.p_method = st.radio("طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
        search_q = st.text_input("🔍 ابحث عن صنف...")
        bill_items = []
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i.get('قسم') == cat]
            if search_q: items = [i for i in items if search_q in i['item']]
            if items:
                with st.expander(f"📂 {cat}", expanded=True):
                    for it in items:
                        c1, c2, c3 = st.columns([2, 1, 2])
                        c1.markdown(f"**{it['item']}**\n<small>متوفر: {format_num(it['كمية'])}</small>", unsafe_allow_html=True)
                        mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{it['item']}", horizontal=True)
                        val = clean_num(c3.text_input("المقدار", key=f"v_{it['item']}"))
                        if val > 0:
                            qty = val if mode == "كجم" else val / it['بيع']
                            bill_items.append({"item": it['item'], "qty": qty, "amount": val if mode == "₪" else val * it['بيع'], "profit": (it['بيع'] - it['شراء']) * qty})
        
        if st.button("🚀 إتمام البيع", type="primary") and bill_items:
            b_id = str(uuid.uuid4())[:8]
            for e in bill_items:
                for idx, inv_item in enumerate(st.session_state.inventory):
                    if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                        st.session_state.inventory[idx]['كمية'] -= e['qty']
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id, 'branch': st.session_state.my_branch}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            st.session_state.current_bill_id = b_id
            auto_save(); st.session_state.show_cust_fields = True; st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    t_list, t_jard = st.tabs(["📋 الرصيد", "⚖️ الجرد"])
    with t_list: st.dataframe(pd.DataFrame(my_inv), use_container_width=True)
    with t_jard:
        new_counts = {}
        for it in my_inv:
            c1, c2, c3 = st.columns([2, 1, 2])
            c1.write(f"**{it['item']}**")
            res = c3.text_input("الوزن الحقيقي", key=f"j_{it['item']}")
            if res != "": new_counts[it['item']] = clean_num(res)
        if st.button("✔️ اعتماد الجرد"):
            for name, rq in new_counts.items():
                for idx, inv_item in enumerate(st.session_state.inventory):
                    if inv_item['item'] == name and inv_item['branch'] == st.session_state.my_branch:
                        diff = inv_item['كمية'] - rq
                        st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': name, 'diff_qty': diff, 'loss_value': diff * inv_item['شراء'], 'branch': st.session_state.my_branch}])], ignore_index=True)
                        st.session_state.inventory[idx]['كمية'] = rq
            auto_save(); st.rerun()

elif menu == "📊 التقارير المالية" or menu == "📊 التقارير العامة":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية ورأس المال</h1>", unsafe_allow_html=True)
    
    sales = st.session_state.sales_df[st.session_state.sales_df['branch'] == active_branch].copy() if active_branch != "كافة الفروع" else st.session_state.sales_df.copy()
    if not sales.empty: sales['date_dt'] = pd.to_datetime(sales['date'])
    
    inv_df = pd.DataFrame(st.session_state.inventory)
    # الإصلاح هنا: التأكد من وجود عمود branch قبل الفلترة
    if not inv_df.empty and 'branch' in inv_df.columns:
        if active_branch != "كافة الفروع": 
            inv_df = inv_df[inv_df['branch'] == active_branch]
    
    if not inv_df.empty:
        inv_df['total_capital'] = inv_df['شراء'] * inv_df['كمية']
        total_cap = inv_df['total_capital'].sum()
    else:
        total_cap = 0.0

    row = st.columns(3)
    row[0].markdown(f"<div class='metric-box'><div class='metric-label'>إجمالي المبيعات</div><div class='metric-value'>{format_num(sales['amount'].sum()) if not sales.empty else 0} ₪</div></div>", unsafe_allow_html=True)
    row[1].markdown(f"<div class='metric-box'><div class='metric-label'>صافي الأرباح</div><div class='metric-value'>{format_num(sales['profit'].sum()) if not sales.empty else 0} ₪</div></div>", unsafe_allow_html=True)
    row[2].markdown(f"<div class='metric-box capital-box'><div class='metric-label'>رأس المال الحالي</div><div class='metric-value'>{format_num(total_cap)} ₪</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>تفصيل رأس مال الأقسام</div>", unsafe_allow_html=True)
    if not inv_df.empty and 'قسم' in inv_df.columns:
        cat_cap = inv_df.groupby('قسم')['total_capital'].sum().reset_index()
        cols = st.columns(len(cat_cap))
        for i, r in cat_cap.iterrows():
            cols[i].markdown(f"<div class='metric-box' style='border-right-color: #9b59b6;'><div class='metric-label'>{r['قسم']}</div><div class='metric-value'>{format_num(r['total_capital'])} ₪</div></div>", unsafe_allow_html=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
    with st.form("add_i"):
        n = st.text_input("الصنف"); cat = st.selectbox("القسم", st.session_state.categories)
        b = st.text_input("سعر التكلفة"); s = st.text_input("سعر البيع"); q = st.text_input("الكمية")
        if st.form_submit_button("إضافة للمخزن"):
            st.session_state.inventory.append({"item": n, "قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q), "branch": st.session_state.my_branch})
            auto_save(); st.success("تم الحفظ"); st.rerun()

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_f"):
        r = st.text_input("البيان"); a = st.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()
    st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch], use_container_width=True)
