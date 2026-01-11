import streamlit as st
import pandas as pd
from datetime import datetime
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
    .stock-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال المساعدة
def format_num(val):
    return f"{val:,.0f}"

# 3. الاتصال بقاعدة البيانات
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
    except Exception as e:
        st.error(f"خطأ في المزامنة: {e}")
        return False

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
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'phone', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# 5. القائمة الجانبية
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])

# --- 🛒 قسم نقطة البيع ---
if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 نظام البيع السريع</h1>", unsafe_allow_html=True)
    if 'cart' not in st.session_state: st.session_state.cart = {}

    c1, c2 = st.columns([1, 2])
    cat_sel = c1.selectbox("📂 القسم", ["الكل"] + st.session_state.CATEGORIES)
    search = c2.text_input("🔍 ابحث عن صنف...")
    
    items = {k: v for k, v in st.session_state.inventory.items() if (cat_sel == "الكل" or v.get('قسم') == cat_sel) and (search.lower() in k.lower())}
    
    cols = st.columns(4)
    for idx, (it, data) in enumerate(items.items()):
        with cols[idx % 4]:
            st.markdown(f"<div style='background:#fff; border-top: 5px solid #27ae60; padding:10px; border-radius:10px; text-align:center;'><b>{it}</b><br><small>متوفر: {int(data['كمية'])}</small></div>", unsafe_allow_html=True)
            if st.button(f"➕ إضافة", key=f"add_{it}", use_container_width=True):
                if data['كمية'] > 0:
                    st.session_state.cart[it] = {'price': float(data['بيع']), 'cost': float(data['شراء'])}
                    st.rerun()

    if st.session_state.cart:
        st.markdown("---")
        total_bill = 0.0
        for item_name, info in list(st.session_state.cart.items()):
            col1, col2, col3 = st.columns([4, 3, 1])
            col1.write(f"**{item_name}**")
            p = col2.number_input("المبلغ", min_value=0, value=int(info['price']), key=f"p_{item_name}", label_visibility="collapsed")
            st.session_state.cart[item_name]['price'] = p
            total_bill += p
            if col3.button("❌", key=f"del_{item_name}"):
                del st.session_state.cart[item_name]
                st.rerun()

        st.markdown(f"<h2 style='text-align:center;'>الإجمالي: {int(total_bill)} ₪</h2>", unsafe_allow_html=True)
        pay_method = st.radio("💰 طريقة الدفع:", ["نقدي", "تطبيق"], horizontal=True)
        cust_name = st.text_input("الاسم (للتطبيق)")
        cust_phone = st.text_input("الجوال (للتطبيق)")

        if st.button("🚀 حفظ الفاتورة وإنهاء", use_container_width=True, type="primary"):
            if pay_method == "تطبيق" and (not cust_name or not cust_phone):
                st.error("❌ للدفع بالتطبيق يجب تسجيل بيانات الزبون")
            else:
                bid = str(uuid.uuid4())[:8]
                sales_list = []
                for name, details in st.session_state.cart.items():
                    # حساب الربح بناءً على السعر المدخل يدوياً
                    cost = float(st.session_state.inventory[name]['شراء'])
                    sold_at = float(details['price'])
                    st.session_state.inventory[name]['كمية'] -= 1
                    
                    sales_list.append({
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'item': name, 'amount': sold_at, 
                        'profit': (sold_at - cost), # هنا تصحيح الربح
                        'method': pay_method, 'customer_name': cust_name if cust_name else "زبون محل",
                        'phone': cust_phone if cust_phone else "-", 'bill_id': bid
                    })
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame(sales_list)], ignore_index=True)
                if sync_to_google():
                    st.session_state.cart = {}
                    st.rerun()

# --- 📊 قسم التقارير المالية (التصحيح الرئيسي هنا) ---
elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقرير المالي الدقيق - أبو عمر</h1>", unsafe_allow_html=True)

    # تجهيز البيانات وتوحيد التواريخ
    df_s = st.session_state.sales_df.copy()
    df_s['date'] = pd.to_datetime(df_s['date']).dt.date
    df_e = st.session_state.expenses_df.copy()
    if not df_e.empty: df_e['date'] = pd.to_datetime(df_e['date']).dt.date
    df_w = st.session_state.waste_df.copy()
    if not df_w.empty: df_w['date'] = pd.to_datetime(df_w['date']).dt.date

    today = datetime.now().date()

    # حسابات اليوم
    daily_sales = df_s[df_s['date'] == today]
    t_sales = daily_sales['amount'].sum()
    t_gross_profit = daily_sales['profit'].sum() # إجمالي ربح المبيعات
    
    t_exp = df_e[df_e['date'] == today]['amount'].sum() if not df_e.empty else 0
    t_waste = df_w[df_w['date'] == today]['loss_value'].sum() if not df_w.empty else 0
    
    # صافي الربح = أرباح المبيعات - المصاريف - قيمة التوالف
    t_net_profit = t_gross_profit - t_exp - t_waste

    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي مبيعات اليوم", f"{int(t_sales)} ₪")
    c2.metric("صافي الربح الخالص", f"{int(t_net_profit)} ₪", delta=f"{int(t_net_profit)} ₪")
    c3.metric("مصاريف وتوالف", f"{int(t_exp + t_waste)} ₪")

    st.markdown("---")
    # عرض رأس المال الحالي
    current_cap = sum(float(v['شراء']) * float(v['كمية']) for v in st.session_state.inventory.values())
    st.info(f"💰 قيمة البضاعة الحالية في المخزن (رأس المال): {format_num(current_cap)} ₪")
    
    st.write("### 📝 سجل مبيعات اليوم")
    st.dataframe(daily_sales[['item', 'amount', 'profit', 'method']], use_container_width=True)

# (بقية الأقسام: المخزن، المصروفات، الإعدادات تبقى كما هي في كودك)
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 حالة المخزن</h1>", unsafe_allow_html=True)
    # كود المخزن الخاص بك...
    if st.session_state.inventory:
        cols = st.columns(3)
        for idx, (it, data) in enumerate(st.session_state.inventory.items()):
            with cols[idx % 3]:
                st.markdown(f"<div class='stock-card'><h3>{it}</h3><p>المتبقي: {int(data['كمية'])}</p><h4>{data['بيع']} ₪</h4></div>", unsafe_allow_html=True)
                with st.expander("تعديل الكمية"):
                    new_q = st.number_input("الكمية الجديدة", value=int(data['كمية']), key=f"inv_{it}")
                    if st.button("حفظ", key=f"btn_{it}"):
                        st.session_state.inventory[it]['كمية'] = new_q
                        sync_to_google(); st.rerun()

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_form"):
        reason = st.text_input("البيان")
        amt = st.number_input("المبلغ", min_value=0)
        if st.form_submit_button("حفظ"):
            new_row = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': reason, 'amount': amt}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_row])], ignore_index=True)
            sync_to_google(); st.rerun()

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
    # كود الإعدادات الخاص بك لإضافة صنف جديد...
    with st.form("new_item"):
        n = st.text_input("اسم الصنف")
        cat = st.selectbox("القسم", st.session_state.CATEGORIES)
        b = st.number_input("سعر الشراء")
        s = st.number_input("سعر البيع")
        q = st.number_input("الكمية")
        if st.form_submit_button("إضافة"):
            st.session_state.inventory[n] = {'قسم': cat, 'شراء': b, 'بيع': s, 'كمية': q}
            sync_to_google(); st.rerun()
