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
    
    # تحديد تاريخ اليوم بشكل دقيق
    today = datetime.now().date()

    # --- 1. حساب أرباح المبيعات ---
    df_sales = st.session_state.sales_df.copy()
    total_sales_today = 0
    total_gross_profit_today = 0
    
    if not df_sales.empty:
        df_sales['date'] = pd.to_datetime(df_sales['date']).dt.date
        # التأكد من تحويل الأعمدة لأرقام، وإذا لم توجد نضع 0
        s_amount_col = 'amount' if 'amount' in df_sales.columns else df_sales.columns[2] # محاولة تخمين العمود
        s_profit_col = 'profit' if 'profit' in df_sales.columns else df_sales.columns[3]
        
        day_sales = df_sales[df_sales['date'] == today]
        total_sales_today = pd.to_numeric(day_sales[s_amount_col], errors='coerce').sum()
        total_gross_profit_today = pd.to_numeric(day_sales[s_profit_col], errors='coerce').sum()

    # --- 2. حساب المصروفات (حل مشكلة الخطأ هنا) ---
    df_exp = st.session_state.expenses_df.copy()
    total_expenses_today = 0
    
    if not df_exp.empty:
        # التأكد من تحويل التاريخ
        df_exp['date'] = pd.to_datetime(df_exp['date']).dt.date
        # التحقق هل العمود موجود فعلاً؟
        if 'amount' in df_exp.columns:
            today_exp = df_exp[df_exp['date'] == today]
            total_expenses_today = pd.to_numeric(today_exp['amount'], errors='coerce').sum()
        else:
            # إذا كان العمود مفقوداً، نبحث عن أول عمود يحتوي على أرقام
            st.warning("تنبيه: لم يتم العثور على عمود باسم 'amount' في المصروفات.")
    
    # --- 3. حساب التوالف ---
    df_waste = st.session_state.waste_df.copy()
    total_waste_today = 0
    if not df_waste.empty:
        df_waste['date'] = pd.to_datetime(df_waste['date']).dt.date
        w_col = 'loss_value' if 'loss_value' in df_waste.columns else df_waste.columns[-1]
        today_waste = df_waste[df_waste['date'] == today]
        total_waste_today = pd.to_numeric(today_waste[w_col], errors='coerce').sum()

    # --- 4. الحسبة النهائية ---
    net_profit_today = total_gross_profit_today - total_expenses_today - total_waste_today

    # عرض النتائج
    st.markdown(f"### 📅 تقرير يوم: {today}")
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي مبيعات اليوم", f"{format_num(total_sales_today)} ₪")
    c2.metric("ربح المبيعات", f"{format_num(total_gross_profit_today)} ₪")
    c3.metric("مصاريف وتوالف اليوم", f"{format_num(total_expenses_today + total_waste_today)} ₪")

    st.markdown(f"""
        <div style="background: #f0f2f6; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #27ae60;">
            <h2 style="margin:0; color: #1a1a1a;">صافي الربح النهائي لليوم</h2>
            <h1 style="margin:0; color: #27ae60;">{format_num(net_profit_today)} ₪</h1>
        </div>
    """, unsafe_allow_html=True)

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
