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
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .stock-card { background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 20px; }
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
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# 5. القائمة الجانبية
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث البيانات"): st.rerun()

# --- المنطق الرئيسي ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    cat_sel = c1.selectbox("📂 القسم", ["الكل"] + st.session_state.CATEGORIES)
    search = c2.text_input("🔍 ابحث عن صنف لبيعه...")
    
    items_to_sell = st.session_state.inventory.items()
    if cat_sel != "الكل":
        items_to_sell = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat_sel}.items()
    
    items = {k: v for k, v in items_to_sell if search.lower() in k.lower()}
    cols = st.columns(4)
    temp_bill = []
    
    for idx, (it, data) in enumerate(items.items()):
        with cols[idx % 4]:
            st.markdown(f"<div style='background:#fff; border:1px solid #ddd; padding:10px; border-radius:10px; text-align:center;'><b>{it}</b><br><span style='color:green;'>{data['بيع']} ₪</span><br><small>متوفر: {data['كمية']}</small></div>", unsafe_allow_html=True)
            val = st.number_input(f"الكمية ({it})", key=f"v_{it}", min_value=0.0, step=0.1)
            if val > 0:
                temp_bill.append({'item': it, 'qty': val, 'amount': val * data['بيع'], 'profit': (data['بيع'] - data['شراء']) * val})
    
    if temp_bill and st.button("✅ إتمام البيع وحفظ الفاتورة", use_container_width=True):
        bid = str(uuid.uuid4())[:8]
        for row in temp_bill:
            st.session_state.inventory[row['item']]['كمية'] -= row['qty']
            new_row = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': row['item'], 'amount': row['amount'], 'profit': row['profit'], 'method': 'نقدي', 'customer_name': 'زبون محل', 'bill_id': bid}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
        sync_to_google(); st.success("تمت العملية بنجاح!"); st.rerun()

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقرير المالي الدقيق - أبو عمر</h1>", unsafe_allow_html=True)
    
    # الحصول على تاريخ اليوم وتوحيد التنسيق
    today_dt = datetime.now().date()

    # دالة ذكية لتصفية البيانات حسب التاريخ مهما كان تنسيقه
    def get_today_data(df, date_col):
        if df is None or df.empty:
            return pd.DataFrame()
        temp = df.copy()
        # تحويل العمود لتاريخ مع معالجة الأخطاء وتوحيد التنسيق
        temp[date_col] = pd.to_datetime(temp[date_col], errors='coerce').dt.date
        return temp[temp[date_col] == today_dt]

    # 1. حساب مبيعات وأرباح اليوم
    today_sales_df = get_today_data(st.session_state.sales_df, 'date')
    t_sales = pd.to_numeric(today_sales_df['amount'], errors='coerce').sum()
    t_gross_profit = pd.to_numeric(today_sales_df['profit'], errors='coerce').sum()

    # 2. حساب مصروفات اليوم (حصراً)
    today_exp_df = get_today_data(st.session_state.expenses_df, 'date')
    t_exp = pd.to_numeric(today_exp_df['amount'], errors='coerce').sum()

    # 3. حساب توالف اليوم
    today_waste_df = get_today_data(st.session_state.waste_df, 'date')
    t_waste = pd.to_numeric(today_waste_df['loss_value'], errors='coerce').sum()

    # 4. الحسبة النهائية الصافية
    # صافي الربح = (ربح المبيعات) - (المصروفات) - (التوالف)
    net_profit = t_gross_profit - t_exp - t_waste

    # --- عرض النتائج في كروت واضحة ---
    st.markdown(f"### 🕒 تقرير مبيعات ومصاريف اليوم: {today_dt}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='report-card'><h5>مبيعات اليوم</h5><h2 style='color:#27ae60;'>{format_num(t_sales)} ₪</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='report-card' style='border-top-color: #e67e22;'><h5>مصاريف وتوالف اليوم</h5><h2 style='color:#e67e22;'>{format_num(t_exp + t_waste)} ₪</h2></div>", unsafe_allow_html=True)
    with c3:
        color = "#27ae60" if net_profit >= 0 else "#e74c3c"
        st.markdown(f"<div class='report-card' style='border-top-color: {color};'><h5>صافي ربح اليوم</h5><h2 style='color:{color};'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)

    st.divider()
    
    # قسم شفافية الحسابات - ليطمئن قلبك يا أبا عمر
    with st.expander("📝 تفاصيل الحسبة (لماذا ظهر هذا الرقم؟)"):
        st.write(f"1️⃣ **ربح المبيعات (الخام):** {format_num(t_gross_profit)} ₪")
        st.write(f"2️⃣ **يُطرح منه مصروفات اليوم:** {format_num(t_exp)} ₪")
        st.write(f"3️⃣ **يُطرح منه توالف اليوم:** {format_num(t_waste)} ₪")
        st.write("---")
        st.write(f"📊 **الصافي النهائي:** {format_num(t_gross_profit)} - {format_num(t_exp)} - {format_num(t_waste)} = **{format_num(net_profit)} ₪**")
    
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>", unsafe_allow_html=True)
    
    with st.form("exp_form"):
        r = st.text_input("البيان")
        a = st.number_input("المبلغ (₪)", min_value=0.0)
        if st.form_submit_button("حفظ المصروف"):
            if r and a > 0:
                new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                sync_to_google(); st.rerun()

    st.subheader("سجل المصروفات (يمكنك الحذف من هنا)")
    if not st.session_state.expenses_df.empty:
        for idx, row in st.session_state.expenses_df.iterrows():
            colx, coly, colz = st.columns([3, 2, 1])
            colx.write(f"📌 {row['reason']}")
            coly.write(f"💰 {row['amount']} ₪")
            if colz.button("حذف", key=f"del_exp_{idx}"):
                st.session_state.expenses_df = st.session_state.expenses_df.drop(idx)
                sync_to_google(); st.rerun()

# (بقية الأقسام: المخزن والإعدادات تظل كما هي في كودك)
