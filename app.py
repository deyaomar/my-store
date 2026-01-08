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

# --- نظام تسجيل الدخول ---
def get_db_path(): return 'branches_config.csv'

def force_init_db():
    path = get_db_path()
    default_data = [
        {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
        {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
    ]
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        pd.DataFrame(default_data).to_csv(path, index=False, encoding='utf-8-sig')
    return pd.read_csv(path, encoding='utf-8-sig')

# 2. تحميل البيانات والمحافظة على السلة
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = force_init_db()

if 'cart' not in st.session_state:
    st.session_state.cart = []

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
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + (cat_df['name'].tolist() if not cat_df.empty else ["مواد غذائية"])))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)

# 3. التنسيق (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; direction: rtl; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-left: 3px solid #10b981; }
    .sidebar-user { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white !important; font-weight: 900; font-size: 22px; text-align: center; padding: 20px; border-radius: 15px; margin: 10px; }
    .pos-card { background: white; border-radius: 15px; padding: 15px; border-right: 6px solid #10b981; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .cart-style { background: #fffbeb; border: 1px solid #fef3c7; border-radius: 10px; padding: 10px; margin-bottom: 5px; }
    .main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("👤 اسم المستخدم").strip()
        p = st.text_input("🔑 كلمة المرور", type="password").strip()
        if st.form_submit_button("دخول"):
            db = force_init_db()
            m = db[(db['user_name'] == u) & (db['password'] == p)]
            if not m.empty:
                st.session_state.logged_in, st.session_state.user_role = True, m.iloc[0]['role']
                st.session_state.active_user, st.session_state.my_branch = u, m.iloc[0]['branch_name']
                st.rerun()
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)
menu_list = ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"]
menu = st.sidebar.radio("التنقل", menu_list)

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- شاشة البيع الاحترافية ---
if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع الذكية</h1>", unsafe_allow_html=True)
    
    col_main, col_cart = st.columns([2, 1])

    with col_main:
        search = st.text_input("🔍 بحث عن صنف...", placeholder="اكتب اسم المنتج...")
        my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
        
        for idx, it in enumerate(my_inv):
            if not search or search.lower() in it['item'].lower():
                with st.container():
                    st.markdown(f"""<div class='pos-card'><b>{it['item']}</b> | المتوفر: {format_num(it['كمية'])}</div>""", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([1, 1, 0.8])
                    
                    opts = ["وحدة/علبة"]
                    if it.get('سعر_القطعة', 0) > 0: opts.append("تجزئة/فرط")
                    stype = c1.selectbox("النوع", opts, key=f"st_{idx}")
                    
                    val_input = c2.text_input("المبلغ (₪)", key=f"val_{idx}", placeholder="0.0")
                    val = clean_num(val_input)
                    
                    if c3.button("➕ للسلة", key=f"add_{idx}", use_container_width=True):
                        if val > 0:
                            p = it['بيع'] if stype == "وحدة/علبة" else it.get('سعر_القطعة', it['بيع'])
                            qty = (val/p)/20 if (stype=="تجزئة/فرط" and it.get('قسم')=="سجائر") else (val/p)
                            st.session_state.cart.append({
                                'item': it['item'], 'amount': val, 
                                'profit': val - (it['شراء']*qty), 'qty_sub': qty, 'type': stype
                            })
                            st.toast(f"تم إضافة {it['item']}")
                        else:
                            st.error("أدخل مبلغاً")

    with col_cart:
        st.markdown("### 🧺 سلة المشتريات")
        if not st.session_state.cart:
            st.write("السلة فارغة")
        else:
            total_bill = 0
            for i, c_item in enumerate(st.session_state.cart):
                total_bill += c_item['amount']
                st.markdown(f"""<div class='cart-style'><b>{c_item['item']}</b><br>{c_item['amount']} ₪ ({c_item['type']})</div>""", unsafe_allow_html=True)
                if st.button("❌", key=f"del_cart_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            
            st.divider()
            st.success(f"**المجموع: {format_num(total_bill)} ₪**")
            
            if st.button("🚀 اعتماد الفاتورة", use_container_width=True):
                st.session_state.checkout_final = True

    if st.session_state.get('checkout_final'):
        with st.expander("🏁 إنهاء العملية", expanded=True):
            name = st.text_input("اسم الزبون")
            method = st.selectbox("الدفع", ["نقدي", "دين/آجل"])
            if st.button("✅ تأكيد وحفظ"):
                b_id = str(uuid.uuid4())[:8]
                dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                for item in st.session_state.cart:
                    # خصم من المخزن
                    for i, inv in enumerate(st.session_state.inventory):
                        if inv['item'] == item['item'] and inv['branch'] == st.session_state.my_branch:
                            st.session_state.inventory[i]['كمية'] -= item['qty_sub']
                    # تسجيل بيع
                    new_sale = {'date': dt, 'item': item['item'], 'amount': item['amount'], 'profit': item['profit'], 'method': method, 'customer_name': name, 'bill_id': b_id, 'branch': st.session_state.my_branch}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
                
                auto_save()
                st.session_state.cart = []
                st.session_state.checkout_final = False
                st.success("تمت العملية!")
                st.rerun()

# --- قسم المخزن والجرد ---
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🛠️ تعديل وحذف الأصناف", "📋 الجرد اليدوي"])
    with t1:
        for i, it in enumerate(st.session_state.inventory):
            if it.get('branch') == st.session_state.my_branch:
                with st.expander(f"📦 {it['item']} - {format_num(it['كمية'])}"):
                    c1, c2, c3, c4 = st.columns(4)
                    n_n = c1.text_input("الاسم", it['item'], key=f"en_{i}")
                    n_q = c2.text_input("الكمية", format_num(it['كمية']), key=f"eq_{i}")
                    n_b = c3.text_input("شراء", format_num(it['شراء']), key=f"eb_{i}")
                    n_s = c4.text_input("بيع", format_num(it['بيع']), key=f"es_{i}")
                    if st.button("💾 حفظ التعديل", key=f"sv_{i}"):
                        st.session_state.inventory[i].update({'item': n_n, 'كمية': clean_num(n_q), 'شراء': clean_num(n_b), 'بيع': clean_num(n_s)})
                        auto_save(); st.rerun()
                    if st.button("🗑️ حذف نهائي", key=f"dl_{i}"):
                        st.session_state.inventory.pop(i); auto_save(); st.rerun()
    with t2:
        st.subheader("الجرد الفعلي")
        for i, it in enumerate(st.session_state.inventory):
            if it.get('branch') == st.session_state.my_branch:
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{it['item']}** (نظام: {format_num(it['كمية'])})")
                act = c2.text_input("الفعلي", key=f"act_{i}")

# --- الأقسام الأخرى ---
elif menu == "💸 المصروفات":
    with st.form("exp"):
        r, a = st.text_input("السبب"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()

elif menu == "📊 التقارير المالية":
    st.dataframe(st.session_state.sales_df[st.session_state.sales_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "⚙️ إدارة الأصناف":
    with st.form("add"):
        n = st.text_input("اسم الصنف")
        cat = st.selectbox("القسم", st.session_state.categories)
        b, s, p, q = st.text_input("شراء"), st.text_input("بيع"), st.text_input("فرط"), st.text_input("كمية")
        if st.form_submit_button("إضافة"):
            st.session_state.inventory.append({'item': n, 'قسم': cat, 'شراء': clean_num(b), 'بيع': clean_num(s), 'كمية': clean_num(q), 'branch': st.session_state.my_branch, 'سعر_القطعة': clean_num(p)})
            auto_save(); st.rerun()

elif menu == "👤 ملفي الشخصي":
    st.write(f"المستخدم: {st.session_state.active_user}")
