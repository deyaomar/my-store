import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة والتصميم المتجاوب مع الموبايل
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="📦")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    /* تنسيق الخط والاتجاه */
    html, body, [class*="css"], .stMarkdown { 
        font-family: 'Tajawal', sans-serif !important; 
        direction: rtl !important; 
        text-align: right !important; 
    }

    /* جعل العناوين مناسبة لشاشة الجوال */
    .main-title { 
        color: #1a1a1a; 
        font-weight: 900; 
        font-size: 22px; /* تصغير الحجم للموبايل */
        border-right: 5px solid #27ae60; 
        padding-right: 10px; 
        margin-bottom: 20px; 
    }

    /* تحسين كروت المخزن لتظهر بشكل ممتاز على الموبايل */
    .stock-card {
        background: white;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #eee;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        text-align: center;
    }
    
    /* تحسين البطاقات المالية */
    .report-card { 
        background: white; 
        padding: 15px; 
        border-radius: 12px; 
        border-top: 4px solid #27ae60; 
        text-align: center; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }

    /* إخفاء القائمة الجانبية تلقائياً في الشاشات الصغيرة لتحسين الرؤية */
    @media (max-width: 768px) {
        .main-title { font-size: 18px; }
        .stMetric { padding: 5px !important; }
    }
    
    /* تحسين شكل الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #27ae60;
        color: white;
    }
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
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# 5. القائمة الجانبية (Sidebar)
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    st.divider()
    if st.button("🔄 تحديث"): st.rerun()

# --- المنطق الرئيسي ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    
    # تحسين الفلاتر للموبايل (وضعها تحت بعض)
    cat_sel = st.selectbox("📂 القسم", ["الكل"] + st.session_state.CATEGORIES)
    search = st.text_input("🔍 ابحث عن صنف...")
    
    items_to_sell = st.session_state.inventory.items()
    if cat_sel != "الكل":
        items_to_sell = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat_sel}.items()
    
    items = {k: v for k, v in items_to_sell if search.lower() in k.lower()}
    
    # عرض الأصناف بشكل قائمة مرنة للموبايل
    temp_bill = []
    for it, data in items.items():
        with st.container():
            c1, c2 = st.columns([2, 1])
            c1.markdown(f"**{it}** \n<small>{data['بيع']} ₪ | متوفر: {data['كمية']}</small>", unsafe_allow_html=True)
            val = c2.number_input("الكمية", key=f"v_{it}", min_value=0.0, step=1.0)
            if val > 0:
                temp_bill.append({'item': it, 'qty': val, 'amount': val * data['بيع'], 'profit': (data['بيع'] - data['شراء']) * val})
        st.divider()
    
    if temp_bill:
        if st.button("✅ إتمام البيع", use_container_width=True):
            bid = str(uuid.uuid4())[:8]
            for row in temp_bill:
                st.session_state.inventory[row['item']]['كمية'] -= row['qty']
                new_row = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': row['item'], 'amount': row['amount'], 'profit': row['profit'], 'method': 'نقدي', 'customer_name': 'زبون محل', 'bill_id': bid}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
            sync_to_google(); st.success("تم الحفظ!"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 المخزن والجرد</h1>", unsafe_allow_html=True)
    
    # تبسيط عرض قيمة المخزن للموبايل
    if st.session_state.inventory:
        stock_value = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())
        st.markdown(f"<div class='report-card'><small>قيمة البضاعة الحالية</small><h3>{format_num(stock_value)} ₪</h3></div>", unsafe_allow_html=True)
        
        f_cat = st.selectbox("📂 تصفية القسم", ["الكل"] + st.session_state.CATEGORIES)
        search_st = st.text_input("🔍 بحث في المخزن...")
        
        for it, data in st.session_state.inventory.items():
            item_cat = data.get('قسم', 'أخرى')
            if (f_cat == "الكل" or item_cat == f_cat) and (search_st.lower() in it.lower()):
                with st.expander(f"📦 {it} ({data['كمية']})"):
                    st.write(f"سعر البيع: {data['بيع']} ₪")
                    st.write(f"القسم: {item_cat}")
                    new_q = st.number_input("تعديل الكمية الفعلية", value=float(data['كمية']), key=f"inv_q_{it}")
                    if st.button("تحديث الجرد", key=f"inv_btn_{it}"):
                        st.session_state.inventory[it]['كمية'] = new_q
                        st.session_state.inventory[it]['أصلي'] = new_q
                        sync_to_google(); st.rerun()

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 تقارير أبو عمر</h1>", unsafe_allow_html=True)
    
    # حسابات سريعة
    df_sales = st.session_state.sales_df.copy()
    df_sales['date'] = pd.to_datetime(df_sales['date'])
    today = pd.Timestamp(datetime.now().date())
    
    t_sales = df_sales[df_sales['date'] == today]['amount'].sum()
    
    # عرض البطاقات واحدة تلو الأخرى للموبايل
    st.metric("مبيعات اليوم", f"{format_num(t_sales)} ₪")
    
    # استخدام Tabs بدلاً من أعمدة كثيرة
    t1, t2 = st.tabs(["💰 الأرباح", "📋 السجلات"])
    with t1:
        cap_now = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())
        st.write(f"رأس المال الحالي: **{format_num(cap_now)} ₪**")
    with t2:
        st.dataframe(df_sales.sort_values(by='date', ascending=False), use_container_width=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_form"):
        r = st.text_input("البيان")
        a = st.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ المصروف"):
            if r and a > 0:
                new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                sync_to_google(); st.rerun()

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["✨ صنف جديد", "📥 تزويد", "📂 الأقسام"])
    
    with tab1:
        with st.form("new_item"):
            n = st.text_input("الاسم")
            cat = st.selectbox("القسم", st.session_state.CATEGORIES)
            b = st.number_input("سعر الشراء")
            s = st.number_input("سعر البيع")
            q = st.number_input("الكمية")
            if st.form_submit_button("إضافة"):
                if n:
                    st.session_state.inventory[n] = {'قسم': cat, 'شراء': b, 'بيع': s, 'كمية': q, 'أصلي': q}
                    sync_to_google(); st.rerun()

    with tab3:
        new_cat = st.text_input("قسم جديد")
        if st.button("إضافة"):
            if new_cat: st.session_state.CATEGORIES.append(new_cat); st.rerun()
        for c in st.session_state.CATEGORIES:
            st.text(f"- {c}")
