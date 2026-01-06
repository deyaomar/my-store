import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px # ستحتاج لتثبيت مكتبة plotly (pip install plotly)

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المطور", layout="wide", page_icon="🍏")

def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

# 2. ملفات البيانات (أضفنا ملف للمصروفات والتالف)
DB_FILE = 'inventory_final.csv'
SALES_FILE = 'sales_final.csv'
EXPENSES_FILE = 'expenses_final.csv'
WASTE_FILE = 'waste_final.csv'
CATS_FILE = 'categories_final.csv'

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)
    st.session_state.expenses_df.to_csv(EXPENSES_FILE, index=False)
    st.session_state.waste_df.to_csv(WASTE_FILE, index=False)

# تحميل البيانات في Session State
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'bill_id'])
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = pd.read_csv(EXPENSES_FILE) if os.path.exists(EXPENSES_FILE) else pd.DataFrame(columns=['date', 'reason', 'amount'])
if 'waste_df' not in st.session_state:
    st.session_state.waste_df = pd.read_csv(WASTE_FILE) if os.path.exists(WASTE_FILE) else pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

# 3. الهوية البصرية المحدثة
st.markdown("""
    <style>
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .report-card { background: #ffffff; padding: 15px; border-radius: 12px; border-right: 8px solid #2c3e50; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
    .low-stock { background: #ffeded; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; color: #ff4b4b; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# نظام الدخول (مختصر للتوضيح)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 شاشة البيع", "📦 المخزن والتالف", "💸 المصروفات", "📊 التقارير والإحصائيات"])

    # --- 1. شاشة البيع مع تنبيه النواقص ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        
        # (الاقتراح 2): تنبيه النواقص
        low_stock_items = [k for k, v in st.session_state.inventory.items() if v['كمية'] <= 5] # نبهني لو أقل من 5 كيلو
        if low_stock_items:
            with st.container():
                for item in low_stock_items:
                    st.markdown(f"<div class='low-stock'>⚠️ تنبيه: صنف ({item}) قرب يخلص! المتبقي: {st.session_state.inventory[item]['كمية']:.1f}</div>", unsafe_allow_html=True)

        # ... (كود البيع الأصلي يوضع هنا مع إضافة خيار الدفع) ...
        st.info("كود البيع يعمل كالمعتاد..")
        # [ملاحظة: كود البيع في رسالتك السابقة يدمج هنا]

    # --- 2. المخزن وتسجيل التالف (الاقتراح 4) ---
    elif menu == "📦 المخزن والتالف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن والتالف</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["محتوى المخزن", "🗑️ تسجيل تالف (خرب)"])
        
        with tab1:
            if st.session_state.inventory:
                st.table(pd.DataFrame([{"الصنف": k, "الكمية": f"{v['كمية']:.1f}", "القسم": v['قسم']} for k, v in st.session_state.inventory.items()]))
        
        with tab2:
            with st.form("waste_form"):
                w_item = st.selectbox("الصنف الخربان", list(st.session_state.inventory.keys()))
                w_qty = st.number_input("الكمية التالفة", min_value=0.1)
                if st.form_submit_button("تسجيل التالف"):
                    if st.session_state.inventory[w_item]['كمية'] >= w_qty:
                        loss = w_qty * st.session_state.inventory[w_item]['شراء']
                        st.session_state.inventory[w_item]['كمية'] -= w_qty
                        new_waste = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'loss_value': loss}
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_waste])], ignore_index=True)
                        auto_save(); st.success(f"تم خصم {w_qty} من {w_item} كخسارة."); st.rerun()
                    else: st.error("الكمية بالمخزن أقل من التالف!")

    # --- 3. المصروفات النثرية (الاقتراح 5) ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp_form"):
            reason = st.text_input("بيان المصروف (أكياس، كهرباء، ضريبة..)")
            amt = st.number_input("المبلغ", min_value=1.0)
            if st.form_submit_button("إضافة مصروف"):
                new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': reason, 'amount': amt}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                auto_save(); st.success("تم تسجيل المصروف"); st.rerun()
        st.dataframe(st.session_state.expenses_df.sort_values(by='date', ascending=False), use_container_width=True)

    # --- 4. التقارير والإحصائيات المتقدمة (الاقتراح 3) ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التحليل المالي للأداء</h1>", unsafe_allow_html=True)
        
        total_sales = st.session_state.sales_df['amount'].sum()
        total_profit = st.session_state.sales_df['profit'].sum()
        total_exp = st.session_state.expenses_df['amount'].sum()
        total_waste = st.session_state.waste_df['loss_value'].sum()
        net_profit = total_profit - total_exp - total_waste

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='report-card'><h3>💰 إجمالي المبيعات</h3><h2>{total_sales:.1f}</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h3>💸 مصروفات</h3><h2>{total_exp:.1f}</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h3>🍎 خسارة تالف</h3><h2>{total_waste:.1f}</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='report-card' style='border-right-color:#27ae60;'><h3>✅ الربح الصافي</h3><h2>{net_profit:.1f}</h2></div>", unsafe_allow_html=True)

        # (الاقتراح 3): الأكثر مبيعاً
        st.write("---")
        if not st.session_state.sales_df.empty:
            st.subheader("🔝 الأصناف الأكثر مبيعاً (من حيث القيمة)")
            top_items = st.session_state.sales_df.groupby('item')['amount'].sum().reset_index().sort_values(by='amount', ascending=False)
            fig = px.bar(top_items.head(10), x='item', y='amount', color='amount', labels={'item':'الصنف', 'amount':'إجمالي المبيعات'}, color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)
