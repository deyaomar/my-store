import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📊")

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

# 2. إدارة قواعد البيانات (المحلات والمستخدمين)
if 'branches_db' not in st.session_state:
    if os.path.exists('branches_config.csv'):
        st.session_state.branches_db = pd.read_csv('branches_config.csv')
    else:
        st.session_state.branches_db = pd.DataFrame([{'branch_name': 'المحل الأول', 'user_name': 'user1', 'password': '123'}])

# إدارة ملفات البيانات (معدلة لتدعم الفروع)
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value', 'branch']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value', 'branch'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        if os.path.exists(file):
            df = pd.read_csv(file)
            for c in cols: 
                if c not in df.columns: df[c] = 0.0 if any(x in c for x in ['amount', 'profit', 'loss', 'qty']) else ""
            st.session_state[state_key] = df
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv('inventory_final.csv').to_dict('records') if os.path.exists('inventory_final.csv') else []
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    st.session_state.branches_db.to_csv('branches_config.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق (الستايل المعتمد)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 15px; margin-bottom: 25px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام تسجيل الدخول المحمي
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    u_in = st.text_input("اسم المستخدم")
    p_in = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u_in == "أبو عمر" and p_in == "admin":
            st.session_state.logged_in = True
            st.session_state.user_role = "admin"
            st.session_state.active_user = "أبو عمر"
            st.rerun()
        else:
            db = st.session_state.branches_db
            match = db[(db['user_name'] == u_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = "shop"
                st.session_state.my_branch = match.iloc[0]['branch_name']
                st.session_state.active_user = u_in
                st.rerun()
            else: st.error("خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية والتحكم بالفروع
role = st.session_state.user_role
user_name = st.session_state.active_user
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {user_name} 👋</div>", unsafe_allow_html=True)

if role == "admin":
    b_list = ["الكل"] + st.session_state.branches_db['branch_name'].tolist()
    active_branch = st.sidebar.selectbox("تبديل المحل:", b_list)
    menu_options = ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "🏗️ إدارة المحلات", "⚙️ الإعدادات"]
else:
    active_branch = st.session_state.my_branch
    menu_options = ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية"]

menu = st.sidebar.radio("التنقل السريع", menu_options)

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# --- 1. نقطة البيع (كود أبو عمر المدمج) ---
if menu == "🛒 نقطة البيع":
    st.markdown(f"<h1 class='main-title'>🛒 بيع بضاعة - {active_branch}</h1>", unsafe_allow_html=True)
    if active_branch == "الكل":
        st.warning("يرجى اختيار فرع محدد من القائمة الجانبية للبيع")
    else:
        # (نفس منطق الكود الأصلي الخاص بك مع فلترة الفرع)
        search_q = st.text_input("🔍 ابحث عن صنف...")
        bill_items = []
        inv_filtered = [i for i in st.session_state.inventory if i.get('branch') == active_branch]
        
        for cat in st.session_state.categories:
            items = [i for i in inv_filtered if i.get('قسم') == cat]
            if search_q: items = [i for i in items if search_q in i['item']]
            if items:
                with st.expander(f"📂 {cat}", expanded=True):
                    for data in items:
                        c1, c2, c3 = st.columns([2, 1, 2])
                        c1.markdown(f"**{data['item']}**\n<small>متوفر: {format_num(data['كمية'])}</small>", unsafe_allow_html=True)
                        mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{data['item']}_{active_branch}")
                        val = clean_num(c3.text_input("المقدار", key=f"v_{data['item']}_{active_branch}"))
                        if val > 0:
                            qty = val if mode == "كجم" else val / data["بيع"]
                            bill_items.append({"item": data["item"], "qty": qty, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * qty, "cat": cat})
        
        if st.button("🚀 إتمام البيع", type="primary") and bill_items:
            b_id = str(uuid.uuid4())[:8]
            for e in bill_items:
                for i in st.session_state.inventory:
                    if i['item'] == e['item'] and i['branch'] == active_branch: i['qty'] -= e['qty']
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': 'نقدي', 'branch': active_branch, 'bill_id': b_id, 'cat': e['cat']}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            auto_save(); st.success("تم الحفظ!"); st.rerun()

# --- 2. إدارة المحلات (للمدير فقط) ---
elif menu == "🏗️ إدارة المحلات":
    st.markdown("<h1 class='main-title'>🏗️ إدارة الفروع والمستخدمين</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("إضافة فرع جديد")
        nb = st.text_input("اسم المحل")
        nu = st.text_input("اسم المستخدم")
        np = st.text_input("كلمة المرور")
        if st.button("حفظ الفرع"):
            new_r = {'branch_name': nb, 'user_name': nu, 'password': np}
            st.session_state.branches_db = pd.concat([st.session_state.branches_db, pd.DataFrame([new_r])], ignore_index=True)
            auto_save(); st.success("تم!"); st.rerun()
    with c2:
        st.subheader("المحلات المسجلة")
        st.dataframe(st.session_state.branches_db, use_container_width=True)

# (تكملة باقي الأقسام: التقارير، المخزن، المصروفات تتبع نفس منطق كودك الأصلي مع فلترة active_branch)
elif menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 تقارير {active_branch}</h1>", unsafe_allow_html=True)
    # استخدم كود التقارير الذي أرسلته أنت هنا مع فلترة Sales_df بالفرع
    s_df = st.session_state.sales_df.copy()
    if active_branch != "الكل": s_df = s_df[s_df['branch'] == active_branch]
    st.write(f"إجمالي مبيعات الفرع: {format_num(s_df['amount'].sum())} ₪")
