import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر - الإدارة الفخمة", layout="wide", page_icon="🍏")

# التصميم الجمالي
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1e4d2b; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #2e7d32; border: 1px solid gold; }
    .metric-card { background-color: white; padding: 15px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border-right: 5px solid #1e4d2b; text-align: center; }
    h1 { color: #1e4d2b; text-align: center; border-bottom: 2px solid gold; padding-bottom: 10px; }
    .stock-row { background-color: white; padding: 10px; border-radius: 10px; margin-bottom: 5px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# نظام الدخول
if 'logged_in' not in st.session_state:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("<h1>🔐 دخول الإدارة</h1>", unsafe_allow_html=True)
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # البيانات الأساسية
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3.0, "بيع": 3.33},
            "ليمون": {"كمية": 27.5, "شراء": 4.0, "بيع": 6.0},
            "تفاح": {"كمية": 23.0, "شراء": 9.0, "بيع": 12.0},
            "بندورة": {"كمية": 12.0, "شراء": 7.0, "بيع": 10.0}
        }
    if 'daily_profit' not in st.session_state: st.session_state.daily_profit = 0.0

    # القائمة الجانبية
    st.sidebar.markdown(f"<h2 style='text-align:center; color:#1e4d2b;'>🍏 إدارة أبو عمر</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية:", 
                            ["💎 منصة البيع", 
                             "🏪 المخزن الشامل", 
                             "✨ إضافة صنف جديد", 
                             "🍂 قسم التوالف"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # --- 1. منصة البيع ---
    if menu == "💎 منصة البيع":
        st.markdown("<h1>🛒 فاتورة مبيعات</h1>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        m1.markdown(f"<div class='metric-card'><h3>📈 أرباح اليوم</h3><h2>{st.session_state.daily_profit:.2f} ₪</h2></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><h3>📦 أصناف المخزن</h3><h2>{len(st.session_state.inventory)}</h2></div>", unsafe_allow_html=True)
        
        bill_items = []
        for item in list(st.session_state.inventory.keys()):
            c1, c2, c3, c4 = st.columns([0.5, 2, 2, 3])
            with c1: sel = st.checkbox("", key=f"sel_{item}")
            with c2: st.markdown(f"**{item}**")
            with c3: mode = st.radio("", ["شيكل", "كيلو"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
            with c4: val = st.number_input("", min_value=0.0, step=0.1, key=f"v_{item}", label_visibility="collapsed")
            
            if sel and val > 0:
                p_buy, p_sell = st.session_state.inventory[item]["شراء"], st.session_state.inventory[item]["بيع"]
                q = val if mode == "كيلو" else val / p_sell
                bill_items.append({"صنف": item, "كمية": q, "مبلغ": (val if mode == "شيكل" else val * p_sell), "ربح": (p_sell - p_buy) * q})

        if bill_items:
            if st.button("✅ تأكيد البيع"):
                for e in bill_items:
                    st.session_state.inventory[e["صنف"]]["كمية"] -= e["كمية"]
                    st.session_state.daily_profit += e["ربح"]
                st.balloons(); st.rerun()

    # --- 2. المخزن الشامل (التعديل والحذف) ---
    elif menu == "🏪 المخزن الشامل":
        st.markdown("<h1>🏪 إدارة المخزن</h1>", unsafe_allow_html=True)
        
        # ترويسة الجدول
        t1, t2, t3, t4, t5 = st.columns([2, 1.5, 1.5, 1.5, 2])
        t1.write("**الصنف**"); t2.write("**الكمية**"); t3.write("**الشراء**"); t4.write("**البيع**"); t5.write("**إجراءات**")
        
        for item, data in list(st.session_state.inventory.items()):
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 1.5, 2])
                c1.write(f"**{item}**")
                c2.write(f"{data['كمية']:.2f} كغم")
                c3.write(f"{data['شراء']} ₪")
                c4.write(f"{data['بيع']} ₪")
                
                # أزرار التعديل والحذف في عمود واحد
                with c5:
                    sub_c1, sub_c2 = st.columns(2)
                    if sub_c1.button("📝", key=f"edit_{item}"):
                        st.session_state.editing_item = item
                    if sub_c2.button("🗑️", key=f"del_{item}"):
                        del st.session_state.inventory[item]
                        st.rerun()
        
        # نافذة التعديل (تظهر فقط عند الضغط على زر التعديل)
        if 'editing_item' in st.session_state:
            st.divider()
            st.subheader(f"🛠️ تعديل صنف: {st.session_state.editing_item}")
            item_to_upd = st.session_state.editing_item
            col_up1, col_up2, col_up3 = st.columns(3)
            new_q = col_up1.number_input("الكمية الحالية", value=st.session_state.inventory[item_to_upd]["كمية"])
            new_b = col_up2.number_input("سعر الشراء", value=st.session_state.inventory[item_to_upd]["شراء"])
            new_s = col_up3.number_input("سعر البيع", value=st.session_state.inventory[item_to_upd]["بيع"])
            
            if st.button("حفظ التعديلات"):
                st.session_state.inventory[item_to_upd] = {"كمية": new_q, "شراء": new_b, "بيع": new_s}
                del st.session_state.editing_item
                st.success("تم التحديث!"); st.rerun()

    # --- 3. إضافة صنف جديد ---
    elif menu == "✨ إضافة صنف جديد":
        st.markdown("<h1>✨ صنف جديد</h1>", unsafe_allow_html=True)
        with st.form("new_item"):
            n = st.text_input("اسم الصنف")
            q = st.number_input("الكمية", min_value=0.0)
            b = st.number_input("سعر الشراء", min_value=0.0)
            s = st.number_input("سعر البيع", min_value=0.0)
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {"كمية": q, "شراء": b, "بيع": s}
                st.success("تم الإضافة"); st.rerun()

    # --- 4. التوالف ---
    elif menu == "🍂 قسم التوالف":
        st.markdown("<h1>🍂 التوالف</h1>", unsafe_allow_html=True)
        it_w = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
        q_w = st.number_input("الكمية التالفة", min_value=0.0)
        if st.button("خصم كخسارة"):
            st.session_state.inventory[it_w]["كمية"] -= q_w
            st.session_state.daily_profit -= (q_w * st.session_state.inventory[it_w]["شراء"])
            st.error("تم الخصم"); st.rerun()
