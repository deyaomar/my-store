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
    .category-header { background-color: #e8f5e9; padding: 10px; border-radius: 10px; color: #1b5e20; font-weight: bold; margin-top: 20px; border-right: 5px solid #2e7d32; }
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
    # البيانات الأساسية
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3.0, "بيع": 3.33, "قسم": "خضار وفواكه"},
            "ليمون": {"كمية": 27.5, "شراء": 4.0, "بيع": 6.0, "قسم": "خضار وفواكه"},
            "فستق": {"كمية": 10.0, "شراء": 12.0, "بيع": 18.0, "قسم": "مكسرات"},
            "نسكافيه": {"كمية": 50.0, "شراء": 0.8, "بيع": 1.5, "قسم": "نسكافيه ومشروبات"}
        }
    if 'daily_profit' not in st.session_state: st.session_state.daily_profit = 0.0

    menu = st.sidebar.radio("القائمة الرئيسية:", ["💎 منصة البيع", "🏪 المخزن الشامل", "🍂 قسم التوالف"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # --- 1. منصة البيع ---
    if menu == "💎 منصة البيع":
        st.markdown("<h1>🛒 فاتورة مبيعات</h1>", unsafe_allow_html=True)
        st.metric("📈 أرباح اليوم", f"{st.session_state.daily_profit:.2f} ₪")
        
        bill_items = []
        cats = ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]
        
        for cat in cats:
            with st.expander(f"📂 قسم {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item in items:
                    c1, c2, c3, c4 = st.columns([0.5, 2, 2, 3])
                    with c1: sel = st.checkbox("", key=f"s_{item}")
                    with c2: st.markdown(f"**{item}**")
                    with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
                    with c4: val = st.number_input("", min_value=0.0, key=f"v_{item}", label_visibility="collapsed")
                    
                    if sel and val > 0:
                        inv = st.session_state.inventory[item]
                        q = val if mode == "كمية" else val / inv["بيع"]
                        bill_items.append({"صنف": item, "كمية": q, "مبلغ": (val if mode == "شيكل" else val * inv["بيع"]), "ربح": (inv["بيع"] - inv["شراء"]) * q})

        if bill_items:
            if st.button("✅ تأكيد البيع"):
                for e in bill_items:
                    st.session_state.inventory[e["صنف"]]["كمية"] -= e["كمية"]
                    st.session_state.daily_profit += e["ربح"]
                st.balloons(); st.rerun()

    # --- 2. المخزن الشامل ---
    elif menu == "🏪 المخزن الشامل":
        st.markdown("<h1>🏪 إدارة المخزن</h1>", unsafe_allow_html=True)
        
        with st.expander("➕ إضافة صنف جديد", expanded=False):
            with st.form("add_form"):
                n = st.text_input("اسم الصنف")
                cat = st.selectbox("القسم", ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"])
                c_a1, c_a2, c_a3 = st.columns(3)
                q = c_a1.number_input("الكمية")
                b = c_a2.number_input("شراء")
                s = c_a3.number_input("بيع")
                if st.form_submit_button("إضافة للمخزن"):
                    st.session_state.inventory[n] = {"كمية": q, "شراء": b, "بيع": s, "قسم": cat}
                    st.rerun()

        for cat in ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]:
            st.markdown(f"<div class='category-header'>📂 {cat}</div>", unsafe_allow_html=True)
            items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            for item, data in items.items():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
                col1.write(item)
                col2.write(f"{data['كمية']:.1f}")
                col3.write(f"{data['شراء']}")
                col4.write(f"{data['بيع']}")
                with col5:
                    if st.button("🗑️", key=f"del_{item}"):
                        del st.session_state.inventory[item]
                        st.rerun()

    # --- 3. التوالف ---
    elif menu == "🍂 قسم التوالف":
        st.markdown("<h1>🍂 التوالف</h1>", unsafe_allow_html=True)
        it_w = st.selectbox("الصنف", list(st.session_state.inventory.keys()))
        q_w = st.number_input("الكمية التالفة")
        if st.button("خصم الخسارة"):
            st.session_state.inventory[it_w]["كمية"] -= q_w
            st.session_state.daily_profit -= (q_w * st.session_state.inventory[it_w]["شراء"])
            st.rerun()
