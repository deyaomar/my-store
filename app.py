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
            st.session_state.inventory = inv_df.set_index(inv_df.columns[0]).to_dict('index')
        except: st.session_state.inventory = {}
    else: st.session_state.inventory = {}

if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

def auto_save():
    if st.session_state.inventory:
        pd.DataFrame.from_dict(st.session_state.inventory, orient='index').to_csv('inventory_final.csv', index=True)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)

# 3. واجهة المستخدم (التنسيق)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-left: 3px solid #27ae60; min-width: 300px !important; }
    .sidebar-user { background-color: #1a1a1a; padding: 25px 10px; border-radius: 15px; margin: 15px 10px; border: 2px solid #27ae60; text-align: center; color: white !important; font-weight: 900; font-size: 24px; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { background-color: #1a1a1a !important; color: #ffffff !important; padding: 15px 20px !important; border-radius: 12px !important; margin-bottom: 10px !important; font-size: 18px !important; font-weight: 900 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #27ae60 !important; border: 1px solid white; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > span:first-child { display: none !important; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
    .report-card { background: #f9f9f9; padding: 20px; border-radius: 15px; border-right: 5px solid #27ae60; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
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

    # --- 🛒 نقطة البيع (مختصرة) ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>")
        c1, c2 = st.columns([1, 2]); p_meth = c1.selectbox("💳 الدفع", ["تطبيق", "نقداً"]); search_q = c2.text_input("🔍 ابحث...")
        bill_items = []
        for it, data in st.session_state.inventory.items():
            if not search_q or search_q in it:
                st.markdown(f"<div style='border:1px solid #ddd; padding:10px; border-radius:10px;'><b>{it}</b> | {data['بيع']} ₪</div>", unsafe_allow_html=True)
                mc1, mc2 = st.columns(2); mode = mc1.radio("بـ", ["₪", "كجم"], key=f"m_{it}", horizontal=True); val = clean_num(mc2.text_input("المقدار", key=f"v_{it}"))
                if val > 0:
                    q = val if mode == "كجم" else val / data["بيع"]
                    bill_items.append({"item": it, "qty": q, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * q})
        if bill_items and st.button("🚀 إتمام العملية"):
            bid = str(uuid.uuid4())[:8]
            for e in bill_items:
                st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': p_meth, 'bill_id': bid}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            auto_save(); st.rerun()

    # --- 📦 المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>")
        t1, t2 = st.tabs(["📋 الرصيد", "🗑️ تسجيل تالف"])
        with t1: st.dataframe(pd.DataFrame([{"الصنف": k, "الكمية": v['كمية']} for k, v in st.session_state.inventory.items()]), use_container_width=True)
        with t2:
            with st.form("waste"):
                it = st.selectbox("الصنف", list(st.session_state.inventory.keys()))
                qty = st.number_input("الكمية التالفة", min_value=0.0)
                if st.form_submit_button("تسجيل"):
                    loss = qty * st.session_state.inventory[it]['شراء']
                    st.session_state.inventory[it]['كمية'] -= qty
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': it, 'qty': qty, 'loss_value': loss}])], ignore_index=True)
                    auto_save(); st.rerun()

    # --- 💸 المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>")
        with st.form("exp"):
            r = st.text_input("البيان"); a = st.number_input("المبلغ"); c = st.selectbox("التصنيف", ["عمال", "إيجار", "أخرى"])
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'category': c}])], ignore_index=True)
                auto_save(); st.rerun()
        st.dataframe(st.session_state.expenses_df)

    # --- 📊 التقارير المالية (تعديل أبو عمر المطلوب) ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية والتحليل الأسبوعي</h1>", unsafe_allow_html=True)
        
        # تجهيز البيانات والتواريخ
        today = datetime.now().strftime("%Y-%m-%d")
        last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # تحويل تواريخ المبيعات والتالف لنوع تاريخ للمقارنة
        st.session_state.sales_df['date_only'] = pd.to_datetime(st.session_state.sales_df['date']).dt.strftime('%Y-%m-%d')
        st.session_state.waste_df['date_only'] = pd.to_datetime(st.session_state.waste_df['date']).dt.strftime('%Y-%m-%d')
        
        # 1. المبيعات اليومية والاسبوعية
        daily_sales = st.session_state.sales_df[st.session_state.sales_df['date_only'] == today]['amount'].sum()
        weekly_sales = st.session_state.sales_df[st.session_state.sales_df['date_only'] >= last_week]['amount'].sum()
        
        # 2. رأس المال الأساسي (قيمة البضاعة الموجودة حالياً بالمحل بسعر الشراء)
        capital_in_stock = sum(v['كمية'] * v['شراء'] for v in st.session_state.inventory.values())
        
        # 3. صافي الأرباح والتالف (الكلي)
        total_profit_raw = st.session_state.sales_df['profit'].sum()
        total_waste = st.session_state.waste_df['loss_value'].sum()
        total_exp = st.session_state.expenses_df['amount'].sum()
        net_profit = total_profit_raw - total_waste - total_exp

        # 4. تحليل الأصناف (الأسبوعي)
        weekly_data = st.session_state.sales_df[st.session_state.sales_df['date_only'] >= last_week]
        weekly_waste = st.session_state.waste_df[st.session_state.waste_df['date_only'] >= last_week]
        
        best_item = weekly_data.groupby('item')['profit'].sum().idxmax() if not weekly_data.empty else "لا يوجد"
        worst_waste_item = weekly_waste.groupby('item')['qty'].sum().idxmax() if not weekly_waste.empty else "لا يوجد"

        # عرض النتائج في بطاقات احترافية
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='report-card'><h3>💰 مبيعات اليوم</h3><h2>{format_num(daily_sales)} ₪</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='report-card'><h3>📅 مبيعات الأسبوع</h3><h2>{format_num(weekly_sales)} ₪</h2></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='report-card'><h3>🏗️ رأس المال الحالي</h3><h2>{format_num(capital_in_stock)} ₪</h2><small>قيمة البضاعة بالمحل</small></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col4, col5, col6 = st.columns(3)
        with col4:
            color = "#27ae60" if net_profit >= 0 else "#e74c3c"
            st.markdown(f"<div class='report-card' style='border-color:{color}'><h3>💵 صافي الأرباح</h3><h2 style='color:{color}'>{format_num(net_profit)} ₪</h2><small>بعد خصم التالف والمصروفات</small></div>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<div class='report-card' style='border-color:#e74c3c'><h3>🗑️ إجمالي التالف</h3><h2 style='color:#e74c3c'>{format_num(total_waste)} ₪</h2></div>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<div class='report-card'><h3>📉 إجمالي المصروفات</h3><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)

        st.divider()
        st.markdown("### 🏆 تحليل الأسبوع (آخر 7 أيام)")
        c_a, c_b = st.columns(2)
        c_a.success(f"🔝 **أفضل صنف ربحاً هذا الأسبوع:** {best_item}")
        c_b.error(f"⚠️ **أكثر صنف تالف (كمية) هذا الأسبوع:** {worst_waste_item}")

    # --- ⚙️ الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>")
        with st.form("add"):
            n = st.text_input("اسم الصنف"); cat = st.selectbox("القسم", st.session_state.categories)
            b = st.text_input("سعر الشراء"); s = st.text_input("سعر البيع"); q = st.text_input("الكمية")
            if st.form_submit_button("حفظ"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.rerun()
