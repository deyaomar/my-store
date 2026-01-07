import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# --- 1. إعدادات النظام الأساسية ---
st.set_page_config(page_title="نظام أبو عمر للمحاسبة 2026", layout="wide", page_icon="🍏")

# دالة لتنسيق الأرقام بشكل نظيف
def format_n(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# دالة لتحويل النصوص إلى أرقام بأمان
def to_num(text):
    try:
        if not text or str(text).strip() == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

# --- 2. إدارة قواعد البيانات ---
FILES_CONFIG = {
    'sales': ('sales_v3.csv', ['التاريخ', 'الصنف', 'المبلغ', 'الربح', 'الطريقة', 'اسم_الزبون', 'هاتف_الزبون', 'رقم_الفاتورة']),
    'expenses': ('expenses_v3.csv', ['التاريخ', 'البيان', 'المبلغ']),
    'waste': ('waste_v3.csv', ['التاريخ', 'الصنف', 'الكمية', 'قيمة_الخسارة']),
    'adjust': ('adjust_v3.csv', ['التاريخ', 'الصنف', 'الفارق_الوزني', 'الفارق_المالي'])
}

# تحميل البيانات في Session State
for key, (file, cols) in FILES_CONFIG.items():
    state_key = f"db_{key}"
    if state_key not in st.session_state:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                # التأكد من وجود كافة الأعمدة المطلوبة
                for col in cols:
                    if col not in df.columns: df[col] = 0.0 if 'المبلغ' in col or 'الربح' in col else ""
                st.session_state[state_key] = df
            except:
                st.session_state[state_key] = pd.DataFrame(columns=cols)
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

# تحميل المخزن والأقسام
if 'inventory' not in st.session_state:
    if os.path.exists('inventory_v3.csv'):
        st.session_state.inventory = pd.read_csv('inventory_v3.csv', index_col=0).to_dict('index')
    else:
        st.session_state.inventory = {}

if 'cats' not in st.session_state:
    if os.path.exists('categories_v3.csv'):
        st.session_state.cats = pd.read_csv('categories_v3.csv')['name'].tolist()
    else:
        st.session_state.cats = ["خضار وفواكه", "مكسرات"]

# دالة الحفظ المركزي
def save_all():
    pd.DataFrame(st.session_state.inventory).T.to_csv('inventory_v3.csv')
    st.session_state.db_sales.to_csv('sales_v3.csv', index=False)
    st.session_state.db_expenses.to_csv('expenses_v3.csv', index=False)
    st.session_state.db_waste.to_csv('waste_v3.csv', index=False)
    st.session_state.db_adjust.to_csv('adjust_v3.csv', index=False)
    pd.DataFrame(st.session_state.cats, columns=['name']).to_csv('categories_v3.csv', index=False)

# --- 3. الواجهة الرسومية ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; border-radius: 10px; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .stButton button { border-radius: 8px !important; font-weight: bold; width: 100%; }
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. الدخول والنظام ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    with st.container():
        _, col, _ = st.columns([1,1,1])
        with col:
            pwd = st.text_input("أدخل كلمة المرور", type="password")
            if st.button("دخول للنظام"):
                if pwd == "123":
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("كلمة المرور غير صحيحة")
else:
    st.sidebar.markdown("<h2 style='color:#27ae60; text-align:center;'>أهلاً أبو عمر</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المتقدمة", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- 1. نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع المباشر</h1>", unsafe_allow_html=True)
        
        # اختيار طريقة الدفع
        pay_method = st.sidebar.selectbox("طريقة الدفع الحالية:", ["نقداً", "تطبيق"])
        
        search = st.text_input("🔍 ابحث عن صنف...")
        
        cart = []
        for name, data in st.session_state.inventory.items():
            if not search or search.lower() in name.lower():
                with st.container():
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.markdown(f"**{name}**")
                    c1.caption(f"المتوفر: {format_n(data['كمية'])} كجم")
                    unit = c2.radio("الوحدة", ["شيكل", "وزن"], key=f"u_{name}", horizontal=True)
                    val = to_num(c3.text_input("المقدار", key=f"v_{name}"))
                    
                    if val > 0:
                        qty = val if unit == "وزن" else val / data["بيع"]
                        amt = val if unit == "شيكل" else val * data["بيع"]
                        profit = (data["بيع"] - data["شراء"]) * qty
                        cart.append({'item': name, 'qty': qty, 'amt': amt, 'profit': profit})
        
        if st.button("🚀 تنفيذ عملية البيع", type="primary"):
            if cart:
                b_id = str(uuid.uuid4())
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                temp_sales = []
                for entry in cart:
                    st.session_state.inventory[entry['item']]['كمية'] -= entry['qty']
                    temp_sales.append({
                        'التاريخ': now, 'الصنف': entry['item'], 'المبلغ': entry['amt'],
                        'الربح': entry['profit'], 'الطريقة': pay_method, 
                        'اسم_الزبون': 'زبون عام', 'رقم_الفاتورة': b_id
                    })
                st.session_state.db_sales = pd.concat([st.session_state.db_sales, pd.DataFrame(temp_sales)], ignore_index=True)
                save_all()
                st.success(f"✅ تم حفظ العملية بنجاح - رقم الفاتورة: {b_id[:8]}")
                st.rerun()

    # --- 2. المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزون</h1>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["📋 قائمة الأصناف", "⚖️ الجرد السنوي/اليومي", "🗑️ التالف"])
        
        with t1:
            if st.session_state.inventory:
                st.dataframe(pd.DataFrame(st.session_state.inventory).T[['قسم', 'كمية', 'شراء', 'بيع']], use_container_width=True)
        
        with t2:
            st.info("أدخل الأوزان الحقيقية لتصحيح المخزن")
            adjust_list = []
            for name, data in st.session_state.inventory.items():
                c_n, c_s, c_i = st.columns([2, 1, 2])
                c_n.write(f"**{name}**")
                c_s.caption(f"النظام: {format_n(data['كمية'])}")
                real = c_i.text_input("الوزن الفعلي", key=f"j_{name}")
                if real != "":
                    real_val = to_num(real)
                    diff = data['كمية'] - real_val
                    if diff != 0:
                        adjust_list.append({'التاريخ': datetime.now().strftime("%Y-%m-%d"), 'الصنف': name, 'الفارق_الوزني': diff, 'الفارق_المالي': diff * data['شراء'], 'new_qty': real_val})
            
            if st.button("💾 اعتماد الجرد وتصحيح العجز"):
                for adj in adjust_list:
                    st.session_state.inventory[adj['الصنف']]['كمية'] = adj['new_qty']
                    del adj['new_qty']
                    st.session_state.db_adjust = pd.concat([st.session_state.db_adjust, pd.DataFrame([adj])], ignore_index=True)
                save_all()
                st.success("✅ تم تحديث المخزن")
                st.rerun()

    # --- 3. التقارير المتقدمة ---
    elif menu == "📊 التقارير المتقدمة":
        st.markdown("<h1 class='main-title'>📊 التقارير والأرباح</h1>", unsafe_allow_html=True)
        
        range_option = st.selectbox("عرض تقرير:", ["اليوم", "آخر 7 أيام", "تاريخ مخصص"])
        start_date = datetime.now().date()
        end_date = datetime.now().date()
        
        if range_option == "آخر 7 أيام": start_date -= timedelta(days=7)
        elif range_option == "تاريخ مخصص":
            c1, c2 = st.columns(2)
            start_date = c1.date_input("من", start_date - timedelta(days=30))
            end_date = c2.date_input("إلى", end_date)

        def filter_data(df):
            if df.empty: return df
            df['date_only'] = pd.to_datetime(df['التاريخ']).dt.date
            return df[(df['date_only'] >= start_date) & (df['date_only'] <= end_date)]

        s_f = filter_data(st.session_state.db_sales)
        e_f = filter_data(st.session_state.db_expenses)
        w_f = filter_data(st.session_state.db_waste)
        a_f = filter_data(st.session_state.db_adjust)

        total_sales = s_f['المبلغ'].sum()
        total_profit = s_f['الربح'].sum()
        total_exp = e_f['المبلغ'].sum()
        total_loss = w_f['قيمة_الخسارة'].sum() + a_f['الفارق_المالي'].sum()
        net = total_profit - total_exp - total_loss

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("المبيعات", f"{format_n(total_sales)} ₪")
        c2.metric("المصروفات", f"{format_n(total_exp)} ₪")
        c3.metric("عجز وتالف", f"{format_n(total_loss)} ₪")
        c4.metric("صافي الربح", f"{format_n(net)} ₪")

        st.markdown("---")
        st.subheader("📋 سجل الفواتير المفصل")
        if not s_f.empty:
            summary = s_f.groupby('رقم_الفاتورة').agg({'التاريخ':'first','الطريقة':'first','المبلغ':'sum','الربح':'sum'}).sort_values('التاريخ', ascending=False)
            st.dataframe(summary.rename(columns={'التاريخ':'التاريخ','الطريقة':'نوع الدفع','المبلغ':'الإجمالي','الربح':'الربح'}), use_container_width=True)

    # --- 4. المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>")
        with st.form("exp_form"):
            reason = st.text_input("بيان الصرف")
            amount = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                new_exp = {'التاريخ': datetime.now().strftime("%Y-%m-%d"), 'البيان': reason, 'المبلغ': amount}
                st.session_state.db_expenses = pd.concat([st.session_state.db_expenses, pd.DataFrame([new_exp])], ignore_index=True)
                save_all()
                st.rerun()

    # --- 5. الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إدارة البيانات</h1>", unsafe_allow_html=True)
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("new_item"):
                n = st.text_input("اسم الصنف")
                c = st.selectbox("القسم", st.session_state.cats)
                col1, col2, col3 = st.columns(3)
                bp = col1.text_input("سعر الشراء")
                sp = col2.text_input("سعر البيع")
                qt = col3.text_input("الكمية")
                if st.form_submit_button("إضافة للمخزن"):
                    st.session_state.inventory[n] = {'قسم': c, 'شراء': to_num(bp), 'بيع': to_num(sp), 'كمية': to_num(qt)}
                    save_all()
                    st.rerun()
