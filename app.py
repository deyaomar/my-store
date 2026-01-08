import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

# دالات التنسيق
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

# --- نظام الحماية المباشر ---
def get_db_path(): return 'branches_config.csv'

# 2. تحميل البيانات
if 'branches_db' not in st.session_state:
    if not os.path.exists(get_db_path()):
        df = pd.DataFrame([
            {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
            {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
        ])
        df.to_csv(get_db_path(), index=False, encoding='utf-8-sig')
    st.session_state.branches_db = pd.read_csv(get_db_path(), encoding='utf-8-sig')

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id', 'branch']),
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
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False, encoding='utf-8-sig')
    st.session_state.sales_df.to_csv('sales_final.csv', index=False, encoding='utf-8-sig')
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False, encoding='utf-8-sig')

# 3. التصميم (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; direction: rtl; }
    .main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding: 10px; font-weight: 900; }
    .sidebar-user { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white; padding: 20px; border-radius: 15px; text-align: center; margin: 10px; font-weight: bold; }
    .sale-card { background: #f8fafc; padding: 15px; border-radius: 12px; border-right: 6px solid #10b981; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول (حل نهائي)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("👤 اسم المستخدم").strip()
        p = st.text_input("🔑 كلمة المرور", type="password").strip()
        
        if st.button("دخول النظام"):
            # فحص مباشر لتجاوز أي مشاكل في الملفات
            if (u in ["أبو عمر", "ابو عمر"] and p == "admin"):
                st.session_state.update({"logged_in": True, "user_role": "admin", "active_user": "أبو عمر", "my_branch": "المدير العام"})
                st.rerun()
            elif (u == "admin" and p == "123"):
                st.session_state.update({"logged_in": True, "user_role": "shop", "active_user": "المحل", "my_branch": "المحل الرئيسي"})
                st.rerun()
            else:
                st.error("❌ خطأ في البيانات.. جرب المستخدم: أبو عمر والباسورد: admin")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل", ["📊 التقارير العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف"])
    active_branch = st.sidebar.selectbox("تصفية حسب الفرع:", ["كافة الفروع", "المدير العام", "المحل الرئيسي"])
else:
    menu = st.sidebar.radio("التنقل", ["🛒 نقطة البيع", "📦 المخزن", "💸 المصروفات", "📊 التقارير"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 خروج"):
    st.session_state.clear(); st.rerun()

# --- الأقسام ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    search = st.text_input("🔍 بحث...")
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    current_bill = []
    for it in my_inv:
        if not search or search.lower() in it['item'].lower():
            with st.container():
                st.markdown(f"<div class='sale-card'>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{it['item']}** (متوفر: {format_num(it['كمية'])})")
                stype = c2.selectbox("النوع", ["علبة", "فرط"], key=f"s_{it['item']}")
                amt = clean_num(c3.text_input("المبلغ ₪", key=f"a_{it['item']}"))
                if amt > 0:
                    p = it['بيع'] if stype == "علبة" else it.get('سعر_القطعة', it['بيع'])
                    q = (amt/p)/20 if (stype=="فرط" and it.get('قسم')=="سجائر") else (amt/p)
                    current_bill.append({'item': it['item'], 'amount': amt, 'profit': amt - (it['شراء']*q), 'qty': q})
                st.markdown("</div>", unsafe_allow_html=True)

    if current_bill and st.button("🚀 تأكيد البيع"):
        dt, b_id = datetime.now().strftime("%Y-%m-%d %H:%M"), str(uuid.uuid4())[:8]
        for b in current_bill:
            for i, inv in enumerate(st.session_state.inventory):
                if inv['item'] == b['item'] and inv['branch'] == st.session_state.my_branch:
                    st.session_state.inventory[i]['كمية'] -= b['qty']
            new_s = {'date': dt, 'item': b['item'], 'amount': b['amount'], 'profit': b['profit'], 'branch': st.session_state.my_branch, 'bill_id': b_id}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
        auto_save(); st.success("تم البيع بنجاح"); st.rerun()

elif menu in ["📊 التقارير العامة", "📊 التقارير"]:
    st.markdown(f"<h1 class='main-title'>📊 التقارير - {active_branch}</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df.copy()
    if active_branch != "كافة الفروع": s_df = s_df[s_df['branch'] == active_branch]
    st.metric("إجمالي المبيعات", f"{format_num(s_df['amount'].sum())} ₪")
    st.dataframe(s_df, use_container_width=True)

elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إضافة صنف جديد</h1>", unsafe_allow_html=True)
    with st.form("add"):
        n = st.text_input("الاسم")
        b, s, q = st.text_input("شراء"), st.text_input("بيع"), st.text_input("كمية")
        if st.form_submit_button("حفظ"):
            st.session_state.inventory.append({"item": n, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q), "branch": st.session_state.my_branch})
            auto_save(); st.success("تم"); st.rerun()

elif menu == "📦 المخزن":
    st.table(pd.DataFrame([i for i in st.session_state.inventory if i['branch'] == st.session_state.my_branch]))

elif menu == "💸 المصروفات":
    r = st.text_input("السبب")
    a = st.number_input("المبلغ")
    if st.button("حفظ المصروف"):
        new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}
        st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
        auto_save(); st.rerun()
