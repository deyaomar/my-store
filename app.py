import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل", layout="wide", page_icon="🍏")

# التصميم الجمالي
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1e4d2b; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #2e7d32; border: 1px solid gold; }
    .metric-card { background-color: white; padding: 15px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border-right: 5px solid #1e4d2b; text-align: center; }
    h1 { color: #1e4d2b; text-align: center; border-bottom: 2px solid gold; padding-bottom: 10px; }
    .category-header { background-color: #e8f5e9; padding: 10px; border-radius: 10px; color: #1b5e20; font-weight: bold; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# نظام الدخول
if 'logged_in' not in st.session_state:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("<h1>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # البيانات الأساسية مع الأقسام
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3.0, "بيع": 3.33, "قسم": "خضار وفواكه"},
            "ليمون": {"كمية": 27.5, "شراء": 4.0, "بيع": 6.0, "قسم": "خضار وفواكه"},
            "فستق عبيد": {"كمية": 10.0, "شراء": 12.0, "بيع": 18.0, "قسم": "مكسرات"},
            "نسكافيه 3بـ1": {"كمية": 50.0, "شراء": 0.8, "بيع": 1.5, "قسم": "نسكافيه ومشروبات"}
        }
    if 'daily_profit' not in st.session_state: st.session_state.daily_profit = 0.0

    # القائمة الجانبية
    menu = st.sidebar.radio("القائمة الرئيسية:", ["💎 منصة البيع", "🏪 المخزن الشامل", "🍂 قسم التوالف"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # --- 1. منصة البيع (مقسمة حسب النوع) ---
    if menu == "💎 منصة البيع":
        st.markdown("<h1>🛒 فاتورة مبيعات</h1>", unsafe_allow_html=True)
        st.metric("📈 أرباح اليوم", f"{st.session_state.daily_profit:.2f} ₪")
        
        bill_items = []
        categories = ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]
        
        for cat in categories:
            with st.expander(f"📂 قسم {cat}", expanded=True):
                items_in_cat = {k: v for k, v in st.session_state.inventory.items() if v['قسم'] == cat}
                for item in items_in_cat:
                    c1, c2, c3, c4 = st.columns([0.5, 2, 2, 3])
                    with c1: sel = st.checkbox("", key=f"sel_sale_{item}")
                    with c2: st.markdown(f"**{item}**")
                    with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
                    with c4: val = st.number_input("", min_value=0.0, key=f"v_{item}", label_visibility="collapsed")
                    
                    if sel and val > 0:
                        p_buy, p_sell = st.session_state.inventory[item]["شراء"], st.session_state.inventory[item]["بيع"]
                        q = val if mode == "كمية" else val / p_sell
                        bill_items.append({"صنف": item, "كمية": q, "مبلغ": (val if mode == "شيكل" else val * p_sell), "ربح": (p_sell - p_buy) * q})

        if bill_items:
            if st.button("✅ تأكيد البيع"):
                for e in bill_items:
                    st.session_state.inventory[e["صنف"]]["كمية"] -= e["كمية"]
                    st.session_state.daily_profit += e["ربح"]
                st.balloons(); st.rerun()

    # --- 2. المخزن الشامل (مع إضافة صنف وأقسام) ---
    elif menu == "🏪 المخزن الشامل":
        st.markdown("<h1>🏪 إدارة المخزن الشامل</h1>", unsafe_allow_html=True)
        
        # زر إضافة صنف جديد داخل المخزن
        with st.expander("➕ إضافة صنف جديد للم
