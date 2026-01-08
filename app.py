import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل - غزة 2026", layout="wide", page_icon="👑")

# دالات التنظيف والحساب
def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 3)) # زيادة الدقة لـ 3 أرقام للأوزان الصغيرة
    except: return str(val)

def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

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

if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

# ملفات البيانات
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value', 'branch'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        st.session_state[state_key] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    # أضفنا عمود 'نوع_الوحدة' وعمود 'سعر_القطعة'
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية', 'نوع_الوحدة', 'سعر_القطعة'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = cat_df['name'].tolist() if not cat_df.empty else ["سجائر", "دخان عربي", "بهارات", "ألبان"]

if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول (مختصرة)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔑 تسجيل الدخول</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("المستخدم").strip()
        p = st.text_input("كلمة المرور", type="password").strip()
        if st.form_submit_button("دخول"):
            if u == "أبو عمر" and p == "admin":
                st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                st.session_state.my_branch = "الإدارة"
                st.rerun()
            else: st.error("خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية
menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "⚙️ إدارة الأصناف", "📊 التقارير", "🏪 إدارة الفروع"])

if menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف (نظام غزة)</h1>", unsafe_allow_html=True)
    
    if st.session_state.user_role == "admin":
        branch_list = pd.read_csv(get_db_path())['branch_name'].tolist()
        target_branch = st.selectbox("🏬 اختيار الفرع:", branch_list)
    else: target_branch = st.session_state.my_branch

    t_add, t_edit = st.tabs(["➕ إضافة بضاعة", "📝 جرد وتعديل"])
    
    with t_add:
        with st.form("add_form", clear_on_submit=True):
            n = st.text_input("اسم الصنف (مثلاً: مالبورو الأحمر أو بهار بني)")
            cat = st.selectbox("القسم", st.session_state.categories)
            u_type = st.selectbox("وحدة البيع الكبرى", ["علبة", "كيلو", "قطعة"])
            
            col1, col2 = st.columns(2)
            buy_price = col1.text_input(f"سعر شراء ({u_type})")
            sell_price = col2.text_input(f"سعر بيع ({u_type})")
            
            st.markdown("---")
            st.write("🎯 **نظام التجزئة (للسجائر بالسيجارة أو البهارات بالغرام)**")
            has_sub = st.checkbox("تفعيل البيع بالتجزئة (سيجارة/غرام)")
            sub_price = st.text_input("سعر بيع الوحدة الصغيرة (مثلاً سعر السيجارة الواحدة)", value="0.0")
            
            qty = st.text_input(f"الكمية المتوفرة بـ ({u_type})")
            
            if st.form_submit_button("➕ حفظ الصنف"):
                st.session_state.inventory.append({
                    "item": n, "قسم": cat, "شراء": clean_num(buy_price), 
                    "بيع": clean_num(sell_price), "كمية": clean_num(qty), 
                    "branch": target_branch, "نوع_الوحدة": u_type,
                    "سعر_القطعة": clean_num(sub_price) if has_sub else 0
                })
                auto_save(); st.success("تم الحفظ!"); st.rerun()

    with t_edit:
        branch_inv = [i for i in st.session_state.inventory if i.get('branch') == target_branch]
        if branch_inv:
            df_edit = pd.DataFrame(branch_inv)
            edited = st.data_editor(df_edit[['item', 'قسم', 'نوع_الوحدة', 'شراء', 'بيع', 'سعر_القطعة', 'كمية']], use_container_width=True)
            if st.button("💾 حفظ التعديلات"):
                # تحديث منطقي للحفظ
                new_inv = [i for i in st.session_state.inventory if i.get('branch') != target_branch]
                for _, row in edited.iterrows():
                    new_inv.append({**row.to_dict(), "branch": target_branch})
                st.session_state.inventory = new_inv
                auto_save(); st.success("تم التحديث"); st.rerun()

elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    search = st.text_input("🔍 ابحث عن صنف (سجائر، بهار، إلخ)...")
    
    bill_items = []
    for it in my_inv:
        if search.lower() in it['item'].lower():
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{it['item']}** ({it['قسم']})")
                
                # اختيار طريقة البيع
                options = [f"بالـ {it['نوع_الوحدة']}"]
                if it['سعر_القطعة'] > 0:
                    sub_unit = "سيجارة" if it['نوع_الوحدة'] == "علبة" else "غرام/أخرى"
                    options.append(f"بالـ {sub_unit}")
                
                sell_type = c2.selectbox("البيع بـ", options, key=f"type_{it['item']}")
                amount_in_shekel = clean_num(c3.text_input("المبلغ (₪)", key=f"p_{it['item']}"))
                
                if amount_in_shekel > 0:
                    # حساب الكمية المخصومة
                    if "بالـ العلبة" in sell_type or "بالـ كيلو" in sell_type or "بالـ قطعة" in sell_type:
                        qty_to_deduct = amount_in_shekel / it['بيع']
                        profit = (it['بيع'] - it['شراء']) * qty_to_deduct
                    else:
                        # بيع بالتجزئة (سيجارة مثلاً)
                        qty_to_deduct = (amount_in_shekel / it['سعر_القطعة']) / (20 if it['نوع_الوحدة'] == "علبة" else 1000)
                        # الربح في التجزئة غالباً أعلى
                        profit = amount_in_shekel - (it['شراء'] / (20 if it['نوع_الوحدة'] == "علبة" else 1000) * (amount_in_shekel / it['سعر_القطعة']))
                    
                    bill_items.append({"item": it['item'], "qty": qty_to_deduct, "amount": amount_in_shekel, "profit": profit})

    if st.button("🚀 اعتماد البيع") and bill_items:
        for e in bill_items:
            for idx, inv_item in enumerate(st.session_state.inventory):
                if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                    st.session_state.inventory[idx]['كمية'] -= e['qty']
            new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': 'نقداً', 'customer_name': 'عام', 'customer_phone': '', 'bill_id': str(uuid.uuid4())[:8], 'branch': st.session_state.my_branch}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
        auto_save(); st.success("تمت عملية البيع بنجاح!"); st.rerun()

# (باقي الأقسام كالفروع والتقارير تبقى كما هي في الكود السابق)
