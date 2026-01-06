import streamlit as st
import pandas as pd

# إعدادات الصفحة بشكل مهيب
st.set_page_config(page_title="نظام أبو عمر - الإدارة الفخمة", layout="wide", page_icon="🍏")

# إضافة التصميم (تم تصحيح الكود هنا)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1e4d2b; color: white; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #2e7d32; border: 1px solid gold; }
    .metric-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border-right: 5px solid #1e4d2b; margin-bottom: 20px; text-align: center; }
    h1 { color: #1e4d2b; text-align: center; font-family: 'Arial'; border-bottom: 2px solid gold; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# نظام الدخول
if 'logged_in' not in st.session_state:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("<h1>🔐 دخول الإدارة</h1>", unsafe_allow_html=True)
        pwd = st.text_input("كلمة المرور المهيبة", type="password")
        if st.button("دخول للنظام"):
            if pwd == "123":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة")
else:
    # البيانات الأساسية للجرد
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3.0, "بيع": 3.33},
            "ليمون": {"كمية": 27.5, "شراء": 4.0, "بيع": 6.0},
            "تفاح": {"كمية": 23.0, "شراء": 9.0, "بيع": 12.0},
            "بندورة": {"كمية": 12.0, "شراء": 7.0, "بيع": 10.0},
            "خيار": {"كمية": 12.6, "شراء": 5.0, "بيع": 8.0}
        }
    if 'daily_profit' not in st.session_state:
        st.session_state.daily_profit = 0.0

    # القائمة الجانبية
    st.sidebar.markdown(f"<h2 style='text-align:center; color:#1e4d2b;'>🍏 محل أبو عمر</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("اختر القسم:", 
                            ["💎 منصة البيع السريع", 
                             "📦 إضافة بضاعة جديدة", 
                             "🛠️ تعديل الأسعار", 
                             "🍂 قسم التوالف"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # 1. منصة البيع السريع
    if menu == "💎 منصة البيع السريع":
        st.markdown("<h1>🛒 فاتورة المبيعات الملكية</h1>", unsafe_allow_html=True)
        
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"<div class='metric-card'><h3>📈 أرباح اليوم</h3><h2>{st.session_state.daily_profit:.2f} ₪</h2></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-card'><h3>📦 عدد الأصناف</h3><h2>{len(st.session_state.inventory)} صنف</h2></div>", unsafe_allow_html=True)
        
        bill_items = []
        st.write("### اختر المشتريات:")
        
        # عرض الأصناف بتنسيق أرتب
        for item in list(st.session_state.inventory.keys()):
            c1, c2, c3, c4 = st.columns([0.5, 2, 2, 3])
            with c1: sel = st.checkbox("", key=f"sel_{item}")
            with c2: st.markdown(f"**{item}**")
            with c3: m = st.radio("", ["شيكل", "كيلو"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
            with c4: v = st.number_input(f"القيمة لـ {item}", min_value=0.0, step=0.1, key=f"v_{item}", label_visibility="collapsed")
            
            if sel and v > 0:
                p_buy = st.session_state.inventory[item]["شراء"]
                p_sell = st.session_state.inventory[item]["بيع"]
                q = v if m == "كيلو" else v / p_sell
                amt = (v if m == "شيكل" else v * p_sell)
                bill_items.append({"صنف": item, "كمية": q, "مبلغ": amt, "ربح": (p_sell - p_buy) * q})

        st.markdown("---")
        if bill_items:
            total_bill = sum(i['مبلغ'] for i in bill_items)
            st.markdown(f"<h2 style='text-align:left; color:#1e4d2b;'>💰 إجمالي الفاتورة: {total_bill:.2f} شيكل</h2>", unsafe_allow_html=True)
            if st.button("🌟 تأكيد العملية"):
                for e in bill_items:
                    st.session_state.inventory[e["صنف"]]["كمية"] -= e["كمية"]
                    st.session_state.daily_profit += e["ربح"]
                st.balloons()
                st.success("تم تسجيل المبيعات بنجاح!")
                st.rerun()

    # 2. إضافة صنف جديد
    elif menu == "📦 إضافة بضاعة جديدة":
        st.markdown("<h1>📦 إضافة صنف جديد</h1>", unsafe_allow_html=True)
        n = st.text_input("اسم الصنف")
        q = st.number_input("الكمية المتوفرة", min_value=0.0)
        b = st.number_input("سعر الشراء", min_value=0.0)
        s = st.number_input("سعر البيع", min_value=0.0)
        if st.button("إضافة للمحل"):
            if n:
                st.session_state.inventory[n] = {"كمية": q, "شراء": b, "بيع": s}
                st.success(f"تمت إضافة {n} بنجاح")
            else: st.error("يرجى إدخال اسم")

    # 4. التوالف
    elif menu == "🍂 قسم التوالف":
        st.markdown("<h1>🍂 تسجيل التوالف</h1>", unsafe_allow_html=True)
        it_w = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
        q_w = st.number_input("الكمية التالفة (كيلو)", min_value=0.0)
        if st.button("خصم من المخزن"):
            st.session_state.inventory[it_w]["كمية"] -= q_w
            loss = q_w * st.session_state.inventory[it_w]["شراء"]
            st.session_state.daily_profit -= loss
            st.error(f"تم خصم {q_w} كيلو. خسارة: {loss:.2f}")

    # عرض الجرد
    with st.expander("📋 عرض الجرد المتبقي"):
        st.table(pd.DataFrame(st.session_state.inventory).T)
