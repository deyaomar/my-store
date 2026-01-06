import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المحاسبي الذكي", layout="wide", page_icon="📈")

# ملفات قاعدة البيانات
DB_FILE = 'inventory_data.csv'
SALES_FILE = 'sales_history.csv'
CATS_FILE = 'categories.csv'
WASTE_FILE = 'waste_history.csv'

# --- وظائف إدارة البيانات ---
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, index_col=0).to_dict('index')
    return {"بطاطا": {"كمية": 100.0, "شراء": 3.0, "بيع": 4.0, "قسم": "خضار وفواكه"}}

def load_categories():
    if os.path.exists(CATS_FILE):
        return pd.read_csv(CATS_FILE)['name'].tolist()
    return ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]

def load_sales():
    if os.path.exists(SALES_FILE):
        return pd.read_csv(SALES_FILE)
    return pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])

def load_waste():
    if os.path.exists(WASTE_FILE):
        return pd.read_csv(WASTE_FILE)
    return pd.DataFrame(columns=['date', 'item', 'loss_amount', 'qty'])

def save_all():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame({'name': st.session_state.categories}).to_csv(CATS_FILE, index=False)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)
    st.session_state.waste_df.to_csv(WASTE_FILE, index=False)

# تحميل البيانات
if 'inventory' not in st.session_state: st.session_state.inventory = load_data()
if 'categories' not in st.session_state: st.session_state.categories = load_categories()
if 'sales_df' not in st.session_state: st.session_state.sales_df = load_sales()
if 'waste_df' not in st.session_state: st.session_state.waste_df = load_waste()

