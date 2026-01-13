import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-right: 8px solid #27ae60; padding-right: 15px; margin-bottom: 25px; }
    .stock-card { background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; transition: 0.3s; }
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال المساعدة
def clean_num(val):
    try:
        if val is None or val == "" or pd.isna(val): return 0.0
        return float(str(val).replace(',', '').replace('₪', '').strip())
    except: return 0.0

def format_num(val):
    return f"{clean_num(val):,.2f}"

# 3. الاتصال وقاعدة البيانات
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_to_google():
    try:
        inv_data = [{'item': k, **v} for k, v in st.session_state.inventory.items()]
        sales_to_save = st.session_state.sales_df.copy()
        if not sales_to_save.empty:
            sales_to_save['profit'] = pd.to_numeric(sales_to_save['profit'], errors='coerce').fillna(0).round(2)
            sales_to_save['amount'] = pd.to_numeric(sales_to_save['amount'], errors='coerce').fillna(0).round(2)

        conn.update(worksheet="Inventory", data=pd.DataFrame(inv_data))
        conn.update(worksheet="Sales", data=sales_to_save)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"خطأ في المزامنة: {e}")
        return False

# 4. تحميل البيانات
if 'inventory' not in st.session_state:
    try:
        inv_df = conn.read(worksheet="Inventory", ttl=0)
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        s_df = conn.read(worksheet="Sales", ttl=0)
        st.session_state.sales_df = s_df if not s_df.empty else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        st.session_state.inventory = {}
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount', 'id'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث البيانات"): st.rerun()

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
            st.session_state.show_customer_form = True
            st.rerun()
    else:
        c_n = st.text_input("اسم الزبون")
        c_p = st.text_input("رقم الهاتف")
        if st.button("✅ تأكيد"):
            bid = str(uuid.uuid4())[:8]
            for e in st.session_state.current_bill_items:
                st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': c_p, 'bill_id': bid}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            sync_to_google()
            st.session_state.show_customer_form = False
            st.rerun()

# --- 📦 المخزن والجرد ---
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
    
    with st.expander("➕ إضافة صنف جديد للمحل"):
        with st.form("add_new_item"):
            n_name = st.text_input("اسم الصنف")
            n_cat = st.selectbox("القسم", st.session_state.CATEGORIES)
            n_buy = st.number_input("سعر الشراء", min_value=0.0)
            n_sell = st.number_input("سعر البيع", min_value=0.0)
            n_qty = st.number_input("الكمية المتوفرة", min_value=0.0)
            if st.form_submit_button("إضافة الصنف للمخزن"):
                if n_name:
                    st.session_state.inventory[n_name] = {'قسم': n_cat, 'شراء': n_buy, 'بيع': n_sell, 'كمية': n_qty}
                    sync_to_google()
                    st.success(f"تمت إضافة {n_name}")
                    st.rerun()

    st.divider()

    if st.session_state.inventory:
        search_stock = st.text_input("🔍 ابحث في المخزن أو زود الكمية...")
        cols = st.columns(3)
        for idx, (it, data) in enumerate(st.session_state.inventory.items()):
            if search_stock.lower() in it.lower():
                qty = clean_num(data.get('كمية', 0))
                buy_p = clean_num(data.get('شراء', 0))
                sell_p = clean_num(data.get('بيع', 0))
                
                with cols[idx % 3]:
                    st.markdown(f"""<div class="stock-card">
                        <b>{it}</b><br>
                        الكمية: {qty} | الشراء: {buy_p} | <span style='color:green;'>البيع: {sell_p}</span>
                    </div>""", unsafe_allow_html=True)
                    with st.expander("تعديل / تزويد الكمية"):
                        add_q = st.number_input("إضافة كمية جديدة", min_value=0.0, key=f"add_{it}")
                        if st.button("تحديث الكمية", key=f"up_{it}"):
                            st.session_state.inventory[it]['كمية'] += add_q
                            sync_to_google()
                            st.rerun()
                        st.divider()
                        nq = st.number_input("تعديل الكمية الكلية", value=qty, key=f"q_{it}")
                        nb = st.number_input("سعر الشراء", value=buy_p, key=f"b_{it}")
                        ns = st.number_input("سعر البيع", value=sell_p, key=f"s_{it}")
                        if st.button("حفظ التعديلات", key=f"btn_{it}"):
                            st.session_state.inventory[it].update({'كمية': nq, 'شراء': nb, 'بيع': ns})
                            sync_to_google()
                            st.rerun()

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
        r = st.text_input("البيان")
        a = st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            new_e = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'reason': r, 'amount': a}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
            sync_to_google()
            st.rerun()
    st.table(st.session_state.expenses_df.sort_values(by='date', ascending=False))

# --- ⚙️ الإعدادات ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
    if st.button("🛠️ إصلاح تضارب البيانات"):
        sync_to_google()
        st.success("تمت المزامنة والإصلاح!")
