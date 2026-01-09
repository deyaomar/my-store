import streamlit as st
import pandas as pd
import os
from datetime import datetime
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

# 2. إدارة ملفات البيانات
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        if os.path.exists(file):
            df = pd.read_csv(file)
            for c in cols: 
                if c not in df.columns: df[c] = 0.0 if 'amount' in c or 'profit' in c or 'loss' in c or 'qty' in c else ""
            st.session_state[state_key] = df
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    if os.path.exists('inventory_final.csv'):
        try:
            inv_df = pd.read_csv('inventory_final.csv')
            inv_df = inv_df.drop_duplicates(subset=[inv_df.columns[0]], keep='last')
            st.session_state.inventory = inv_df.set_index(inv_df.columns[0]).to_dict('index')
        except: st.session_state.inventory = {}
    else: st.session_state.inventory = {}

if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None

def auto_save():
    if st.session_state.inventory:
        pd.DataFrame.from_dict(st.session_state.inventory, orient='index').to_csv('inventory_final.csv', index=True)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. واجهة المستخدم (التنسيق)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }

    [data-testid="stSidebar"] { background-color: #000000 !important; border-left: 3px solid #27ae60; min-width: 300px !important; }
    .sidebar-user { background-color: #1a1a1a; padding: 25px 10px; border-radius: 15px; margin: 15px 10px; border: 2px solid #27ae60; text-align: center; color: white !important; font-weight: 900; font-size: 24px; }
    
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        background-color: #1a1a1a !important; color: #ffffff !important;
        padding: 15px 20px !important; border-radius: 12px !important;
        margin-bottom: 10px !important; font-size: 18px !important; font-weight: 900 !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #27ae60 !important; border: 1px solid white; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > span:first-child { display: none !important; }

    .item-card {
        background-color: #fcfcfc; border: 2px solid #eee; border-radius: 15px;
        padding: 15px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .price-tag { color: #27ae60; font-weight: 900; font-size: 22px; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    with st.sidebar:
        st.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
        menu = st.radio("Menu", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"], label_visibility="collapsed")
        if st.button("🚪 خروج آمن", use_container_width=True): st.session_state.clear(); st.rerun()

    # --- 🛒 نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
        if st.session_state.show_cust_fields:
            with st.status("✅ تم حفظ الفاتورة!"):
                c_n = st.text_input("اسم الزبون")
                c_p = st.text_input("رقم الهاتف")
                if st.button("💾 حفظ البيانات"):
                    mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                    st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                    auto_save(); st.session_state.show_cust_fields = False; st.rerun()
                if st.button("⏩ تخطي"): st.session_state.show_cust_fields = False; st.rerun()
        else:
            c1, c2 = st.columns([1, 2])
            with c1: p_meth = st.selectbox("💳 الدفع", ["تطبيق", "نقداً"])
            with c2: search_q = st.text_input("🔍 ابحث...")
            bill_items = []
            for cat in st.session_state.categories:
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                if search_q: items = {k: v for k, v in items.items() if search_q in k}
                if items:
                    st.markdown(f"#### 📂 {cat}")
                    cols = st.columns(2)
                    for idx, (it, data) in enumerate(items.items()):
                        with cols[idx % 2]:
                            st.markdown(f"<div class='item-card'><b>{it}</b> | <span class='price-tag'>{data['بيع']} ₪</span><br><small>المتوفر: {data['كمية']}</small></div>", unsafe_allow_html=True)
                            mc1, mc2 = st.columns(2)
                            mode = mc1.radio("بـ", ["₪", "كجم"], key=f"m_{it}", horizontal=True)
                            val = clean_num(mc2.text_input("المقدار", key=f"v_{it}"))
                            if val > 0:
                                q = val if mode == "كجم" else val / data["بيع"]
                                bill_items.append({"item": it, "qty": q, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * q})
            if bill_items:
                if st.button("🚀 إتمام العملية", use_container_width=True, type="primary"):
                    bid = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': p_meth, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': bid}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                    st.session_state.current_bill_id = bid
                    auto_save(); st.session_state.show_cust_fields = True; st.rerun()

    # --- 📦 المخزن والجرد (تم إضافة التالف هنا) ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📋 الرصيد الحالي", "⚖️ جرد المخزن", "🗑️ تسجيل التالف"])
        
        with tab1:
            if st.session_state.inventory:
                st.dataframe(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية": v['كمية'], "التكلفة": v['شراء']} for k, v in st.session_state.inventory.items()]), use_container_width=True)
        
        with tab2:
            st.info("قم بإدخال الكمية الفعلية الموجودة في المحل حالياً:")
            jard_data = {}
            for it, data in st.session_state.inventory.items():
                c1, c2 = st.columns([3, 2])
                c1.write(f"**{it}** (النظام: {data['كمية']})")
                val = c2.text_input("الكمية الفعلية", key=f"jard_{it}")
                if val != "": jard_data[it] = clean_num(val)
            if st.button("✔️ اعتماد الجرد وتصحيح الرصيد"):
                for it, real_q in jard_data.items():
                    diff = st.session_state.inventory[it]['كمية'] - real_q
                    loss = diff * st.session_state.inventory[it]['شراء']
                    st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': it, 'diff_qty': diff, 'loss_value': loss}])], ignore_index=True)
                    st.session_state.inventory[it]['كمية'] = real_q
                auto_save(); st.success("تم تحديث المخزن بنجاح"); st.rerun()

        with tab3:
            st.error("تسجيل الكميات التالفة (يتم خصمها من الأرباح مباشرة):")
            with st.form("waste_form"):
                w_item = st.selectbox("اختر الصنف التالف", list(st.session_state.inventory.keys()))
                w_qty = st.number_input("الكمية التالفة (كجم)", min_value=0.0, step=0.1)
                if st.form_submit_button("🗑️ تسجيل وإتلاف"):
                    if w_qty > 0:
                        loss_val = w_qty * st.session_state.inventory[w_item]['شراء']
                        st.session_state.inventory[w_item]['كمية'] -= w_qty
                        new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'loss_value': loss_val}
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                        auto_save(); st.success(f"تم تسجيل {w_qty} كجم تالف من {w_item}"); st.rerun()

    # --- 📊 التقارير المالية (معدلة لخصم التالف) ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية والأرباح</h1>", unsafe_allow_html=True)
        
        sales_profit = st.session_state.sales_df['profit'].sum()
        total_waste = st.session_state.waste_df['loss_value'].sum()
        total_exp = st.session_state.expenses_df['amount'].sum()
        net_profit = sales_profit - total_waste - total_exp

        col1, col2, col3 = st.columns(3)
        col1.metric("أرباح المبيعات", f"{format_num(sales_profit)} ₪")
        col2.metric("إجمالي التالف", f"- {format_num(total_waste)} ₪", delta_color="inverse")
        col3.metric("صافي الربح النهائي", f"{format_num(net_profit)} ₪")

    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
        with st.form("add_item"):
            n = st.text_input("اسم الصنف الجديد")
            cat = st.selectbox("القسم", st.session_state.categories)
            b = st.text_input("سعر التكلفة (شراء)")
            s = st.text_input("سعر البيع")
            q = st.text_input("الكمية الابتدائية")
            if st.form_submit_button("حفظ"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.success("تم الحفظ"); st.rerun()
