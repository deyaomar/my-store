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

# 2. إدارة ملفات البيانات
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'category']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        if os.path.exists(file):
            st.session_state[state_key] = pd.read_csv(file)
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    if os.path.exists('inventory_final.csv'):
        inv_df = pd.read_csv('inventory_final.csv')
        st.session_state.inventory = inv_df.set_index(inv_df.columns[0]).to_dict('index')
    else:
        st.session_state.inventory = {}

def auto_save():
    if st.session_state.inventory:
        pd.DataFrame.from_dict(st.session_state.inventory, orient='index').to_csv('inventory_final.csv', index=True)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)

# 3. واجهة المستخدم والتنسيق
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    [data-testid="stSidebar"] { background-color: #029c63 !important; border-left: 3px solid #27ae60; min-width: 300px !important; }
    .sidebar-user { background-color: #1a1a1a; padding: 25px 10px; border-radius: 15px; margin: 15px 10px; border: 2px solid #27ae60; text-align: center; color: white !important; font-weight: 900; font-size: 24px; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
    .report-card { background: #f9f9f9; padding: 20px; border-radius: 15px; border-right: 5px solid #27ae60; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .stock-card { background: white; border-radius: 15px; padding: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; border-right: 5px solid #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    with st.sidebar:
        st.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
        menu = st.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"], label_visibility="collapsed")
        if st.button("🚪 تسجيل خروج", use_container_width=True): st.session_state.logged_in = False; st.rerun()

    # --- 🛒 نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
        if 'show_customer_form' not in st.session_state:
            st.session_state.show_customer_form = False
            st.session_state.current_bill_items = []

        if not st.session_state.show_customer_form:
            c1, c2 = st.columns([1, 2])
            p_meth = c1.selectbox("💳 طريقة الدفع", ["تطبيق", "نقداً"])
            search_q = c2.text_input("🔍 ابحث عن صنف...")
            temp_bill = []
            cols = st.columns(3)
            filtered_items = [(k, v) for k, v in st.session_state.inventory.items() if not search_q or search_q in k]
            for idx, (it, data) in enumerate(filtered_items):
                with cols[idx % 3]:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:10px; border:1px solid #eee; text-align:center;"><b>{it}</b><br><span style="color:#27ae60">{data["بيع"]} ₪</span></div>', unsafe_allow_html=True)
                    mc1, mc2 = st.columns(2)
                    mode = mc1.radio("بـ", ["₪", "كجم"], key=f"m_{it}", horizontal=True)
                    val = clean_num(mc2.text_input("المقدار", key=f"v_{it}"))
                    if val > 0:
                        q = val if mode == "كجم" else val / data["بيع"]
                        temp_bill.append({"item": it, "qty": q, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * q, "method": p_meth})
            if temp_bill and st.button("🚀 إتمام العملية"):
                st.session_state.current_bill_items = temp_bill
                st.session_state.show_customer_form = True; st.rerun()
        else:
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الهاتف")
            if st.button("✅ تأكيد"):
                bid = str(uuid.uuid4())[:8]
                for e in st.session_state.current_bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': c_p, 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.session_state.show_customer_form = False; st.rerun()

    # --- 📦 المخزن والجرد (تمت استعادة القوائم هنا) ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📋 رصيد المخزن", "⚖️ الجرد والمطابقة", "🗑️ التالف"])
        
        with tab1:
            cols = st.columns(3)
            for idx, (it, data) in enumerate(st.session_state.inventory.items()):
                with cols[idx % 3]:
                    st.markdown(f'<div class="stock-card"><b>{it}</b><br>{format_num(data["كمية"])} كجم</div>', unsafe_allow_html=True)
        
        with tab2:
            st.info("نظام مطابقة الجرد الفعلي")
            audit_results = []
            for it, data in st.session_state.inventory.items():
                c1, c2, c3 = st.columns([2, 1, 2])
                c1.write(f"**{it}** (النظام: {format_num(data['كمية'])})")
                act = c2.text_input("الفعلية", key=f"aud_{it}")
                if act:
                    act_val = clean_num(act)
                    diff = act_val - data['كمية']
                    c3.write(f"الفرق: {format_num(diff)} | قيمة: {format_num(diff * data['شراء'])} ₪")
                    audit_results.append({'item': it, 'new': act_val})
            if audit_results and st.button("💾 اعتماد الجرد المكتمل"):
                for r in audit_results:
                    st.session_state.inventory[r['item']]['كمية'] = r['new']
                auto_save(); st.success("تم تحديث المخزن!"); st.rerun()

        with tab3:
            st.subheader("تسجيل التالف")
            with st.form("waste_form"):
                w_it = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
                w_q = st.number_input("الكمية التالفة", min_value=0.0)
                if st.form_submit_button("حفظ التالف"):
                    st.session_state.inventory[w_it]['كمية'] -= w_q
                    new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_it, 'qty': w_q, 'loss_value': w_q * st.session_state.inventory[w_it]['شراء']}
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                    auto_save(); st.success("تم تسجيل التالف"); st.rerun()

    # --- 📊 التقارير المالية ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية الشاملة</h1>", unsafe_allow_html=True)
        st.session_state.sales_df['date_only'] = pd.to_datetime(st.session_state.sales_df['date']).dt.strftime('%Y-%m-%d')
        today = datetime.now().strftime("%Y-%m-%d")
        last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        daily_sales = st.session_state.sales_df[st.session_state.sales_df['date_only'] == today]['amount'].sum()
        weekly_sales = st.session_state.sales_df[st.session_state.sales_df['date_only'] >= last_week]['amount'].sum()
        cap_stock = sum(v['كمية'] * v['شراء'] for v in st.session_state.inventory.values())
        raw_profit = st.session_state.sales_df['profit'].sum()
        total_exp = st.session_state.expenses_df['amount'].sum()
        total_waste = st.session_state.waste_df['loss_value'].sum()
        net_profit = raw_profit - total_exp - total_waste

        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='report-card'><h3>💰 مبيعات اليوم</h3><h2>{format_num(daily_sales)} ₪</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h3>📅 مبيعات الأسبوع</h3><h2>{format_num(weekly_sales)} ₪</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h3>🏗️ رأس المال الحالي</h3><h2>{format_num(cap_stock)} ₪</h2></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        c4, c5, c6 = st.columns(3)
        p_color = "#27ae60" if net_profit >= 0 else "#e74c3c"
        c4.markdown(f"<div class='report-card' style='border-color:{p_color}'><h3>💵 صافي الأرباح</h3><h2 style='color:{p_color}'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)
        c5.markdown(f"<div class='report-card' style='border-color:#e74c3c'><h3>🗑️ إجمالي التالف</h3><h2>{format_num(total_waste)} ₪</h2></div>", unsafe_allow_html=True)
        c6.markdown(f"<div class='report-card'><h3>📉 إجمالي المصروفات</h3><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("👥 سجل الزبائن اليومي")
        sel_date = st.date_input("اختر التاريخ", datetime.now()).strftime('%Y-%m-%d')
        cust_df = st.session_state.sales_df[st.session_state.sales_df['date_only'] == sel_date]
        if not cust_df.empty:
            st.table(cust_df[['date', 'customer_name', 'customer_phone', 'item', 'amount', 'method']].rename(columns={'date':'الوقت','customer_name':'الزبون','customer_phone':'الهاتف','item':'الصنف','amount':'المبلغ'}))

    # --- 💸 المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("البيان"); a = st.number_input("المبلغ")
            if st.form_submit_button("حفظ"):
                new_e = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'reason': r, 'amount': a}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
                auto_save(); st.rerun()
        st.table(st.session_state.expenses_df.sort_values(by='date', ascending=False))

    # --- ⚙️ الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        with st.form("add"):
            n = st.text_input("الصنف"); b = st.text_input("شراء"); s = st.text_input("بيع"); q = st.text_input("كمية")
            if st.form_submit_button("حفظ"):
                st.session_state.inventory[n] = {"شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.rerun()
