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
    .stock-card {
        background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; transition: 0.3s;
    }
    .stock-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .delete-section { background: #fff5f5; padding: 15px; border-radius: 10px; border: 1px solid #feb2b2; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال المساعدة
def format_num(val):
    return f"{val:,.2f}"

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
        if not inv_df.empty and 'أصلي' not in inv_df.columns: inv_df['أصلي'] = inv_df['كمية']
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        st.session_state.sales_df = conn.read(worksheet="Sales", ttl=0)
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        st.session_state.inventory = {}
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'qty', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
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
        bid = "INV-" + str(uuid.uuid4())[:5].upper()
        for row in temp_bill:
            st.session_state.inventory[row['item']]['كمية'] -= row['qty']
            new_row = {
                'date': datetime.now().strftime("%Y-%m-%d"), 
                'item': row['item'], 
                'qty': row['qty'], 
                'amount': row['amount'], 
                'profit': row['profit'], 
                'method': 'نقدي', 
                'customer_name': 'زبون محل', 
                'bill_id': bid
            }
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
        sync_to_google(); st.success(f"تمت العملية بنجاح! رقم الفاتورة: {bid}"); st.rerun()

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقرير المالي الشامل</h1>", unsafe_allow_html=True)
    
    # حساب الإحصائيات (نفس كودك السابق مع التأكد من نوع البيانات)
    df_sales = st.session_state.sales_df.copy()
    if not df_sales.empty:
        df_sales['date'] = pd.to_datetime(df_sales['date'])
        
        # --- قسم حذف آخر فاتورة ---
        st.markdown("<div class='delete-section'>", unsafe_allow_html=True)
        st.subheader("🛠️ إدارة العمليات الأخيرة")
        last_bill_id = df_sales.iloc[-1]['bill_id']
        if st.button(f"🗑️ تراجع عن آخر فاتورة (رقم: {last_bill_id})", use_container_width=True):
            # استرجاع الكميات للمخزن
            last_bill_items = df_sales[df_sales['bill_id'] == last_bill_id]
            for _, row in last_bill_items.iterrows():
                if row['item'] in st.session_state.inventory:
                    st.session_state.inventory[row['item']]['كمية'] += row['qty']
            
            # حذفها من سجل المبيعات
            st.session_state.sales_df = st.session_state.sales_df[st.session_state.sales_df['bill_id'] != last_bill_id]
            sync_to_google()
            st.warning(f"تم حذف الفاتورة {last_bill_id} وإعادة الأصناف للمخزن.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # باقي كود التقارير (رأس المال، الأرباح، سجل الزبائن) كما هو في نسختك السابقة
    # ... (يمكنك تكملة عرض الجداول هنا)
    st.subheader("👥 سجل المبيعات التفصيلي")
    st.dataframe(st.session_state.sales_df.sort_index(ascending=False), use_container_width=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 حالة المخزن</h1>", unsafe_allow_html=True)
    # (نفس كود المخزن والجرد السابق)
    # ...
    for it, data in st.session_state.inventory.items():
        st.markdown(f"<div class='stock-card'><h3>{it}</h3><p>الكمية المتوفرة: {data['كمية']}</p></div>", unsafe_allow_html=True)

# الأقسام الأخرى (المصروفات، الإعدادات) تبقى كما هي في كودك الأصلي
