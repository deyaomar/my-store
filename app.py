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

# 2. إدارة ملفات البيانات (الثبات الدائم)
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'category']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value'])
}

# تحميل البيانات من الملفات فور تشغيل النظام
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

# دالة الحفظ التلقائي الفوري
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
    [data-testid="stSidebar"] { background-color: #000000 !important; border-left: 3px solid #27ae60; min-width: 300px !important; }
    .sidebar-user { background-color: #1a1a1a; padding: 25px 10px; border-radius: 15px; margin: 15px 10px; border: 2px solid #27ae60; text-align: center; color: white !important; font-weight: 900; font-size: 24px; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
    .report-card { background: #f9f9f9; padding: 20px; border-radius: 15px; border-right: 5px solid #27ae60; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .stock-card { background: white; border-radius: 15px; padding: 15px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; border-right: 5px solid #27ae60; }
    .customer-box { background-color: #f0fff4; padding: 20px; border-radius: 15px; border: 2px solid #27ae60; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول الذكي (يمنع الخروج التلقائي عند التحديث البسيط)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": 
            st.session_state.logged_in = True
            st.rerun()
else:
    # --- محتوى النظام بعد الدخول ---
    with st.sidebar:
        st.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
        menu = st.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 تسجيل خروج نهائي", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- 🛒 نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
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
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:10px; border:1px solid #eee; text-align:center; margin-bottom:5px;"><b>{it}</b><br><span style="color:#27ae60">{data["بيع"]} ₪</span></div>', unsafe_allow_html=True)
                    mc1, mc2 = st.columns(2)
                    mode = mc1.radio("بـ", ["₪", "كجم"], key=f"m_{it}", horizontal=True)
                    val = clean_num(mc2.text_input("المقدار", key=f"v_{it}"))
                    if val > 0:
                        q = val if mode == "كجم" else val / data["بيع"]
                        temp_bill.append({"item": it, "qty": q, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * q, "method": p_meth})
            if temp_bill and st.button("🚀 إتمام العملية", use_container_width=True):
                st.session_state.current_bill_items = temp_bill
                st.session_state.show_customer_form = True; st.rerun()
        else:
            st.markdown('<div class="customer-box">', unsafe_allow_html=True)
            st.subheader("👤 تسجيل بيانات الزبون")
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الهاتف")
            if st.button("✅ تأكيد"):
                bid = str(uuid.uuid4())[:8]
                for e in st.session_state.current_bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': c_p, 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.session_state.show_customer_form = False; st.rerun()
            if st.button("🔙 رجوع"): st.session_state.show_customer_form = False; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # --- 📦 المخزن والجرد ---
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
                    audit_results.append({'item': it, 'new': act_val, 'diff': diff, 'loss': diff * data['شراء']})
            if audit_results and st.button("💾 اعتماد الجرد المكتمل"):
                for r in audit_results:
                    st.session_state.inventory[r['item']]['كمية'] = r['new']
                auto_save(); st.success("تم التحديث!"); st.rerun()

    # --- 📊 التقارير المالية وسجل الزبائن ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية وسجل الزبائن</h1>", unsafe_allow_html=True)
        st.session_state.sales_df['date_only'] = pd.to_datetime(st.session_state.sales_df['date']).dt.strftime('%Y-%m-%d')
        today = datetime.now().strftime("%Y-%m-%d")
        last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # الحسابات
        daily_sales = st.session_state.sales_df[st.session_state.sales_df['date_only'] == today]['amount'].sum()
        weekly_sales = st.session_state.sales_df[st.session_state.sales_df['date_only'] >= last_week]['amount'].sum()
        cap_stock = sum(v['كمية'] * v['شراء'] for v in st.session_state.inventory.values())
        net_profit = st.session_state.sales_df['profit'].sum() - st.session_state.expenses_df['amount'].sum() - st.session_state.waste_df['loss_value'].sum()

        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='report-card'><h3>💰 مبيعات اليوم</h3><h2>{format_num(daily_sales)} ₪</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h3>📅 مبيعات الأسبوع</h3><h2>{format_num(weekly_sales)} ₪</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h3>🏗️ رأس المال الحالي</h3><h2>{format_num(cap_stock)} ₪</h2></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        c4, c5, c6 = st.columns(3)
        c4.markdown(f"<div class='report-card'><h3>💵 صافي الأرباح</h3><h2>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)
        c5.markdown(f"<div class='report-card'><h3>🗑️ إجمالي التالف</h3><h2>{format_num(st.session_state.waste_df['loss_value'].sum())} ₪</h2></div>", unsafe_allow_html=True)
        c6.markdown(f"<div class='report-card'><h3>📉 إجمالي المصروفات</h3><h2>{format_num(st.session_state.expenses_df['amount'].sum())} ₪</h2></div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("👥 سجل مبيعات الزبائن اليومي")
        sel_date = st.date_input("اختر التاريخ", datetime.now()).strftime('%Y-%m-%d')
        cust_df = st.session_state.sales_df[st.session_state.sales_df['date_only'] == sel_date]
        if not cust_df.empty:
            st.table(cust_df[['date', 'customer_name', 'customer_phone', 'item', 'amount', 'method']].rename(columns={'date':'الوقت','customer_name':'الزبون','customer_phone':'الهاتف','item':'الصنف','amount':'المبلغ','method':'الدفع'}))
        else: st.info("لا يوجد سجل لهذا اليوم")

    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("البيان"); a = st.number_input("المبلغ")
            if st.form_submit_button("حفظ المصروف"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                auto_save(); st.rerun()

    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
        with st.form("add"):
            n = st.text_input("الصنف"); b = st.text_input("سعر الشراء"); s = st.text_input("سعر البيع"); q = st.text_input("الكمية")
            if st.form_submit_button("حفظ الصنف"):
                st.session_state.inventory[n] = {"قسم": "خضار وفواكه", "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.rerun()
