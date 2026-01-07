import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026 - التقارير المتقدمة", layout="wide", page_icon="📊")

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
                if c not in df.columns: df[c] = 0.0 if any(x in c for x in ['amount', 'profit', 'loss', 'qty']) else ""
            st.session_state[state_key] = df
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv('inventory_final.csv', index_col=0).to_dict('index') if os.path.exists('inventory_final.csv') else {}
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv('inventory_final.csv')
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. واجهة المستخدم
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; margin-bottom: 20px; font-weight: 900; }
    .report-card { background-color: #f8f9fa; padding: 15px; border-radius: 12px; border-right: 5px solid #27ae60; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 4. النظام
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول النظام</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1,1])
    with col:
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    st.sidebar.markdown(f"<div style='text-align:center; color:#27ae60; font-weight:900; font-size:24px;'>أبو عمر 👋</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة", ["📊 التقارير المالية", "🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 📊 التقارير المالية (التحديث المطلوب) ---
    if menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 تقارير المبيعات والأرباح</h1>", unsafe_allow_html=True)
        
        # تجهيز بيانات اليوم
        today_str = datetime.now().strftime("%Y-%m-%d")
        sales_df = st.session_state.sales_df.copy()
        sales_df['date_dt'] = pd.to_datetime(sales_df['date']).dt.strftime("%Y-%m-%d")
        
        today_sales = sales_df[sales_df['date_dt'] == today_str]
        
        # 1. إجمالي مبيعات اليوم (بصمة أبو عمر)
        st.markdown(f"""
        <div style="background-color:#2c3e50; color:white; padding:20px; border-radius:15px; text-align:center; margin-bottom:25px;">
            <h2 style="margin:0;">إجمالي مبيعات اليوم ({today_str})</h2>
            <h1 style="font-size:50px; color:#27ae60; margin:10px 0;">{format_num(today_sales['amount'].sum())} ₪</h1>
        </div>
        """, unsafe_allow_html=True)

        # 2. تفصيل (نقدي / تطبيق)
        col_m1, col_m2 = st.columns(2)
        
        cash_total = today_sales[today_sales['method'] == "نقداً"]['amount'].sum()
        app_total = today_sales[today_sales['method'] == "تطبيق"]['amount'].sum()
        
        with col_m1:
            st.markdown(f"""<div class='report-card'><h3>💰 الكاش (نقداً)</h3><h2>{format_num(cash_total)} ₪</h2></div>""", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""<div class='report-card'><h3>📱 التطبيق</h3><h2>{format_num(app_total)} ₪</h2></div>""", unsafe_allow_html=True)

        st.divider()
        
        # 3. تقرير الأرباح الشامل
        st.subheader("📈 ملخص الأرباح والخسائر التراكمي")
        tp = sales_df['profit'].sum()
        te = st.session_state.expenses_df['amount'].sum()
        tw = st.session_state.waste_df['loss_value'].sum()
        ta = st.session_state.adjust_df['loss_value'].sum()
        net = tp - te - tw - ta
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي ربح البيع", f"{format_num(tp)} ₪")
        c2.metric("المصروفات", f"{format_num(te)} ₪")
        c3.metric("العجز والتالف", f"{format_num(tw + ta)} ₪")
        c4.metric("صافي الربح النهائي", f"{format_num(net)} ₪")

        st.divider()
        st.subheader("📋 تفاصيل عمليات اليوم")
        if not today_sales.empty:
            st.dataframe(today_sales[['date', 'item', 'amount', 'method', 'customer_name']], use_container_width=True)
        else:
            st.info("لا توجد مبيعات مسجلة لهذا اليوم حتى الآن.")

    # --- باقي الأقسام (كما هي في النسخة المستقرة السابقة) ---
    elif menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
        # (نفس كود البيع السابق المستقر)
        col_h1, col_h2 = st.columns([3, 1])
        with col_h2: st.session_state.p_method = st.radio("طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
        search_q = st.text_input("🔍 ابحث عن صنف...")
        
        bill_items = []
        for cat in st.session_state.categories:
            items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            if search_q: items = {k: v for k, v in items.items() if search_q in k}
            if items:
                with st.expander(f"📂 {cat}", expanded=True):
                    for item, data in items.items():
                        c1, c2, c3 = st.columns([2, 1, 2])
                        c1.markdown(f"**{item}** \n<small>متوفر: {format_num(data['كمية'])}</small>", unsafe_allow_html=True)
                        mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item}", horizontal=True)
                        val = clean_num(c3.text_input("المقدار", key=f"v_{item}"))
                        if val > 0:
                            qty = val if mode == "كجم" else val / data["بيع"]
                            bill_items.append({"item": item, "qty": qty, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * qty})
        
        if st.button("🚀 إتمام البيع", type="primary"):
            if bill_items:
                b_id = str(uuid.uuid4())[:8]
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                for e in bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': now, 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.success("تم الحفظ بنجاح!"); st.rerun()

    # (باقي الأقسام: المخزن، المصروفات، الإعدادات تبقى كما هي لضمان استقرار النظام)
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(st.session_state.inventory).T[['قسم', 'كمية']], use_container_width=True)
    
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("البيان")
            a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                auto_save(); st.rerun()

    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        with st.form("new_item"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            c1, c2, c3 = st.columns(3)
            b = clean_num(c1.text_input("شراء"))
            s = clean_num(c2.text_input("بيع"))
            q = clean_num(c3.text_input("كمية"))
            if st.form_submit_button("حفظ"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": b, "بيع": s, "كمية": q}
                auto_save(); st.rerun()
