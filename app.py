import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المطور 2026", layout="wide", page_icon="🍏")

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

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)
    st.session_state.expenses_df.to_csv(EXPENSES_FILE, index=False)
    st.session_state.waste_df.to_csv(WASTE_FILE, index=False)

# تحميل البيانات
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'bill_id'])
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = pd.read_csv(EXPENSES_FILE) if os.path.exists(EXPENSES_FILE) else pd.DataFrame(columns=['date', 'reason', 'amount'])
if 'waste_df' not in st.session_state:
    st.session_state.waste_df = pd.read_csv(WASTE_FILE) if os.path.exists(WASTE_FILE) else pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

if 'last_report' not in st.session_state: st.session_state.last_report = None
if 'p_method' not in st.session_state: st.session_state.p_method = "نقداً"

# 3. التعديل المطلوب: جعل النص والأيقونات بيضاء وعريضة جداً
st.markdown("""
    <style>
    /* خلفية القائمة الجانبية */
    [data-testid="stSidebar"] { 
        background-color: #2c3e50 !important; 
    }
    
    /* استهداف النص والأيقونات داخل الراديو في القائمة الجانبية */
    [data-testid="stSidebar"] .stRadio div label p {
        color: white !important;
        font-weight: 900 !important; /* عريض جداً */
        font-size: 24px !important;  /* تكبير الخط */
        text-shadow: 1px 1px 2px black; /* ظل خفيف لزيادة الوضوح */
        margin-bottom: 10px;
    }

    /* تكبير الدائرة الخاصة بالاختيار */
    [data-testid="stSidebar"] .stRadio div div[data-testid="stWidgetLabel"] {
        margin-bottom: 15px;
    }

    /* تلوين عنوان الترحيب */
    .sidebar-user {
        color: #27ae60 !important;
        font-weight: 900;
        font-size: 28px;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 2px solid white;
    }

    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .report-card { background: #ffffff; padding: 15px; border-radius: 12px; border-right: 8px solid #2c3e50; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; margin-bottom: 10px; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; width: 100%; color: white !important; font-weight: 900; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd == "123":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
else:
    # القائمة الجانبية
    st.sidebar.markdown("<div class='sidebar-user'>مرحباً يا أبو عمر</div>", unsafe_allow_html=True)
    
    # اختيار القائمة
    menu = st.sidebar.radio(
        "القائمة الرئيسية",
        ["🛒 شاشة البيع", "📦 المخزن والتالف", "💸 المصروفات", "📊 التقارير والإحصائيات"]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        if st.session_state.last_report:
            st.markdown(st.session_state.last_report, unsafe_allow_html=True)
            if st.button("➕ فاتورة جديدة", type="primary"):
                st.session_state.last_report = None
                st.rerun()
        else:
            col_p1, col_p2 = st.columns(2)
            if col_p1.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
                st.session_state.p_method = "نقداً"; st.rerun()
            if col_p2.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                st.session_state.p_method = "تطبيق"; st.rerun()

            st.write(f"الدفع الحالي: **{st.session_state.p_method}**")
            bill_items = []
            for cat in st.session_state.categories:
                with st.expander(f"📂 {cat}", expanded=True):
                    items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                    for item, data in items.items():
                        c1, c2, c3 = st.columns([2, 1, 2])
                        with c1: st.write(f"**{item}** (₪{data['بيع']})")
                        with c2: mode = st.radio("النوع", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                        with c3: val = clean_num(st.text_input("المبلغ/الكمية", key=f"v_{item}"))
                        if val > 0:
                            qty = val if mode == "كمية" else val / data["بيع"]
                            amt = val if mode == "شيكل" else val * data["بيع"]
                            if qty <= data['كمية']:
                                bill_items.append({"item": item, "qty": qty, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * qty})
                            else: st.warning(f"المتبقي {data['كمية']:.1f}")
            if st.button("✅ تأكيد البيع", type="primary", use_container_width=True):
                if bill_items:
                    total_amt = sum(i['amount'] for i in bill_items)
                    bill_id = datetime.now().strftime("%Y%m%d%H%M%S")
                    res_html = '<div style="border:2px solid #27ae60; padding:10px; border-radius:10px; direction:rtl;"><h3>🧾 فاتورة</h3>'
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'bill_id': bill_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
                        res_html += f"<p>{e['item']} | {e['qty']:.2f} | {e['amount']:.1f} ₪</p>"
                    res_html += f"<h4>الإجمالي: {total_amt:.1f} ₪</h4></div>"
                    st.session_state.last_report = res_html
                    auto_save(); st.rerun()

    # --- باقي القوائم ---
    elif menu == "📦 المخزن والتالف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 الجرد", "🗑️ التالف"])
        with t1:
            if st.session_state.inventory:
                st.table(pd.DataFrame([{"الصنف": k, "الكمية": f"{v['كمية']:.1f}", "بيع": v['بيع']} for k, v in st.session_state.inventory.items()]))
        with t2:
            with st.form("waste"):
                item_w = st.selectbox("الصنف", list(st.session_state.inventory.keys()))
                qty_w = st.number_input("الكمية", min_value=0.0)
                if st.form_submit_button("حفظ التالف"):
                    if qty_w <= st.session_state.inventory[item_w]['كمية']:
                        loss = qty_w * st.session_state.inventory[item_w]['شراء']
                        st.session_state.inventory[item_w]['كمية'] -= qty_w
                        new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': item_w, 'qty': qty_w, 'loss_value': loss}
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                        auto_save(); st.success("تم الخصم"); st.rerun()

    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            reason = st.text_input("البيان")
            amt_e = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': reason, 'amount': amt_e}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
                auto_save(); st.success("تم الحفظ"); st.rerun()
        st.dataframe(st.session_state.expenses_df, use_container_width=True)

    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التقارير</h1>", unsafe_allow_html=True)
        c_d1, c_d2 = st.columns(2)
        start, end = c_d1.date_input("من", datetime.now().date()), c_d2.date_input("إلى", datetime.now().date())
        for df_n in ['sales_df', 'expenses_df', 'waste_df']:
            st.session_state[df_n]['date_only'] = pd.to_datetime(st.session_state[df_n]['date']).dt.date
        f_s = st.session_state.sales_df[(st.session_state.sales_df['date_only'] >= start) & (st.session_state.sales_df['date_only'] <= end)]
        f_e = st.session_state.expenses_df[(st.session_state.expenses_df['date_only'] >= start) & (st.session_state.expenses_df['date_only'] <= end)]
        f_w = st.session_state.waste_df[(st.session_state.waste_df['date_only'] >= start) & (st.session_state.waste_df['date_only'] <= end)]
        net = f_s['profit'].sum() - f_e['amount'].sum() - f_w['loss_value'].sum()
        st.columns(4)[0].metric("المبيعات", f"{f_s['amount'].sum():.1f}")
        st.columns(4)[1].metric("المصاريف", f"{f_e['amount'].sum():.1f}")
        st.columns(4)[2].metric("التالف", f"{f_w['loss_value'].sum():.1f}")
        st.columns(4)[3].metric("صافي الربح", f"{net:.1f}")
