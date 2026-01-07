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

# 2. إدارة ملفات البيانات (توزيع الفروع)
if 'branches_db' not in st.session_state:
    if os.path.exists('branches_config.csv'):
        st.session_state.branches_db = pd.read_csv('branches_config.csv')
    else:
        st.session_state.branches_db = pd.DataFrame([{'branch_name': 'المحل الأول', 'user_name': 'user1', 'password': '123'}])

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
    if os.path.exists('inventory_final.csv'):
        # تحويل CSV إلى قائمة ديكشنري لتسهيل التعامل مع الفروع
        st.session_state.inventory = pd.read_csv('inventory_final.csv').to_dict('records')
    else:
        st.session_state.inventory = []

if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

# حالات التشغيل
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    st.session_state.branches_db.to_csv('branches_config.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. واجهة المستخدم (التنسيق الأصلي)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 26px; text-align: center; margin-bottom: 25px; border-bottom: 3px solid #27ae60; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام تسجيل الدخول المطور
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    col_log, _ = st.columns([1, 1])
    with col_log:
        u_in = st.text_input("اسم المستخدم")
        p_in = st.text_input("كلمة المرور", type="password")
        if st.button("دخول النظام"):
            # دخول المدير
            if u_in == "أبو عمر" and p_in == "admin":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.active_user = "أبو عمر"
                st.rerun()
            # دخول أصحاب المحلات
            else:
                db = st.session_state.branches_db
                match = db[(db['user_name'] == u_in) & (db['password'] == p_in)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "shop"
                    st.session_state.my_branch = match.iloc[0]['branch_name']
                    st.session_state.active_user = u_in
                    st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# 5. القائمة الجانبية (بعد الدخول)
role = st.session_state.user_role
user_name = st.session_state.active_user
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {user_name} 👋</div>", unsafe_allow_html=True)

if role == "admin":
    b_list = ["الكل"] + st.session_state.branches_db['branch_name'].tolist()
    active_branch = st.sidebar.selectbox("🏠 عرض فرع:", b_list)
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "🏗️ إدارة المحلات", "⚙️ الإعدادات"])
else:
    active_branch = st.session_state.my_branch
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية"])

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# --- قسم إدارة المحلات (لأبو عمر فقط) ---
if menu == "🏗️ إدارة المحلات":
    st.markdown("<h1 class='main-title'>🏗️ إدارة المحلات والمستخدمين</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("إضافة محل جديد")
        nb = st.text_input("اسم المحل الجديد")
        nu = st.text_input("اسم المستخدم")
        np = st.text_input("كلمة المرور")
        if st.button("حفظ الحساب"):
            new_r = {'branch_name': nb, 'user_name': nu, 'password': np}
            st.session_state.branches_db = pd.concat([st.session_state.branches_db, pd.DataFrame([new_r])], ignore_index=True)
            auto_save(); st.success(f"تم إنشاء حساب {nu} لفرع {nb}"); st.rerun()
    with c2:
        st.subheader("قائمة الحسابات الحالية")
        st.table(st.session_state.branches_db)

# --- نقطة البيع (كود المحل الأصلي معدل للفرع) ---
elif menu == "🛒 نقطة البيع":
    st.markdown(f"<h1 class='main-title'>🛒 بيع بضاعة - {active_branch}</h1>", unsafe_allow_html=True)
    if active_branch == "الكل":
        st.warning("⚠️ يرجى اختيار محل محدد للبيع منه")
    else:
        if st.session_state.show_cust_fields:
            with st.status("✅ تم حفظ الفاتورة!"):
                c_n = st.text_input("اسم الزبون")
                c_p = st.text_input("رقم الهاتف")
                if st.button("💾 حفظ وربط"):
                    mask = (st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id)
                    st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                    auto_save(); st.session_state.show_cust_fields = False; st.rerun()
                if st.button("⏩ تخطي"): st.session_state.show_cust_fields = False; st.rerun()
        else:
            p_method = st.radio("طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
            search_q = st.text_input("🔍 ابحث عن صنف...")
            bill_items = []
            
            # جلب بضاعة الفرع الحالي فقط
            inv_filtered = [i for i in st.session_state.inventory if i.get('branch') == active_branch]
            
            for cat in st.session_state.categories:
                items = [i for i in inv_filtered if i.get('قسم') == cat]
                if search_q: items = [i for i in items if search_q.lower() in i['item'].lower()]
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
                        if i['item'] == e['item'] and i['branch'] == active_branch: i['كمية'] -= e['qty']
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id, 'branch': active_branch, 'cat': e['cat']}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                st.session_state.current_bill_id = b_id
                auto_save(); st.session_state.show_cust_fields = True; st.rerun()

# --- التقارير المالية (نفس كود المحل مع فلترة الفرع) ---
elif menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
    sales = st.session_state.sales_df.copy()
    if active_branch != "الكل": sales = sales[sales['branch'] == active_branch]
    
    sales['date_dt'] = pd.to_datetime(sales['date'])
    today = datetime.now().date()
    d_sales = sales[sales['date_dt'].dt.date == today]
    
    inv_df = pd.DataFrame(st.session_state.inventory)
    if active_branch != "الكل" and not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]
    cap = (inv_df['شراء'] * inv_df['كمية']).sum() if not inv_df.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-box'><div>مبيعات اليوم</div><div class='metric-value'>{format_num(d_sales['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'><div>ربح اليوم</div><div class='metric-value'>{format_num(d_sales['profit'].sum())} ₪</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box' style='border-color:#e67e22'><div>رأس مال البضاعة</div><div class='metric-value'>{format_num(cap)} ₪</div></div>", unsafe_allow_html=True)

# --- الإعدادات (إضافة الأصناف) ---
elif menu == "⚙️ الإعدادات":
    if role != "admin": st.error("🔒 مخصص للمدير فقط"); st.stop()
    st.markdown("<h1 class='main-title'>⚙️ إضافة وتوزيع البضاعة</h1>", unsafe_allow_html=True)
    with st.form("add_item"):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("اسم الصنف")
        br = c2.selectbox("المحل", st.session_state.branches_db['branch_name'].tolist())
        ct = c3.selectbox("القسم", st.session_state.categories)
        buy = c1.number_input("سعر الشراء")
        sell = c2.number_input("سعر البيع")
        qty = c3.number_input("الكمية")
        if st.form_submit_button("إضافة للمخزن"):
            st.session_state.inventory.append({'item':n, 'branch':br, 'قسم':ct, 'شراء':buy, 'بيع':sell, 'كمية':qty})
            auto_save(); st.success("تمت الإضافة!"); st.rerun()
