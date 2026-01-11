import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة والتصميم المتجاوب
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { 
        font-family: 'Tajawal', sans-serif !important; 
        direction: rtl !important; 
        text-align: right !important; 
    }
    .main-title { 
        color: #1a1a1a; font-weight: 900; font-size: 25px; 
        border-right: 8px solid #27ae60; padding-right: 15px; margin-bottom: 25px; 
    }
    .stock-card {
        background: white; padding: 15px; border-radius: 12px;
        border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px; transition: 0.3s;
    }
    .report-card { 
        background: white; padding: 20px; border-radius: 15px; 
        border-top: 5px solid #27ae60; text-align: center; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
    }
    /* تحسين الأزرار للموبايل */
    .stButton>button { width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال المساعدة
def clean_num(text):
    try:
        if text is None or text == "" or pd.isna(text): return 0.0
        return float(str(text).replace(',', '').replace('₪', '').strip())
    except: return 0.0

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
    # استخدام أعمدة تتناسب مع الموبايل
    cat_sel = st.selectbox("📂 القسم", ["الكل"] + st.session_state.CATEGORIES)
    search = st.text_input("🔍 ابحث عن صنف لبيعه...")
    
    items_to_sell = st.session_state.inventory.items()
    if cat_sel != "الكل":
        items_to_sell = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat_sel}.items()
    
    items = {k: v for k, v in items_to_sell if search.lower() in k.lower()}
    
    # تحسين عرض الأصناف للموبايل (بدل 4 أعمدة، نجعلها مرنة)
    temp_bill = []
    for it, data in items.items():
        with st.container():
            col1, col2 = st.columns([2, 1])
            col1.markdown(f"**{it}** ({data['بيع']} ₪)")
            val = col2.number_input(f"الكمية", key=f"v_{it}", min_value=0.0, step=0.1, label_visibility="collapsed")
            if val > 0:
                temp_bill.append({'item': it, 'qty': val, 'amount': val * data['بيع'], 'profit': (data['بيع'] - data['شراء']) * val})
            st.divider()
    
    if temp_bill and st.button("✅ إتمام البيع وحفظ الفاتورة", use_container_width=True):
        bid = str(uuid.uuid4())[:8]
        for row in temp_bill:
            st.session_state.inventory[row['item']]['كمية'] -= row['qty']
            new_row = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': row['item'], 'amount': row['amount'], 'profit': row['profit'], 'method': 'نقدي', 'customer_name': 'زبون محل', 'bill_id': bid}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
        sync_to_google(); st.success("تمت العملية بنجاح!"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 حالة المخزن</h1>", unsafe_allow_html=True)
    # عرض رأس المال بشكل واضح في كرت واحد للموبايل
    if st.session_state.inventory:
        stock_value = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())
        st.markdown(f"<div class='report-card'><h5>إجمالي رأس المال الحالي</h5><h2>{format_num(stock_value)} ₪</h2></div><br>", unsafe_allow_html=True)
        
        search_st = st.text_input("🔍 ابحث في الأصناف...")
        for it, data in st.session_state.inventory.items():
            if search_st.lower() in it.lower():
                with st.expander(f"📦 {it} - المتبقي: {data['كمية']}"):
                    new_q = st.number_input("تعديل الكمية الفعلية", value=float(data['كمية']), key=f"inv_q_{it}")
                    if st.button("تحديث", key=f"inv_btn_{it}"):
                        st.session_state.inventory[it]['كمية'] = new_q
                        sync_to_google(); st.rerun()

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
    # تبسيط عرض التقارير للموبايل
    df_sales = st.session_state.sales_df.copy()
    if not df_sales.empty:
        df_sales['date'] = pd.to_datetime(df_sales['date'])
        today_sales = df_sales[df_sales['date'].dt.date == datetime.now().date()]['amount'].sum()
        st.metric("مبيعات اليوم", f"{format_num(today_sales)} ₪")
        st.divider()
        st.write("سجل المبيعات:")
        st.dataframe(df_sales, use_container_width=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_form"):
        r = st.text_input("البيان")
        a = st.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ"):
            new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
            sync_to_google(); st.rerun()

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["✨ صنف جديد", "📂 الأقسام"])
    with tab1:
        with st.form("add_form"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.CATEGORIES)
            b = st.number_input("سعر الشراء")
            s = st.number_input("سعر البيع")
            q = st.number_input("الكمية")
            if st.form_submit_button("إضافة صنف"):
                st.session_state.inventory[n] = {'قسم': cat, 'شراء': b, 'بيع': s, 'كمية': q, 'أصلي': q}
                sync_to_google(); st.success("تم!"); st.rerun()
