import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر الملكي", layout="wide", page_icon="🍏")

# 2. ملفات قاعدة البيانات
DB_FILE = 'inventory_v2.csv'
SALES_FILE = 'sales_v2.csv'
CATS_FILE = 'categories_v2.csv'

# وظيفة الحفظ التلقائي
def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame({'name': st.session_state.categories}).to_csv(CATS_FILE, index=False)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)

# تحميل البيانات
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات", "نسكافيه"]

# 3. تصميم الـ CSS (الهيبة والجمال)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stat-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-bottom: 5px solid #1e4d2b; text-align: center; margin-bottom: 20px;
    }
    .pay-btn-active { background-color: #1e4d2b !important; color: white !important; border: 2px solid gold !important; }
    .stButton>button { border-radius: 12px; height: 3.5em; font-weight: bold; }
    .category-header { background: #1e4d2b; color: white; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align:center;'>🔐 نظام أبو عمر المحاسبي</h1>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("🌟 دخول للنظام"):
        if pwd == "123":
            st.session_state['logged_in'] = True
            st.rerun()
else:
    # القائمة الجانبية
    menu = st.sidebar.radio("القائمة الرئيسية:", ["💎 شاشة البيع", "📦 إدارة المخزن", "📂 الأقسام", "📊 التقارير"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "💎 شاشة البيع":
        st.markdown("<h1 style='text-align:center;'>🛒 لوحة البيع السريع</h1>", unsafe_allow_html=True)
        
        # حساب مبيعات اليوم
        df_sales = st.session_state.sales_df.copy()
        df_sales['date'] = pd.to_datetime(df_sales['date'])
        today_data = df_sales[df_sales['date'].dt.date == datetime.now().date()]
        total_today = today_data['amount'].sum()
        profit_today = today_data['profit'].sum()

        col_stat1, col_stat2 = st.columns(2)
        col_stat1.markdown(f"<div class='stat-card'><h3>💰 مبيعات اليوم</h3><h2 style='color:#2e7d32;'>{total_today:.1f} ₪</h2></div>", unsafe_allow_html=True)
        col_stat2.markdown(f"<div class='stat-card'><h3>📈 ربح اليوم</h3><h2 style='color:#1565c0;'>{profit_today:.1f} ₪</h2></div>", unsafe_allow_html=True)

        # اختيار طريقة الدفع
        st.markdown("### 💳 طريقة الدفع")
        if 'p_method' not in st.session_state: st.session_state.p_method = "نقداً"
        cp1, cp2 = st.columns(2)
        if cp1.button("💵 نـقـداً (كاش)", use_container_width=True): st.session_state.p_method = "نقداً"
        if cp2.button("📱 بـنـكـي (تطبيق)", use_container_width=True): st.session_state.p_method = "تطبيق"
        
        # عرض الطريقة المختارة
        color = "#2e7d32" if st.session_state.p_method == "نقداً" else "#1565c0"
        st.markdown(f"<div style='text-align:center; padding:10px; border-radius:10px; background:{color}; color:white; font-weight:bold; margin-bottom:20px;'>الـدفـع الحـالي: {st.session_state.p_method}</div>", unsafe_allow_html=True)

        bill_items = []
        for cat in st.session_state.categories:
            with st.expander(f"📂 {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item, data in items.items():
                    r1, r2, r3, r4 = st.columns([0.5, 2, 2, 2])
                    with r1: sel = st.checkbox("", key=f"s_{item}")
                    with r2: st.markdown(f"**{item}** \n <small>({data['كمية']:.1f})</small>", unsafe_allow_html=True)
                    with r3: mode = st.radio(f"نوع_{item}", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
                    with r4: val = st.number_input(f"قيمة_{item}", min_value=0.0, key=f"v_{item}", label_visibility="collapsed")
                    
                    if sel and val > 0:
                        q = val if mode == "كمية" else val / data["بيع"]
                        bill_items.append({"item": item, "qty": q, "amount": (val if mode == "شيكل" else val * data["بيع"]), "profit": (data["بيع"] - data["شراء"]) * q})

        if st.button("🚀 تـنـفـيـذ الـعـمـلـيـة", use_container_width=True):
            if bill_items:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for e in bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_row = pd.DataFrame([{'date': now_str, 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method}])
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_row], ignore_index=True)
                auto_save()
                st.success("✅ تم تسجيل البيع والحفظ التلقائي!")
                st.balloons(); st.rerun()

    # --- 2. إدارة المخزن ---
    elif menu == "📦 إدارة المخزن":
        st.markdown("<h1 style='text-align:center;'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("اسم الصنف")
                c = st.selectbox("القسم", st.session_state.categories)
                q1, q2, q3 = st.columns(3)
                qty = q1.number_input("الكمية")
                buy = q2.number_input("شراء")
                sell = q3.number_input("بيع")
                if st.form_submit_button("إضافة"):
                    st.session_state.inventory[n] = {"كمية": qty, "شراء": buy, "بيع": sell, "قسم": c}
                    auto_save(); st.rerun()

        for cat in st.session_state.categories:
            st.markdown(f"<div class='category-header'>📂 {cat}</div>", unsafe_allow_html=True)
            items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            for it, data in items.items():
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.write(f"**{it}**")
                c2.write(f"متاح: {data['كمية']:.1f}")
                c3.write(f"بيع: {data['بيع']}")
                if c4.button("🗑️", key=f"del_{it}"):
                    del st.session_state.inventory[it]
                    auto_save(); st.rerun()

    # --- 3. الأقسام ---
    elif menu == "📂 الأقسام":
        st.markdown("<h1 style='text-align:center;'>📂 إدارة الأقسام</h1>", unsafe_allow_html=True)
        new_cat = st.text_input("اسم القسم الجديد")
        if st.button("إضافة"):
            if new_cat and new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                auto_save(); st.rerun()
        for cat in st.session_state.categories:
            col_x, col_y = st.columns([4, 1])
            col_x.write(cat)
            if col_y.button("حذف", key=f"dc_{cat}"):
                st.session_state.categories.remove(cat)
                auto_save(); st.rerun()

    # --- 4. التقارير ---
    elif menu == "📊 التقارير":
        st.markdown("<h1 style='text-align:center;'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
        if not st.session_state.sales_df.empty:
            st.write("### آخر المبيعات (محفوظة تلقائياً)")
            st.dataframe(st.session_state.sales_df.tail(20), use_container_width=True)
