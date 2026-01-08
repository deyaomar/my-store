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

# 2. تحميل البيانات
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = force_init_db()

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
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + (cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات"])))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم المطور (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; direction: rtl; background-color: #f1f5f9; }
    
    /*Sidebar*/
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-left: 3px solid #10b981; }
    .sidebar-user { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white !important; font-weight: 900; font-size: 22px; text-align: center; padding: 20px; border-radius: 15px; margin: 10px; }
    
    /* POS Professional Cards */
    .pos-card {
        background: white;
        border-radius: 18px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .pos-card:hover { border-color: #10b981; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .pos-item-name { font-size: 20px; font-weight: 900; color: #1e293b; margin-bottom: 8px; }
    .pos-item-meta { font-size: 14px; color: #64748b; margin-bottom: 15px; }
    .pos-price-tag { background: #ecfdf5; color: #065f46; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; }
    
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
if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
else:
    menu = st.sidebar.radio("التنقل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])

# --- شاشة البيع الاحترافية ---
if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 نقطة البيع العالمية</h1>", unsafe_allow_html=True)
    
    c_search, c_cat = st.columns([2, 1])
    search = c_search.text_input("🔍 ابحث عن اسم المنتج هنا...", placeholder="مثال: مالبورو، تفاح...")
    cat_filter = c_cat.selectbox("📂 تصفية حسب القسم", ["الكل"] + st.session_state.categories)
    
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    current_bill = []

    # عرض المنتجات بنظام احترافي
    cols = st.columns(2) # توزيع المنتجات على عمودين لشكل أرتب
    for idx, it in enumerate(my_inv):
        if (not search or search.lower() in it['item'].lower()) and (cat_filter == "الكل" or it.get('قسم') == cat_filter):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="pos-card">
                    <div class="pos-item-name">{it['item']}</div>
                    <div class="pos-item-meta">
                        <span class="pos-price-tag">سعر البيع: {format_num(it['بيع'])} ₪</span>
                        <span style="margin-right:10px;">📦 المتوفر: {format_num(it['كمية'])}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_type, col_val = st.columns([1, 1])
                opts = ["وحدة/علبة"]
                if it.get('سعر_القطعة', 0) > 0: opts.append("تجزئة/فرط")
                
                stype = col_type.selectbox("اختر النوع", opts, key=f"pos_st_{idx}")
                val = clean_num(col_val.text_input("المبلغ (₪)", key=f"pos_v_{idx}", placeholder="0.00"))
                
                if val > 0:
                    p = it['بيع'] if stype == "وحدة/علبة" else it.get('سعر_القطعة', it['بيع'])
                    qty = (val/p)/20 if (stype=="تجزئة/فرط" and it.get('قسم')=="سجائر") else (val/p)
                    current_bill.append({'item': it['item'], 'amount': val, 'profit': val - (it['شراء']*qty), 'qty_sub': qty})
                st.write("---")

    if current_bill:
        total = sum(b['amount'] for b in current_bill)
        st.markdown(f"### 🧾 إجمالي الفاتورة: {format_num(total)} ₪")
        if st.button("🚀 إتمام العملية الآن", use_container_width=True):
            st.session_state.checkout_final = True

    if st.session_state.get('checkout_final'):
        with st.expander("📝 تسجيل بيانات الزبون وطريقة الدفع", expanded=True):
            c1, c2 = st.columns(2)
            c_name = c1.text_input("اسم الزبون (اختياري)")
            c_method = c2.selectbox("طريقة الدفع", ["نقدي", "دين/آجل"])
            if st.button("✅ حفظ الفاتورة"):
                dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                b_id = str(uuid.uuid4())[:8]
                for b in current_bill:
                    for i, inv in enumerate(st.session_state.inventory):
                        if inv['item'] == b['item'] and inv['branch'] == st.session_state.my_branch:
                            st.session_state.inventory[i]['كمية'] -= b['qty_sub']
                    new_sale = {'date': dt, 'item': b['item'], 'amount': b['amount'], 'profit': b['profit'], 'method': c_method, 'customer_name': c_name, 'bill_id': b_id, 'branch': st.session_state.my_branch}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
                auto_save(); st.session_state.checkout_final = False; st.success("تم البيع بنجاح!"); st.balloons(); st.rerun()

# --- قسم المخزن والجرد (كما طلبته) ---
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🛠️ تعديل وحذف الأصناف", "📋 الجرد اليدوي"])
    with t1:
        for i, it in enumerate(st.session_state.inventory):
            if it.get('branch') == st.session_state.my_branch:
                with st.expander(f"📦 {it['item']} - الكمية: {format_num(it['كمية'])}"):
                    c1, c2, c3, c4 = st.columns(4)
                    n_n = c1.text_input("الاسم", it['item'], key=f"e_n_{i}")
                    n_q = c2.text_input("الكمية", format_num(it['كمية']), key=f"e_q_{i}")
                    n_b = c3.text_input("شراء", format_num(it['شراء']), key=f"e_b_{i}")
                    n_s = c4.text_input("بيع", format_num(it['بيع']), key=f"e_s_{i}")
                    if st.button("💾 حفظ", key=f"e_sv_{i}"):
                        st.session_state.inventory[i].update({'item': n_n, 'كمية': clean_num(n_q), 'شراء': clean_num(n_b), 'بيع': clean_num(n_s)})
                        auto_save(); st.rerun()
                    if st.button("🗑️ حذف", key=f"e_dl_{i}"):
                        st.session_state.inventory.pop(i); auto_save(); st.rerun()
    with t2:
        st.subheader("الجرد الفعلي")
        for i, it in enumerate(st.session_state.inventory):
            if it.get('branch') == st.session_state.my_branch:
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{it['item']}** (نظام: {format_num(it['كمية'])})")
                act = c2.text_input("الفعلي", key=f"act_p_{i}")

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r, a = st.text_input("البيان"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()

elif menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير - {st.session_state.my_branch}</h1>", unsafe_allow_html=True)
    st.dataframe(st.session_state.sales_df[st.session_state.sales_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إضافة صنف</h1>", unsafe_allow_html=True)
    with st.form("add_new"):
        n = st.text_input("الاسم")
        cat = st.selectbox("القسم", st.session_state.categories)
        b, s, p, q = st.text_input("شراء"), st.text_input("بيع"), st.text_input("فرط"), st.text_input("كمية")
        if st.form_submit_button("إضافة"):
            st.session_state.inventory.append({'item': n, 'قسم': cat, 'شراء': clean_num(b), 'بيع': clean_num(s), 'كمية': clean_num(q), 'branch': st.session_state.my_branch, 'سعر_القطعة': clean_num(p)})
            auto_save(); st.rerun()

elif menu == "👤 ملفي الشخصي":
    st.markdown("<h1 class='main-title'>👤 حسابي</h1>", unsafe_allow_html=True)
    st.write(f"المستخدم: {st.session_state.active_user}")
