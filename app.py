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
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { background-color: #1a1a1a !important; color: #ffffff !important; padding: 15px 20px !important; border-radius: 12px !important; margin-bottom: 10px !important; font-size: 18px !important; font-weight: 900 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #27ae60 !important; border: 1px solid white; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > span:first-child { display: none !important; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
    .expense-box { background-color: #fff5f5; border: 1px solid #feb2b2; padding: 20px; border-radius: 15px; }
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
        # (باقي كود نقطة البيع المعتمد سابقاً...)
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
                        st.markdown(f"<div style='border:1px solid #ddd; padding:10px; border-radius:10px;'><b>{it}</b> | {data['بيع']} ₪</div>", unsafe_allow_html=True)
                        mc1, mc2 = st.columns(2); mode = mc1.radio("بـ", ["₪", "كجم"], key=f"m_{it}", horizontal=True)
                        val = clean_num(mc2.text_input("المقدار", key=f"v_{it}"))
                        if val > 0:
                            q = val if mode == "كجم" else val / data["بيع"]
                            bill_items.append({"item": it, "qty": q, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * q})
        if bill_items:
            if st.button("🚀 إتمام العملية", type="primary", use_container_width=True):
                bid = str(uuid.uuid4())[:8]
                for e in bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': p_meth, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.rerun()

    # --- 📦 المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        # (باقي كود المخزن والجرد مع التالف المعتمد سابقاً...)
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

    # --- 💸 المصروفات (تعديل أبو عمر الجديد) ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>", unsafe_allow_html=True)
        
        # نموذج إضافة مصروف
        with st.form("expense_form"):
            st.markdown("### 📝 إضافة مصروف جديد")
            c1, c2, c3 = st.columns([2, 1, 1])
            res = c1.text_input("بيان المصروف (مثلاً: فاتورة كهرباء، أجرة عمال)")
            amt = c2.number_input("المبلغ (₪)", min_value=0.0, step=1.0)
            cat = c3.selectbox("التصنيف", ["أجور عمال", "إيجار", "كهرباء ومياه", "نقل وتوصيل", "أخرى"])
            
            if st.form_submit_button("💾 حفظ المصروف"):
                if res and amt > 0:
                    new_exp = {
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'reason': res,
                        'amount': amt,
                        'category': cat
                    }
                    st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                    auto_save()
                    st.success(f"تم تسجيل {amt} ₪ بنجاح")
                    st.rerun()
                else:
                    st.error("يرجى إدخال البيان والمبلغ")

        st.markdown("### 📜 سجل المصروفات السابقة")
        st.dataframe(st.session_state.expenses_df.sort_index(ascending=False), use_container_width=True)
        
        total_exp = st.session_state.expenses_df['amount'].sum()
        st.error(f"⚠️ إجمالي المصروفات الكلي: {format_num(total_exp)} ₪")

    # --- 📊 التقارير المالية (الربط النهائي) ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية والأرباح</h1>", unsafe_allow_html=True)
        
        sales_profit = st.session_state.sales_df['profit'].sum()
        total_waste = st.session_state.waste_df['loss_value'].sum()
        total_exp = st.session_state.expenses_df['amount'].sum()
        
        # المعادلة الذهبية لأبو عمر
        net_profit = sales_profit - total_waste - total_exp

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("إجمالي مبيعاتك", f"{format_num(st.session_state.sales_df['amount'].sum())} ₪")
        col2.metric("أرباح المبيعات", f"{format_num(sales_profit)} ₪")
        col3.metric("المصروفات + التالف", f"{format_num(total_exp + total_waste)} ₪", delta_color="inverse")
        
        # تلوين صافي الربح حسب الحالة
        if net_profit >= 0:
            col4.success(f"صافي الربح النهائي: {format_num(net_profit)} ₪")
        else:
            col4.error(f"صافي الخسارة: {format_num(net_profit)} ₪")
            
        st.divider()
        st.info("💡 يتم حساب صافي الربح من خلال خصم (قيمة التالف + المصروفات) من (أرباح مبيعاتك).")

    # --- ⚙️ الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        with st.form("set"):
            n = st.text_input("الصنف"); cat = st.selectbox("القسم", st.session_state.categories)
            b = st.text_input("شراء"); s = st.text_input("بيع"); q = st.text_input("كمية")
            if st.form_submit_button("حفظ"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.rerun()
