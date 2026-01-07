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
    
# 3. التصميم (CSS - تباين عالي جداً للقوائم)
st.markdown("""
    <style>
    /* خلفية القائمة الجانبية */
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }

    /* العناوين الرئيسية */
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }

    /* --- تعديل ألوان القائمة المنسدلة (Selectbox) --- */
    
    /* 1. شكل الصندوق وهو مغلق (الواجهة) */
    div[data-baseweb="select"] > div {
        background-color: #2c3e50 !important; /* كحلي غامق */
        color: white !important;              /* كتابة بيضاء */
        border: 2px solid #27ae60 !important; /* إطار أخضر */
        border-radius: 8px !important;
    }

    /* 2. إجبار النص داخل الصندوق أن يكون أبيض وعريض */
    div[data-baseweb="select"] span {
        color: white !important;
        font-weight: 900 !important;
        font-size: 20px !important;
    }

    /* 3. السهم الصغير في القائمة */
    svg[data-testid="stSelectboxArrow"] {
        fill: white !important;
    }

    /* 4. القائمة المنسدلة عند فتحها (الخيارات) */
    ul[data-baseweb="menu"] {
        background-color: white !important;
    }
    li[data-baseweb="option"] {
        color: #2c3e50 !important; /* لون الخط في القائمة المفتوحة كحلي */
        font-weight: bold !important;
        font-size: 18px !important;
    }

    /* باقي التنسيقات */
    .report-card { background: #ffffff; padding: 15px; border-radius: 12px; border-right: 8px solid #2c3e50; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; margin-bottom: 10px; }
    .low-stock { background: #ffeded; border-right: 5px solid #ff4b4b; padding: 10px; border-radius: 5px; color: #ff4b4b; font-weight: bold; margin-bottom: 5px; }
    
    .stButton > button { 
        font-weight: 900 !important; 
        font-size: 20px !important;
        height: 60px !important; /* تكبير زر التأكيد */
        border-radius: 10px !important;
    }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; width: 100%; color: white !important; border: none; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول والتحكم
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
    st.sidebar.markdown(f"### مرحباً يا أبو عمر")
    menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 شاشة البيع", "📦 المخزن والتالف", "💸 المصروفات", "📊 التقارير والإحصائيات"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        
        low_stock = [k for k, v in st.session_state.inventory.items() if v['كمية'] <= 5]
        for item in low_stock:
            st.markdown(f"<div class='low-stock'>⚠️ {item} قارب على الانتهاء ({st.session_state.inventory[item]['كمية']:.1f} متبقي)</div>", unsafe_allow_html=True)

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
                        with c2: mode = st.radio("النوع", ["شيكل", "كمية"], key=f"m_{item}", label_visibility="collapsed", horizontal=True)
                        with c3: val = clean_num(st.text_input("0", key=f"v_{item}", label_visibility="collapsed", placeholder="0"))
                        
                        if val > 0:
                            qty = val if mode == "كمية" else val / data["بيع"]
                            amt = val if mode == "شيكل" else val * data["بيع"]
                            if qty <= data['كمية']:
                                bill_items.append({"item": item, "qty": qty, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * qty})
                            else: st.warning(f"المخزن فيه {data['كمية']:.1f} فقط!")

            if st.button("✅ تأكيد البيع والحفظ", type="primary", use_container_width=True):
                if bill_items:
                    total_amt = sum(i['amount'] for i in bill_items)
                    bill_id = datetime.now().strftime("%Y%m%d%H%M%S")
                    res_html = '<div style="border:2px solid #27ae60; padding:15px; border-radius:10px; direction:rtl; background:#f9f9f9;"><h3>🧾 فاتورة أبو عمر</h3>'
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'bill_id': bill_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
                        res_html += f"<p><b>{e['item']}</b>: {e['qty']:.2f} | {e['amount']:.1f} ₪</p>"
                    res_html += f"<hr><h4>الإجمالي: {total_amt:.1f} ₪</h4></div>"
                    st.session_state.last_report = res_html
                    auto_save(); st.rerun()

    # --- 2. المخزن والتالف ---
    elif menu == "📦 المخزن والتالف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن والتالف</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 جرد المخزن", "🗑️ تسجيل التالف"])
        with t1:
            if st.session_state.inventory:
                st.table(pd.DataFrame([{"الصنف": k, "الكمية": f"{v['كمية']:.1f}", "شراء": v['شراء'], "بيع": v['بيع']} for k, v in st.session_state.inventory.items()]))
        with t2:
            with st.form("waste_form"):
                item_w = st.selectbox("اختر الصنف التالف", list(st.session_state.inventory.keys()))
                qty_w = st.number_input("الكمية", min_value=0.0, step=0.1)
                if st.form_submit_button("تسجيل الخسارة"):
                    if qty_w > 0 and qty_w <= st.session_state.inventory[item_w]['كمية']:
                        loss = qty_w * st.session_state.inventory[item_w]['شراء']
                        st.session_state.inventory[item_w]['كمية'] -= qty_w
                        new_w = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': item_w, 'qty': qty_w, 'loss_value': loss}
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                        auto_save(); st.success("تم الخصم"); st.rerun()

    # --- 3. المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp_form"):
            reason = st.text_input("البيان")
            amt_e = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ المصروف"):
                new_e = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'reason': reason, 'amount': amt_e}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
                auto_save(); st.success("تم الحفظ"); st.rerun()
        st.dataframe(st.session_state.expenses_df.sort_values(by='date', ascending=False))

    # --- 4. التقارير ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 تقرير الأداء المالي</h1>", unsafe_allow_html=True)
        c_d1, c_d2 = st.columns(2)
        start = c_d1.date_input("من", datetime.now().date())
        end = c_d2.date_input("إلى", datetime.now().date())

        for df_n in ['sales_df', 'expenses_df', 'waste_df']:
            st.session_state[df_n]['date_only'] = pd.to_datetime(st.session_state[df_n]['date']).dt.date

        f_s = st.session_state.sales_df[(st.session_state.sales_df['date_only'] >= start) & (st.session_state.sales_df['date_only'] <= end)]
        f_e = st.session_state.expenses_df[(st.session_state.expenses_df['date_only'] >= start) & (st.session_state.expenses_df['date_only'] <= end)]
        f_w = st.session_state.waste_df[(st.session_state.waste_df['date_only'] >= start) & (st.session_state.waste_df['date_only'] <= end)]

        net_p = f_s['profit'].sum() - f_e['amount'].sum() - f_w['loss_value'].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f"<div class='report-card'><h3>المبيعات</h3><h2>{f_s['amount'].sum():.1f}</h2></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='report-card'><h3>المصاريف</h3><h2>{f_e['amount'].sum():.1f}</h2></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='report-card'><h3>التالف</h3><h2>{f_w['loss_value'].sum():.1f}</h2></div>", unsafe_allow_html=True)
        col4.markdown(f"<div class='report-card' style='border-right-color:#27ae60;'><h3>صافي الربح</h3><h2>{net_p:.1f}</h2></div>", unsafe_allow_html=True)

        if not f_s.empty:
            st.plotly_chart(px.bar(f_s.groupby('item')['amount'].sum().reset_index(), x='item', y='amount', color='amount', color_continuous_scale='Greens'), use_container_width=True)
