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
        # حساب المدير العام الافتراضي مخزن هنا أيضاً للقدرة على تعديله
        df = pd.DataFrame([
            {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
            {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
        ])
        df.to_csv(path, index=False)
    return pd.read_csv(path)

# 2. تحميل البيانات الأساسية (Session State)
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

# محاكاة "تذكرني" (استخدام Session State الذي لا ينتهي إلا بغلق المتصفح)
if 'remember_me' not in st.session_state:
    st.session_state.remember_me = False

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
    .rep-card { background: white; border-radius: 15px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #27ae60; }
    .rep-label { color: #7f8c8d; font-size: 1rem; font-weight: bold; margin-bottom: 10px; }
    .rep-value { color: #2c3e50; font-size: 1.8rem; font-weight: 900; }
    .profit-val { color: #27ae60; }
    .loss-val { color: #e74c3c; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول (تعديل: إضافة تذكرني)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("👤 اسم المستخدم").strip()
            p = st.text_input("🔑 كلمة المرور", type="password").strip()
            rem = st.checkbox("تذكرني على هذا الجهاز")
            if st.form_submit_button("دخول"):
                db = pd.read_csv(get_db_path())
                # التحقق من المستخدم (سواء مدير أو فرع)
                m = db[(db['user_name'] == u) & (db['password'] == p)]
                if not m.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = m.iloc[0]['role'] if 'role' in m.columns else "shop"
                    st.session_state.active_user = u
                    st.session_state.my_branch = m.iloc[0]['branch_name']
                    st.session_state.remember_me = rem
                    st.rerun()
                # دخول الطوارئ للمدير العام (أبو عمر) في حال لم يكن في الملف
                elif u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.session_state.my_branch = "الإدارة"
                    st.rerun()
                else: st.error("❌ خطأ في اسم المستخدم أو كلمة المرور")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>, unsafe_allow_html=True)
if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل السريع", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ الإعدادات", "👤 ملفي الشخصي"])
    active_branch = st.sidebar.selectbox("🏠 اختيار الفرع للعرض:", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات", "👤 ملفي الشخصي"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# --- محتوى الأقسام ---

# إضافة قسم الملف الشخصي الجديد
if menu == "👤 ملفي الشخصي":
    st.markdown("<h1 class='main-title'>👤 إعدادات الحساب الشخصي</h1>", unsafe_allow_html=True)
    with st.expander("تعديل بيانات الدخول", expanded=True):
        new_user = st.text_input("تعديل اسم المستخدم", value=st.session_state.active_user)
        new_pass = st.text_input("كلمة مرور جديدة", type="password")
        confirm_pass = st.text_input("تأكيد كلمة المرور", type="password")
        
        if st.button("💾 حفظ التعديلات"):
            if new_pass != confirm_pass:
                st.error("❌ كلمات المرور غير متطابقة")
            elif len(new_pass) < 3:
                st.warning("⚠️ يرجى إدخال كلمة مرور قوية")
            else:
                db = pd.read_csv(get_db_path())
                # تحديث البيانات في ملف الفروع/المستخدمين
                db.loc[db['user_name'] == st.session_state.active_user, ['user_name', 'password']] = [new_user, new_pass]
                db.to_csv(get_db_path(), index=False)
                st.session_state.active_user = new_user
                st.success("✅ تم تحديث بياناتك بنجاح!")

# (بقية الأقسام السابقة كما هي تماماً...)
elif menu in ["📊 التقارير المالية العامة", "📊 التقارير المالية"]:
    title = "📊 التقارير المالية الشاملة - أبو عمر" if st.session_state.user_role == "admin" else f"📊 التقارير المالية - {st.session_state.my_branch}"
    st.markdown(f"<h1 class='main-title'>{title}</h1>", unsafe_allow_html=True)
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    if active_branch != "كافة الفروع":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]
    total_sales = s_df['amount'].sum() if not s_df.empty else 0
    total_profits = s_df['profit'].sum() if not s_df.empty else 0
    total_expenses = e_df['amount'].sum() if not e_df.empty else 0
    net_income = total_profits - total_expenses
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='rep-card'><div class='rep-label'>إجمالي المبيعات</div><div class='rep-value'>{format_num(total_sales)} ₪</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='rep-card'><div class='rep-label'>أرباح البضاعة</div><div class='rep-value profit-val'>{format_num(total_profits)} ₪</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='rep-card'><div class='rep-label'>إجمالي المصروفات</div><div class='rep-value loss-val'>{format_num(total_expenses)} ₪</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='rep-card' style='border-top-color:#3498db'><div class='rep-label'>صافي الربح النهائي</div><div class='rep-value' style='color:#3498db'>{format_num(net_income)} ₪</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    tab_sales, tab_exp = st.tabs(["💰 سجل المبيعات والزبائن", "💸 تفاصيل المصروفات"])
    with tab_sales:
        if s_df.empty: st.info("لا توجد مبيعات مسجلة.")
        else:
            view_s = s_df.sort_values(by='date', ascending=False)
            st.dataframe(view_s[['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'branch']].rename(columns={'date':'التاريخ', 'item':'الصنف', 'amount':'المبلغ', 'profit':'الربح', 'method':'الدفع', 'customer_name':'الزبون', 'customer_phone':'الهاتف', 'branch':'الفرع'}), use_container_width=True, hide_index=True)
    with tab_exp:
        if e_df.empty: st.info("لا توجد مصروفات مسجلة.")
        else:
            view_e = e_df.sort_values(by='date', ascending=False)
            st.dataframe(view_e[['date', 'reason', 'amount', 'branch']].rename(columns={'date':'التاريخ', 'reason':'البيان', 'amount':'المبلغ', 'branch':'الفرع'}), use_container_width=True, hide_index=True)

elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة بيع البضاعة</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    if st.session_state.show_cust_fields:
        with st.expander("✅ تم اعتماد الفاتورة! سجل بيانات الزبون الآن", expanded=True):
            c_n = st.text_input("اسم الزبون"); c_p = st.text_input("رقم الهاتف")
            if st.button("💾 حفظ البيانات"):
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
                st.markdown(f"<div style='background:#f1f4f6; padding:10px; border-radius:10px; margin:10px 0; border-right:5px solid #27ae60; font-weight:bold;'>📂 {cat}</div>", unsafe_allow_html=True)
                cols = st.columns(3)
                for idx, it in enumerate(items):
                    with cols[idx % 3]:
                        st.markdown(f"<div style='background:white; border-radius:12px; padding:12px; border:1px solid #e2e8f0; text-align:center;'><b>{it['item']}</b><br><span style='color:#27ae60'>{format_num(it['بيع'])} ₪</span><br><small>متوفر: {format_num(it['كمية'])}</small></div>", unsafe_allow_html=True)
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
    t1, t2, t3 = st.tabs(["📋 الرصيد", "⚖️ الجرد", "🗑️ التوالف"])
    with t1: st.dataframe(pd.DataFrame(my_inv)[['item', 'قسم', 'شراء', 'بيع', 'كمية']] if my_inv else pd.DataFrame(), use_container_width=True)
    with t2:
        j_data = []
        for it in my_inv:
            c1, _, c3 = st.columns([2, 1, 1])
            res = c3.text_input(f"كمية {it['item']}", key=f"j_{it['item']}")
            if res: j_data.append({'item': it['item'], 'q': clean_num(res)})
        if st.button("✔️ حفظ الجرد"):
            for d in j_data:
                for idx, inv_item in enumerate(st.session_state.inventory):
                    if inv_item['item'] == d['item'] and inv_item['branch'] == st.session_state.my_branch:
                        st.session_state.inventory[idx]['كمية'] = d['q']
            auto_save(); st.rerun()
    with t3:
        with st.form("w_f"):
            wi = st.selectbox("الصنف", [i['item'] for i in my_inv]); wq = st.number_input("الكمية", min_value=0.0)
            if st.form_submit_button("تسجيل"):
                for idx, inv_item in enumerate(st.session_state.inventory):
                    if inv_item['item'] == wi and inv_item['branch'] == st.session_state.my_branch:
                        st.session_state.inventory[idx]['كمية'] -= wq
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': wi, 'qty': wq, 'branch': st.session_state.my_branch}])], ignore_index=True)
                auto_save(); st.rerun()

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r = st.text_input("البيان"); a = st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()
    st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
    with st.form("add_i"):
        n = st.text_input("اسم الصنف"); cat = st.selectbox("القسم", st.session_state.categories)
        b = st.text_input("التكلفة"); s = st.text_input("البيع"); q = st.text_input("الكمية")
        if st.form_submit_button("➕ إضافة"):
            st.session_state.inventory.append({"item": n, "قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q), "branch": st.session_state.my_branch})
            auto_save(); st.rerun()

elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
    with st.form("br"):
        bn = st.text_input("المحل"); un = st.text_input("المستخدم"); pw = st.text_input("المرور")
        if st.form_submit_button("حفظ"):
            pd.concat([pd.read_csv(get_db_path()), pd.DataFrame([{'branch_name':bn,'user_name':un,'password':pw, 'role': 'shop'}])]).to_csv(get_db_path(), index=False)
            st.rerun()
    st.table(pd.read_csv(get_db_path()))
