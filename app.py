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
def format_num(val):
    return f"{val:,.2f}"

# 3. الاتصال والمزامنة
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_to_google():
    try:
        inv_data = [{'item': k, **v} for k, v in st.session_state.inventory.items()]
        conn.update(worksheet="Inventory", data=pd.DataFrame(inv_data))
        conn.update(worksheet="Sales", data=st.session_state.sales_df)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        st.cache_data.clear()
        return True
    except: return False

# 4. تحميل البيانات
if 'inventory' not in st.session_state:
    try:
        inv_df = conn.read(worksheet="Inventory", ttl=0)
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        st.session_state.sales_df = conn.read(worksheet="Sales", ttl=0)
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        st.session_state.inventory = {}
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount', 'id'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# 5. القائمة الجانبية
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث البيانات"): st.rerun()

# --- 🛒 نقطة البيع ---
if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    if 'pay_method_selected' not in st.session_state: st.session_state.pay_method_selected = "نقدي 💵"
    
    col_m1, col_m2 = st.columns(2)
    if col_m1.button("💵 نقدي", use_container_width=True): 
        st.session_state.pay_method_selected = "نقدي 💵"
        st.rerun()
    if col_m2.button("📱 تطبيق", use_container_width=True): 
        st.session_state.pay_method_selected = "تطبيق 📱"
        st.rerun()

    st.info(f"طريقة الدفع الحالية: {st.session_state.pay_method_selected}")
    search = st.text_input("🔍 ابحث عن صنف لبيعه...")
    
    items = {k: v for k, v in st.session_state.inventory.items() if search.lower() in k.lower()}
    temp_bill = []
    cols = st.columns(4)
    for idx, (it, data) in enumerate(items.items()):
        with cols[idx % 4]:
            st.markdown(f"**{it}**\n{data['بيع']} ₪")
            val = st.number_input(f"المبلغ", key=f"s_{it}", min_value=0.0, value=None, placeholder="₪")
            if val:
                qty = val / data['بيع']
                profit = (data['بيع'] - data['شراء']) * qty
                temp_bill.append({'item': it, 'qty': qty, 'amount': val, 'profit': profit})

    if temp_bill:
        if st.button("✅ إتمام البيع", use_container_width=True):
            bid = str(uuid.uuid4())[:8]
            for row in temp_bill:
                st.session_state.inventory[row['item']]['كمية'] -= row['qty']
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': row['item'], 'amount': row['amount'], 'profit': row['profit'], 'method': st.session_state.pay_method_selected, 'customer_name': "زبون", 'bill_id': bid}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            sync_to_google(); st.success("تم البيع!"); st.rerun()

# --- 📦 المخزن ---
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
    search_stock = st.text_input("🔍 بحث في المخزن")
    cols = st.columns(3)
    for idx, (it, data) in enumerate(st.session_state.inventory.items()):
        if search_stock.lower() in it.lower():
            with cols[idx % 3]:
                st.markdown(f"<div class='stock-card'><b>{it}</b><br>الكمية: {data['كمية']}<br>بيع: {data['بيع']} ₪</div>", unsafe_allow_html=True)

# --- 📊 التقارير ---
elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
    raw_profit = st.session_state.sales_df['profit'].sum() if not st.session_state.sales_df.empty else 0
    total_exp = pd.to_numeric(st.session_state.expenses_df['amount'], errors='coerce').sum() if not st.session_state.expenses_df.empty else 0
    st.columns(2)[0].metric("صافي الأرباح", f"{raw_profit - total_exp:.2f} ₪")
    st.table(st.session_state.sales_df.tail(10))

# --- 💸 المصروفات (تم الإصلاح هنا) ---
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    total_exp = pd.to_numeric(st.session_state.expenses_df['amount'], errors='coerce').sum() if not st.session_state.expenses_df.empty else 0
    st.markdown(f"<div class='report-card'><h5>إجمالي المصروفات</h5><h2>{total_exp:.2f} ₪</h2></div>", unsafe_allow_html=True)
    
    with st.form("exp_form", clear_on_submit=True):
        r = st.text_input("البيان")
        a = st.number_input("المبلغ", min_value=0.0, value=None, placeholder="0.0")
        if st.form_submit_button("💾 حفظ"):
            if r and a:
                new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': float(a), 'id': str(uuid.uuid4())[:6]}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
                sync_to_google(); st.rerun()

    for idx, row in st.session_state.expenses_df.iterrows():
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{row['reason']}**")
        c2.write(f"{row['amount']} ₪")
        if c3.button("🗑️", key=f"del_{idx}"):
            st.session_state.expenses_df = st.session_state.expenses_df.drop(idx)
            sync_to_google(); st.rerun()

# --- ⚙️ الإعدادات (تم الإصلاح والترتيب هنا) ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["➕ صنف جديد", "📂 الأقسام", "🗑️ حذف صنف"])
    
    with t1:
        with st.form("add_new"):
            name = st.text_input("اسم الصنف")
            c1, c2, c3 = st.columns(3)
            bp = c1.number_input("شراء", value=None, placeholder="0.0")
            sp = c2.number_input("بيع", value=None, placeholder="0.0")
            qt = c3.number_input("كمية", value=None, placeholder="0.0")
            cat = st.selectbox("القسم", st.session_state.CATEGORIES)
            if st.form_submit_button("حفظ"):
                if name and bp and sp and qt:
                    st.session_state.inventory[name] = {'شراء': bp, 'بيع': sp, 'كمية': qt, 'قسم': cat}
                    sync_to_google(); st.success("تم!"); st.rerun()
    
    with t2:
        st.write(st.session_state.CATEGORIES)
        new_c = st.text_input("قسم جديد")
        if st.button("إضافة"):
            st.session_state.CATEGORIES.append(new_c); st.rerun()

    with t3:
        to_del = st.selectbox("اختر للحذف", list(st.session_state.inventory.keys()))
        if st.button("حذف نهائي"):
            del st.session_state.inventory[to_del]; sync_to_google(); st.rerun()
