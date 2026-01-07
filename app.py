import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

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

# 2. ملفات البيانات
DB_FILE = 'inventory_final.csv'
SALES_FILE = 'sales_final.csv'
EXPENSES_FILE = 'expenses_final.csv'
WASTE_FILE = 'waste_final.csv'
CATS_FILE = 'categories_final.csv'

# معالجة تحميل الملفات
for f, cols in {SALES_FILE: ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'],
                EXPENSES_FILE: ['date', 'reason', 'amount'],
                WASTE_FILE: ['date', 'item', 'qty', 'loss_value']}.items():
    if f not in st.session_state:
        if os.path.exists(f):
            df = pd.read_csv(f)
            for col in cols:
                if col not in df.columns: df[col] = 0.0 if 'profit' in col or 'amount' in col or 'loss' in col else ""
            st.session_state[f.split('_')[0] + '_df'] = df
        else:
            st.session_state[f.split('_')[0] + '_df'] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

# حالات البرنامج
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None
if 'success_msg' not in st.session_state: st.session_state.success_msg = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)
    st.session_state.expenses_df.to_csv(EXPENSES_FILE, index=False)
    st.session_state.waste_df.to_csv(WASTE_FILE, index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv(CATS_FILE, index=False)

# 3. التنسيق الجمالي (العائد كما كان)
st.markdown("""
    <style>
    /* تنسيق القائمة الجانبية */
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 900; font-size: 19px; margin-bottom: 10px; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; margin-bottom: 20px; border-bottom: 2px solid white; padding-bottom: 10px; }
    
    /* تنسيق العناوين والأزرار */
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 25px; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; width: 100%; color: white !important; font-weight: 900; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None

    # القائمة الجانبية بالتنسيق المطلوب
    st.sidebar.markdown("<div class='sidebar-user'>مرحباً يا أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "🛒 شاشة البيع", 
        "📦 المخزن والجرد", 
        "💸 المصروفات", 
        "📊 التقارير والإحصائيات", 
        "⚙️ إدارة الأصناف"
    ])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        if st.session_state.show_cust_fields:
            st.info("👤 إضافة بيانات الزبون")
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الجوال")
            if st.button("💾 حفظ وإتمام", type="primary"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, 'customer_name'] = c_n
                st.session_state.sales_df.loc[mask, 'customer_phone'] = c_p
                auto_save(); st.session_state.show_cust_fields = False; st.rerun()
        else:
            col_m1, col_m2 = st.columns(2)
            if col_m2.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                st.session_state.p_method = "تطبيق"; st.rerun()
            if col_m1.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
                st.session_state.p_method = "نقداً"; st.rerun()
            
            bill_items = []
            for cat in st.session_state.categories:
                with st.expander(f"📂 {cat}", expanded=True):
                    items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                    for item, data in items.items():
                        c1, c2, c3 = st.columns([2, 1, 2])
                        with c1: st.write(f"**{item}**")
                        with c2: mode = st.radio("النوع", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                        with c3: val = clean_num(st.text_input("القيمة", key=f"v_{item}", label_visibility="collapsed"))
                        if val > 0:
                            qty = val if mode == "كمية" else val / data["بيع"]
                            amt = val if mode == "شيكل" else val * data["بيع"]
                            bill_items.append({"item": item, "qty": qty, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * qty})
            
            if st.button("✅ تأكيد البيع والحفظ", type="primary"):
                if bill_items:
                    b_id = str(uuid.uuid4())
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': '', 'customer_phone': '', 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save()
                    if st.session_state.p_method == "تطبيق": st.session_state.show_cust_fields = True
                    else: st.session_state.success_msg = "✅ تم الحفظ"; st.rerun()

    # --- 2. المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["📊 عرض الكميات", "⚖️ الجرد اليدوي", "🗑️ تسجيل تالف"])
        with t1:
            if st.session_state.inventory:
                st.table(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية المسجلة": format_num(v['كمية'])} for k, v in st.session_state.inventory.items()]))
        with t2:
            st.subheader("تعديل الكمية المسجلة")
            it = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
            st.warning(f"الكمية الحالية في النظام لـ {it} هي: {format_num(st.session_state.inventory[it]['كمية'])}")
            new_q = st.number_input("الكمية الفعلية بالمحل", min_value=0.0)
            if st.button("تحديث الكمية"):
                st.session_state.inventory[it]['كمية'] = new_q
                auto_save(); st.session_state.success_msg = "✅ تم تحديث الجرد"; st.rerun()
        with t3:
            with st.form("waste_f"):
                wi = st.selectbox("صنف تالف", list(st.session_state.inventory.keys()))
                wq = st.number_input("الكمية", min_value=0.0)
                if st.form_submit_button("تسجيل"):
                    loss = wq * st.session_state.inventory[wi]['شراء']
                    st.session_state.inventory[wi]['كمية'] -= wq
                    new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': wi, 'qty': wq, 'loss_value': loss}
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                    auto_save(); st.rerun()

    # --- 3. المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp_f"):
            reason = st.text_input("البيان")
            amount = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': reason, 'amount': amount}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
                auto_save(); st.session_state.success_msg = "✅ تم الحفظ"; st.rerun()
        st.dataframe(st.session_state.expenses_df.sort_index(ascending=False), use_container_width=True)

    # --- 4. التقارير ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
        ts = st.session_state.sales_df['amount'].sum()
        tp = st.session_state.sales_df['profit'].sum()
        te = st.session_state.expenses_df['amount'].sum()
        tw = st.session_state.waste_df['loss_value'].sum()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("المبيعات", f"{format_num(ts)} ₪")
        c2.metric("المصروفات", f"{format_num(te)} ₪")
        c3.metric("خسائر التالف", f"{format_num(tw)} ₪")
        c4.metric("صافي الربح", f"{format_num(tp - te - tw)} ₪")
        st.markdown("---")
        st.subheader("📋 تقرير التالف")
        st.dataframe(st.session_state.waste_df, use_container_width=True)

    # --- 5. إدارة الأصناف ---
    elif menu == "⚙️ إدارة الأصناف":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        with st.form("add_i"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            c1, c2, c3 = st.columns(3)
            b, s, q = c1.text_input("شراء"), c2.text_input("بيع"), c3.text_input("كمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.session_state.success_msg = f"✅ تم إضافة صنف {n} بنجاح"; st.rerun()
