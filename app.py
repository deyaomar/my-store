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
        text_str = str(text).replace(',', '.').replace('،', '.')
        return float(text_str)
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

# 3. التصميم (CSS الأصلي)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-left: 2px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; margin-bottom: 25px; border-bottom: 2px solid #334155; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 دخول النظام</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("👤 المستخدم").strip()
        p = st.text_input("🔑 المرور", type="password").strip()
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

# --- إدارة الأصناف (التبويبات الثلاثة) ---
if menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
    target_branch = st.session_state.my_branch
    
    t1, t2, t3 = st.tabs(["➕ إضافة بضاعة", "🛠️ تعديل الكميات", "📂 إدارة الأقسام"])

    with t1:
        # ملاحظة: اختيار القسم هنا يغير الحقول بالأسفل
        sel_cat = st.selectbox("اختار القسم:", st.session_state.categories, key="cat_selector_unique")
        
        with st.form("form_add_v2", clear_on_submit=True):
            if sel_cat == "سجائر":
                st.warning("🚬 نظام السجائر: أدخل العلب والفرط بشكل منفصل")
                item_name = st.text_input("اسم الدخان")
                c_col1, c_col2 = st.columns(2)
                v_boxes = c_col1.text_input("عدد العلب الكاملة", value="0")
                v_singles = c_col2.text_input("عدد السجائر الفرط (إضافي)", value="0")
                v_buy = st.text_input("سعر تكلفة العلبة الواحدة")
                v_sell = st.text_input("سعر بيع العلبة كاملة")
                v_single_sell = st.text_input("سعر بيع السيجارة الواحدة")
            else:
                item_name = st.text_input("اسم الصنف")
                v_boxes = st.text_input("الكمية")
                v_singles = "0"
                v_buy = st.text_input("سعر الشراء")
                v_sell = st.text_input("سعر البيع")
                v_single_sell = "0"

            if st.form_submit_button("إضافة للصنف"):
                if item_name:
                    # حساب الكمية: كل سيجارة هي 1/20 من العلبة
                    final_q = clean_num(v_boxes) + (clean_num(v_singles) / 20)
                    st.session_state.inventory.append({
                        "item": item_name, "قسم": sel_cat, "شراء": clean_num(v_buy), 
                        "بيع": clean_num(v_sell), "كمية": final_q, 
                        "branch": target_branch, "سعر_القطعة": clean_num(v_single_sell)
                    })
                    auto_save(); st.success(f"تمت إضافة {item_name}"); st.rerun()

    with t2:
        br_data = [i for i in st.session_state.inventory if i.get('branch') == target_branch]
        if br_data:
            df_edit = st.data_editor(pd.DataFrame(br_data)[['item', 'قسم', 'شراء', 'بيع', 'سعر_القطعة', 'كمية']], use_container_width=True, key="inventory_editor")
            if st.button("حفظ التعديلات النهائية"):
                new_inv = [i for i in st.session_state.inventory if i.get('branch') != target_branch]
                for _, row in df_edit.iterrows():
                    new_inv.append({**row.to_dict(), "branch": target_branch})
                st.session_state.inventory = new_inv
                auto_save(); st.success("تم التحديث بنجاح"); st.rerun()

    with t3:
        st.subheader("إدارة أقسام المحل")
        with st.form("cat_form_v2", clear_on_submit=True):
            new_cat_name = st.text_input("اسم القسم الجديد")
            if st.form_submit_button("إضافة القسم"):
                if new_cat_name and new_cat_name not in st.session_state.categories:
                    st.session_state.categories.append(new_cat_name); auto_save(); st.rerun()
        
        for cat in st.session_state.categories:
            cc1, cc2 = st.columns([5,1])
            cc1.write(f"📂 {cat}")
            if cat != "سجائر": # السجائر قسم أساسي لا يحذف
                if cc2.button("حذف", key=f"del_{cat}"):
                    st.session_state.categories.remove(cat); auto_save(); st.rerun()

# --- بقية الأقسام (البيع والمخزن) ---
elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 نقطة البيع</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    search_q = st.text_input("🔍 ابحث عن صنف...")
    bill = []
    for it in my_inv:
        if not search_q or search_q.lower() in it['item'].lower():
            with st.container():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{it['item']}**")
                is_cig = it.get('سعر_القطعة', 0) > 0
                sale_type = c2.selectbox("النوع", ["كاملة", "تجزئة/فرط"] if is_cig else ["كاملة"], key=f"sale_{it['item']}")
                money = clean_num(c3.text_input("المبلغ ₪", key=f"pr_{it['item']}"))
                if money > 0:
                    if sale_type == "تجزئة/فرط":
                        qty_sold = (money / it['سعر_القطعة']) / 20 if it['قسم'] == "سجائر" else (money / it['سعر_القطعة'])
                        cost = (it['شراء'] / 20) if it['قسم'] == "سجائر" else it['شراء']
                        prof = money - (cost * (money / it['سعر_القطعة']))
                    else:
                        qty_sold = money / it['بيع']; prof = (it['بيع'] - it['شراء']) * qty_sold
                    bill.append({"item": it['item'], "qty": qty_sold, "amount": money, "profit": prof})
    
    if st.button("🚀 تأكيد البيع") and bill:
        for b_item in bill:
            for idx, inv_item in enumerate(st.session_state.inventory):
                if inv_item['item'] == b_item['item'] and inv_item['branch'] == st.session_state.my_branch:
                    st.session_state.inventory[idx]['كمية'] -= b_item['qty']
            new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': b_item['item'], 'amount': b_item['amount'], 'profit': b_item['profit'], 'method': 'نقداً', 'customer_name': 'عام', 'customer_phone': '', 'bill_id': str(uuid.uuid4())[:8], 'branch': st.session_state.my_branch}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
        auto_save(); st.success("✅ تم تسجيل البيع"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 بضاعة المحل</h1>", unsafe_allow_html=True)
    st.table(pd.DataFrame([i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]))

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df[st.session_state.sales_df['branch'] == st.session_state.my_branch]
    st.metric("صافي مبيعاتك اليوم", f"{format_num(s_df['amount'].sum())} ₪")
    st.dataframe(s_df)
