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
    
    /* تنسيق خاص للمخزن */
    .inventory-card {
        background: white; border-radius: 10px; padding: 15px;
        border-right: 5px solid #27ae60; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .inv-label { color: #64748b; font-size: 0.9rem; font-weight: bold; }
    .inv-value { color: #1e293b; font-size: 1.1rem; font-weight: 900; }
    
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 3em; background: #27ae60; color: white; border: none; }
    
    .product-card { background: white; border-radius: 12px; padding: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; margin-bottom: 10px; text-align: center; }
    .product-title { color: #1e293b; font-weight: 800; font-size: 1rem; margin-bottom: 3px; }
    .product-price { color: #27ae60; font-weight: 700; font-size: 1.1rem; }
    .product-stock { color: #64748b; font-size: 0.8rem; }
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

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة بيع البضاعة</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    if st.session_state.show_cust_fields:
        with st.expander("✅ تم اعتماد الفاتورة! سجل بيانات الزبون الآن", expanded=True):
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الهاتف")
            if st.button("💾 حفظ البيانات"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                auto_save(); st.session_state.show_cust_fields = False; st.rerun()
            if st.button("⏩ تخطي"): 
                st.session_state.show_cust_fields = False; st.rerun()
    else:
        st.session_state.p_method = st.radio("طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
        search_q = st.text_input("🔍 ابحث عن صنف...")
        bill_items = []
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i.get('قسم') == cat]
            if search_q: items = [i for i in items if search_q in i['item']]
            if items:
                st.markdown(f"<div style='background:#f1f4f6; padding:10px; border-radius:10px; margin:10px 0; border-right:5px solid #27ae60; font-weight:bold;'>📂 {cat}</div>", unsafe_allow_html=True)
                cols = st.columns(3)
                for idx, it in enumerate(items):
                    with cols[idx % 3]:
                        st.markdown(f"<div class='product-card'><div class='product-title'>{it['item']}</div><div class='product-price'>{format_num(it['بيع'])} ₪</div><div class='product-stock'>المتوفر: {format_num(it['كمية'])}</div></div>", unsafe_allow_html=True)
                        m_col, v_col = st.columns([1, 1.2])
                        mode = m_col.selectbox("بـ", ["₪", "كجم"], key=f"m_{it['item']}_{cat}")
                        val = clean_num(v_col.text_input("المقدار", key=f"v_{it['item']}_{cat}"))
                        if val > 0:
                            qty = val if mode == "كجم" else val / it['بيع']
                            bill_items.append({"item": it['item'], "qty": qty, "amount": val if mode == "₪" else val * it['بيع'], "profit": (it['بيع'] - it['شراء']) * qty})
        if st.button("🚀 إتمام واعتماد البيع") and bill_items:
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
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    tab1, tab2, tab3 = st.tabs(["📋 رصيد المخزن الحالي", "⚖️ عملية الجرد الدوري", "🗑️ سجل التوالف"])
    
    with tab1:
        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
        if not my_inv:
            st.info("المخزن فارغ حالياً.")
        else:
            # عرض بطاقات ملخصة للأقسام
            cat_summaries = {}
            for it in my_inv:
                cat = it['قسم']
                cat_summaries[cat] = cat_summaries.get(cat, 0) + (it['شراء'] * it['كمية'])
            
            summ_cols = st.columns(len(cat_summaries))
            for i, (c_name, c_val) in enumerate(cat_summaries.items()):
                summ_cols[i].markdown(f"<div class='inventory-card'><div class='inv-label'>قيمة {c_name}</div><div class='inv-value'>{format_num(c_val)} ₪</div></div>", unsafe_allow_html=True)
            
            st.markdown("### 📝 تفاصيل بضاعة المحل")
            df_display = pd.DataFrame(my_inv)[['item', 'قسم', 'شراء', 'بيع', 'كمية']]
            df_display.columns = ['الصنف', 'القسم', 'سعر الشراء', 'سعر البيع', 'الكمية المتوفرة']
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### ⚖️ تحديث كميات المخزن (الجرد)")
        st.warning("تنبيه: إدخال كمية جديدة سيقوم باستبدال الكمية القديمة في النظام.")
        
        jard_data = []
        for cat in st.session_state.categories:
            cat_items = [i for i in my_inv if i.get('قسم') == cat]
            if cat_items:
                with st.expander(f"جرد قسم: {cat}", expanded=False):
                    for it in cat_items:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{it['item']}** (الحالي: {format_num(it['كمية'])})")
                        new_q = c3.text_input("الكمية الفعلية", key=f"jard_{it['item']}_{st.session_state.my_branch}")
                        if new_q != "":
                            jard_data.append({'item': it['item'], 'new_qty': clean_num(new_q)})
        
        if st.button("💾 اعتماد نتائج الجرد"):
            if jard_data:
                for entry in jard_data:
                    for idx, inv_item in enumerate(st.session_state.inventory):
                        if inv_item['item'] == entry['item'] and inv_item['branch'] == st.session_state.my_branch:
                            st.session_state.inventory[idx]['كمية'] = entry['new_qty']
                auto_save()
                st.success("✅ تم تحديث المخزن بناءً على الجرد الجديد")
                st.rerun()

    with tab3:
        st.markdown("### 🗑️ تسجيل بضاعة تالفة")
        with st.form("waste_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            w_item = col1.selectbox("اختر الصنف التالف", [i['item'] for i in my_inv])
            w_qty = col2.number_input("الكمية التي أُتلفت", min_value=0.0, step=0.1)
            reason = st.text_input("سبب التلف (اختياري)")
            if st.form_submit_button("تسجيل التالف الآن"):
                for idx, inv_item in enumerate(st.session_state.inventory):
                    if inv_item['item'] == w_item and inv_item['branch'] == st.session_state.my_branch:
                        st.session_state.inventory[idx]['كمية'] -= w_qty
                        # إضافة لسجل التوالف
                        new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'branch': st.session_state.my_branch}
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                auto_save()
                st.success(f"✅ تم خصم {w_qty} من {w_item} وتسجيلها تالف")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🗓️ سجل التوالف الأخير")
        waste_view = st.session_state.waste_df[st.session_state.waste_df['branch'] == st.session_state.my_branch]
        if not waste_view.empty:
            st.dataframe(waste_view[['date', 'item', 'qty']].rename(columns={'date':'التاريخ', 'item':'الصنف', 'qty':'الكمية'}), use_container_width=True, hide_index=True)

# باقي الأقسام كما هي
elif menu == "🏪 إدارة الفروع":
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

elif menu == "📊 التقارير المالية" or menu == "📊 التقارير العامة":
    st.markdown("<h1 class='main-title'>📊 التقارير والزبائن</h1>", unsafe_allow_html=True)
    sales = st.session_state.sales_df.copy()
    if active_branch != "كافة الفروع": sales = sales[sales['branch'] == active_branch]
    row = st.columns(3)
    row[0].markdown(f"<div class='metric-box'><div class='metric-label'>المبيعات</div><div class='metric-value'>{format_num(sales['amount'].sum()) if not sales.empty else 0} ₪</div></div>", unsafe_allow_html=True)
    row[1].markdown(f"<div class='metric-box'><div class='metric-label'>صافي الأرباح</div><div class='metric-value'>{format_num(sales['profit'].sum()) if not sales.empty else 0} ₪</div></div>", unsafe_allow_html=True)
    inv_df = pd.DataFrame(st.session_state.inventory)
    if not inv_df.empty and active_branch != "كافة الفروع": inv_df = inv_df[inv_df['branch'] == active_branch]
    total_cap = (inv_df['شراء'] * inv_df['كمية']).sum() if not inv_df.empty else 0
    row[2].markdown(f"<div class='metric-box'><div class='metric-label'>رأس المال الحالي</div><div class='metric-value'>{format_num(total_cap)} ₪</div></div>", unsafe_allow_html=True)
    st.dataframe(sales[['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'branch']].sort_values(by='date', ascending=False), use_container_width=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp", clear_on_submit=True):
        r = st.text_input("البيان"); a = st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()
    st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
    with st.form("add_i", clear_on_submit=True):
        n = st.text_input("اسم الصنف الجديد"); cat = st.selectbox("القسم", st.session_state.categories)
        b = st.text_input("سعر التكلفة (شراء)"); s = st.text_input("سعر البيع"); q = st.text_input("الكمية")
        if st.form_submit_button("➕ إضافة للمخزن"):
            st.session_state.inventory.append({"item": n, "قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q), "branch": st.session_state.my_branch})
            auto_save(); st.success(f"✅ تم إضافة {n}"); st.rerun()
