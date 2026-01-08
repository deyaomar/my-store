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

def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try: return pd.read_csv(file_path, encoding='utf-8-sig')
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# --- نظام تسجيل الدخول المحسن ---
def get_db_path(): return 'branches_config.csv'

def force_init_db():
    path = get_db_path()
    # البيانات الافتراضية الصارمة
    default_data = [
        {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
        {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
    ]
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        pd.DataFrame(default_data).to_csv(path, index=False, encoding='utf-8-sig')
    return pd.read_csv(path, encoding='utf-8-sig')

# 2. تحميل البيانات الأساسية
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = force_init_db()

if 'pos_cart' not in st.session_state:
    st.session_state.pos_cart = []

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
    st.session_state.categories = ["سجائر", "خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)

# 3. التصميم
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; direction: rtl; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-left: 3px solid #10b981; }
    .sidebar-user { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white !important; font-weight: 900; font-size: 22px; text-align: center; padding: 20px; border-radius: 15px; margin: 10px; }
    .main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .cart-box { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; margin-bottom: 10px; border-right: 5px solid #10b981; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة تسجيل الدخول (تم الإصلاح هنا)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        u = st.text_input("👤 اسم المستخدم (أبو عمر)").strip()
        p = st.text_input("🔑 كلمة المرور", type="password").strip()
        
        if st.form_submit_button("دخول"):
            # التحقق اليدوي المباشر كحل احتياطي
            if (u == "أبو عمر" and p == "admin") or (u == "admin" and p == "123"):
                role = "admin" if u == "أبو عمر" else "shop"
                branch = "المدير العام" if u == "أبو عمر" else "المحل الرئيسي"
                st.session_state.update({"logged_in": True, "user_role": role, "active_user": u, "my_branch": branch})
                st.rerun()
            else:
                # التحقق من قاعدة البيانات
                db = force_init_db()
                m = db[(db['user_name'] == u) & (db['password'] == p)]
                if not m.empty:
                    st.session_state.update({
                        "logged_in": True, "user_role": m.iloc[0]['role'],
                        "active_user": u, "my_branch": m.iloc[0]['branch_name']
                    })
                    st.rerun()
                else:
                    st.error("❌ عذراً.. تأكد من اسم المستخدم وكلمة المرور")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.sidebar.selectbox("تصفية الفرع:", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("التنقل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- الصفحات ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 نقطة البيع</h1>", unsafe_allow_html=True)
    col_products, col_cart = st.columns([1.8, 1.2])
    
    with col_products:
        search = st.text_input("🔍 بحث عن صنف...")
        my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
        for idx, it in enumerate(my_inv):
            if not search or search.lower() in it['item'].lower():
                with st.container():
                    st.markdown(f"<div style='background:#f1f5f9; padding:10px; border-radius:8px; margin-bottom:5px;'><b>{it['item']}</b> | متوفر: {format_num(it['كمية'])}</div>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([1, 1, 0.5])
                    opts = ["علبة/قطعة", "فرط/تجزئة"] if it.get('سعر_القطعة', 0) > 0 else ["علبة/قطعة"]
                    m = c1.selectbox("النوع", opts, key=f"m_{idx}")
                    v = c2.text_input("المبلغ ₪", key=f"v_{idx}")
                    if c3.button("➕", key=f"add_{idx}"):
                        val = clean_num(v)
                        if val > 0:
                            p = it['بيع'] if m == "علبة/قطعة" else it.get('سعر_القطعة', it['بيع'])
                            q = (val/p)/20 if (m=="فرط/تجزئة" and it.get('قسم')=="سجائر") else (val/p)
                            st.session_state.pos_cart.append({"item": it['item'], "qty": q, "amount": val, "profit": val - (it['شراء']*q), "type": m})
                            st.rerun()

    with col_cart:
        st.subheader("🧺 السلة")
        total = 0
        for i, item in enumerate(st.session_state.pos_cart):
            total += item['amount']
            st.markdown(f"<div class='cart-box'>{item['item']} - {item['amount']} ₪</div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.pos_cart.pop(i); st.rerun()
        st.success(f"الإجمالي: {format_num(total)} ₪")
        if st.session_state.pos_cart and st.button("🚀 تنفيذ البيع"):
            dt, b_id = datetime.now().strftime("%Y-%m-%d %H:%M"), str(uuid.uuid4())[:8]
            for entry in st.session_state.pos_cart:
                for i, inv in enumerate(st.session_state.inventory):
                    if inv['item'] == entry['item'] and inv['branch'] == st.session_state.my_branch:
                        st.session_state.inventory[i]['كمية'] -= entry['qty']
                new_s = {'date': dt, 'item': entry['item'], 'amount': entry['amount'], 'profit': entry['profit'], 'branch': st.session_state.my_branch, 'method': 'نقدي', 'bill_id': b_id}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            auto_save(); st.session_state.pos_cart = []; st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 جرد المخزن</h1>", unsafe_allow_html=True)
    st.table(pd.DataFrame([i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]))

elif menu == "💸 المصروفات":
    with st.form("exp"):
        r, a = st.text_input("البيان"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()

elif menu == "📊 التقارير المالية":
    st.dataframe(st.session_state.sales_df[st.session_state.sales_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "⚙️ إدارة الأصناف":
    with st.form("add_item"):
        n = st.text_input("اسم الصنف")
        cat = st.selectbox("القسم", st.session_state.categories)
        b, s, q = st.text_input("شراء"), st.text_input("بيع"), st.text_input("كمية")
        if st.form_submit_button("إضافة"):
            st.session_state.inventory.append({"item": n, "قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q), "branch": st.session_state.my_branch})
            auto_save(); st.rerun()

elif menu == "👤 ملفي الشخصي":
    st.write(f"المستخدم الحالي: {st.session_state.active_user}")
