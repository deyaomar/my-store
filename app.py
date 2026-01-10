import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

# 2. الدوال المساعدة
def format_num(val):
    try:
        val = float(val)
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

def clean_num(text):
    try:
        if text is None or text == "" or pd.isna(text): return 0.0
        cleaned = str(text).replace(',', '').replace('₪', '').strip()
        return float(cleaned)
    except: return 0.0

# 3. الربط مع جداول بيانات جوجل
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet_data(worksheet_name, columns):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df is None or df.empty: return pd.DataFrame(columns=columns)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame(columns=columns)

def sync_to_google():
    try:
        if st.session_state.inventory:
            inv_df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index().rename(columns={'index':'item'})
            conn.update(worksheet="Inventory", data=inv_df)
        conn.update(worksheet="Sales", data=st.session_state.sales_df)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        st.cache_data.clear()
        return True
    except: return False

# 4. إدارة البيانات (التحميل الأولي)
if 'inventory' not in st.session_state:
    inv_df = load_sheet_data("Inventory", ['item', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
    st.session_state.sales_df = load_sheet_data("Sales", ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])
    st.session_state.expenses_df = load_sheet_data("Expenses", ['date', 'reason', 'amount'])
    st.session_state.waste_df = load_sheet_data("Waste", ['date', 'item', 'qty', 'loss_value'])

# 5. التنسيق (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .report-card { background: #ffffff; padding: 20px; border-radius: 15px; border-right: 5px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom:10px; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# 6. نظام الدخول
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    with st.sidebar:
        st.markdown(f"<div style='text-align:center; padding:10px; background:#27ae60; color:white; border-radius:10px;'>أهلاً أبو عمر 👋<br>{datetime.now().strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
        menu = st.radio("القائمة الرئيسية", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
        
        if st.button("🔄 تحديث شامل من جوجل"):
            st.cache_data.clear()
            for key in ['inventory', 'sales_df', 'expenses_df', 'waste_df']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    # --- 📊 التقارير المالية (النسخة الكاملة مع الحذف) ---
    if menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التحليل المالي والتحكم</h1>", unsafe_allow_html=True)
        
        # ميزة الحذف الذكي في الأعلى
        with st.expander("🛠️ إدارة العمليات (تعديل/حذف خطأ)"):
            if not st.session_state.sales_df.empty:
                st.warning("تنبيه: حذف آخر عملية سيعيد الكمية للمخزن ويمسح الفاتورة من التقارير.")
                if st.button("🗑️ إلغاء آخر عملية بيع مسجلة"):
                    last_row = st.session_state.sales_df.iloc[-1]
                    item_name = last_row['item']
                    # استعادة المخزن
                    if item_name in st.session_state.inventory:
                        sell_price = st.session_state.inventory[item_name]['بيع']
                        qty_ret = clean_num(last_row['amount']) / sell_price
                        st.session_state.inventory[item_name]['كمية'] += qty_ret
                    # حذف السطر
                    st.session_state.sales_df = st.session_state.sales_df.iloc[:-1]
                    sync_to_google()
                    st.success(f"تم بنجاح إلغاء مبيعات {item_name} وتحديث المخزن.")
                    st.rerun()
            else:
                st.info("لا توجد مبيعات حالية للحذف.")

        # معالجة البيانات للتقارير
        df_s = st.session_state.sales_df.copy()
        df_s['date_dt'] = pd.to_datetime(df_s['date'], errors='coerce')
        df_s['amount'] = pd.to_numeric(df_s['amount'], errors='coerce').fillna(0)
        df_s['profit'] = pd.to_numeric(df_s['profit'], errors='coerce').fillna(0)
        
        now = datetime.now()
        today = now.date()
        this_week = today - timedelta(days=now.weekday() + 1) # بداية الأسبوع
        this_month = today.replace(day=1) # بداية الشهر

        # الحسابات
        d_sales = df_s[df_s['date_dt'].dt.date == today]['amount'].sum()
        w_sales = df_s[df_s['date_dt'].dt.date >= this_week]['amount'].sum()
        m_sales = df_s[df_s['date_dt'].dt.date >= this_month]['amount'].sum()
        
        total_raw_profit = df_s['profit'].sum()
        total_exp = pd.to_numeric(st.session_state.expenses_df['amount'], errors='coerce').sum() if not st.session_state.expenses_df.empty else 0
        net_profit = total_raw_profit - total_exp
        stock_val = sum(v['كمية'] * v['شراء'] for v in st.session_state.inventory.values())

        # العرض (كروت المبيعات)
        st.write("### 💰 إحصائيات المبيعات")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='report-card'><h5>مبيعات اليوم</h5><h2>{format_num(d_sales)} ₪</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h5>مبيعات الأسبوع</h5><h2>{format_num(w_sales)} ₪</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h5>مبيعات الشهر</h5><h2>{format_num(m_sales)} ₪</h2></div>", unsafe_allow_html=True)

        # العرض (كروت الأرباح والمخزن)
        st.write("### 💵 الأرباح والمخزون")
        c4, c5, c6 = st.columns(3)
        c4.markdown(f"<div class='report-card'><h5>قيمة المخزن (شراء)</h5><h2>{format_num(stock_val)} ₪</h2></div>", unsafe_allow_html=True)
        c5.markdown(f"<div class='report-card'><h5>إجمالي المصروفات</h5><h2 style='color:#e74c3c'>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)
        p_color = "#27ae60" if net_profit >= 0 else "#e74c3c"
        c6.markdown(f"<div class='report-card' style='border-color:{p_color}'><h5>صافي الربح العام</h5><h2 style='color:{p_color}'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)

        st.divider()
        st.write("### 📈 آخر العمليات")
        st.dataframe(df_s.sort_values(by='date_dt', ascending=False).drop(columns=['date_dt']), use_container_width=True)

    # --- 🛒 نقطة البيع ---
    elif menu == "🛒 نقطة البيع":
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
            
            if temp_bill and st.button("🚀 إتمام العملية وحفظ"):
                st.session_state.current_bill_items = temp_bill
                st.session_state.show_customer_form = True; st.rerun()
        else:
            c_n = st.text_input("اسم الزبون", value="زبون محل")
            if st.button("✅ تأكيد البيع"):
                bid = str(uuid.uuid4())[:8]
                date_str = datetime.now().strftime("%Y-%m-%d")
                for e in st.session_state.current_bill_items:
                    if e["item"] in st.session_state.inventory:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': date_str, 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': '', 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                sync_to_google()
                st.session_state.show_customer_form = False; st.rerun()

    # --- باقي الأقسام ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h2 class='main-title'>📦 إدارة المخزن</h2>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame.from_dict(st.session_state.inventory, orient='index'), use_container_width=True)

    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("البيان"); a = st.number_input("المبلغ")
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                sync_to_google(); st.rerun()

    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إضافة صنف جديد</h1>", unsafe_allow_html=True)
        with st.form("add"):
            n = st.text_input("اسم الصنف"); b = st.text_input("شراء"); s = st.text_input("بيع"); q = st.text_input("كمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {"شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                sync_to_google(); st.rerun()