# --- التصميم ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-top: 4px solid #1e4d2b; }
    .advice-box { background-color: #e3f2fd; padding: 20px; border-radius: 15px; border-right: 8px solid #2196f3; color: #0d47a1; margin-bottom: 20px; }
    .main-title { color: #1e4d2b; text-align: center; border-bottom: 2px solid #gold; }
    </style>
    """, unsafe_allow_html=True)

# نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "123":
            st.session_state['logged_in'] = True
            st.rerun()
else:
    st.sidebar.title(f"مرحباً أبو عمر 🍏")
    menu = st.sidebar.radio("القائمة:", ["💎 منصة البيع", "🏪 المخزن والأقسام", "🍂 قسم التوالف", "📊 التقارير والتحليلات"])

    # --- 1. منصة البيع ---
    if menu == "💎 منصة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        pay_method = st.radio("طريقة الدفع:", ["نقداً", "تطبيق"], horizontal=True)
        
        bill_items = []
        for cat in st.session_state.categories:
            with st.expander(f"📂 {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item, data in items.items():
                    c1, c2, c3, c4 = st.columns([0.5, 2, 2, 2])
                    with c1: sel = st.checkbox("", key=f"s_{item}")
                    with c2: st.write(f"**{item}** (متاح: {data['كمية']:.1f})")
                    with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                    with c4: val = st.number_input("القيمة", min_value=0.0, key=f"v_{item}")
                    
                    if sel and val > 0:
                        q = val if mode == "كمية" else val / data["بيع"]
                        amt = (val if mode == "شيكل" else val * data["بيع"])
                        bill_items.append({"item": item, "qty": q, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * q})

        if st.button("✅ تأكيد البيع") and bill_items:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for e in bill_items:
                st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                new_row = pd.DataFrame([{'date': now, 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': pay_method}])
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_row], ignore_index=True)
            save_all(); st.success("تم الحفظ!"); st.balloons()

    # --- 2. المخزن والأقسام ---
    elif menu == "🏪 المخزن والأقسام":
        st.markdown("<h1 class='main-title'>🏪 إدارة المخزن</h1>", unsafe_allow_html=True)
        # (نفس كود المخزن السابق مع زر الإضافة والحذف)
        st.write("استخدم هذا القسم لإضافة الأقسام والأصناف كما في الكود السابق.")

    # --- 3. قسم التوالف ---
    elif menu == "🍂 قسم التوالف":
        st.markdown("<h1 class='main-title'>🍂 إدارة التوالف</h1>", unsafe_allow_html=True)
        it_w = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
        q_w = st.number_input("الكمية التالفة", min_value=0.0)
        if st.button("خصم من المخزن كخسارة"):
            loss = q_w * st.session_state.inventory[it_w]["شراء"]
            st.session_state.inventory[it_w]["كمية"] -= q_w
            new_waste = pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': it_w, 'loss_amount': loss, 'qty': q_w}])
            st.session_state.waste_df = pd.concat([st.session_state.waste_df, new_waste], ignore_index=True)
            save_all(); st.error(f"تم تسجيل خسارة {loss:.2f} ₪")

    # --- 4. التقارير والتحليلات (الإضافة الجديدة) ---
    elif menu == "📊 التقارير والتحليلات":
        st.markdown("<h1 class='main-title'>📊 لوحة تحليلات المحل</h1>", unsafe_allow_html=True)
        
        # تجهيز البيانات
        sales = st.session_state.sales_df.copy()
        waste = st.session_state.waste_df.copy()
        sales['date'] = pd.to_datetime(sales['date'])
        waste['date'] = pd.to_datetime(waste['date'])
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        # 1. إحصائيات سريعة
        c1, c2, c3, c4 = st.columns(4)
        day_sales_val = sales[sales['date'].dt.date == today]['amount'].sum()
        day_profit_val = sales[sales['date'].dt.date == today]['profit'].sum()
        week_sales_val = sales[sales['date'].dt.date >= week_ago]['amount'].sum()
        week_waste_val = waste[waste['date'].dt.date >= week_ago]['loss_amount'].sum()

        c1.metric("مبيعات اليوم", f"{day_sales_val:.1f} ₪")
        c2.metric("ربح اليوم الصافي", f"{day_profit_val:.1f} ₪")
        c3.metric("مبيعات الأسبوع", f"{week_sales_val:.1f} ₪")
        c4.metric("توالف الأسبوع", f"{week_waste_val:.1f} ₪", delta_color="inverse")

        st.divider()

        # 2. التحليلات العميقة
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("🔝 الأكثر مبيعاً (كمية)")
            top_sell = sales.groupby('item')['amount'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_sell)

        with col_chart2:
            st.subheader("💰 الأكثر ربحاً")
            top_profit = sales.groupby('item')['profit'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_profit)

        st.divider()

        # 3. جدول التوالف
        st.subheader("🍂 تقرير التوالف الأسبوعي")
        st.table(waste[waste['date'].dt.date >= week_ago])

        # 4. ركن النصائح الذكي (AI Advice)
        st.markdown("<h3>💡 نصائح أبو عمر الذكية</h3>", unsafe_allow_html=True)
        
        advice_list = []
        # نصيحة التوالف
        if week_waste_val > (week_sales_val * 0.1):
            advice_list.append("⚠️ **تحذير:** نسبة التوالف عالية هذا الأسبوع (أكثر من 10%). راجع طريقة تخزين الخضار أو قلل كمية الشراء اليومية.")
        
        # نصيحة الأكثر مبيعاً
        if not top_sell.empty:
            best_item = top_sell.index[0]
            advice_list.append(f"🌟 **فرصة:** صنف **({best_item})** هو الأكثر طلباً. تأكد من توفر كميات كافية منه دائماً.")
        
        # نصيحة الربح
        if not top_profit.empty:
            most_profitable = top_profit.index[0]
            advice_list.append(f"💸 **ملاحظة:** صنف **({most_profitable})** يعطيك أفضل صافي ربح. حاول عمل عروض عليه لزيادة المبيعات.")

        # نصيحة النقص في المخزن
        low_stock = [k for k, v in st.session_state.inventory.items() if v['كمية'] < 5]
        if low_stock:
            advice_list.append(f"📦 **نقص مخزن:** الأصناف التالية قاربت على الانتهاء: {', '.join(low_stock)}.")

        for advice in advice_list:
            st.markdown(f"<div class='advice-box'>{advice}</div>", unsafe_allow_html=True)
