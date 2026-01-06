import streamlit as st
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام مبيعات أبو عمر السريع", layout="wide")
PASSWORD = "123"

if 'logged_in' not in st.session_state:
    st.title("🔐 دخول نظام أبو عمر")
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun()
else:
    # القائمة الجانبية
    st.sidebar.title("🛠️ التحكم")
    menu = st.sidebar.radio("القائمة:", ["البيع السريع (سلة)", "إضافة بضاعة", "تعديل الأسعار"])

    # البيانات الأساسية
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3.0, "بيع": 3.33},
            "ليمون": {"كمية": 27.5, "شراء": 4.0, "بيع": 6.0},
            "بندورة": {"كمية": 12.0, "شراء": 7.0, "بيع": 10.0}
        }
    if 'cart' not in st.session_state: st.session_state.cart = []
    if 'daily_profit' not in st.session_state: st.session_state.daily_profit = 0.0

    # --- نظام البيع السريع (السلة) ---
    if menu == "البيع السريع (سلة)":
        st.header("🛒 سلة مشتريات الزبون")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            item = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
        with col2:
            mode = st.radio("البيع بـ:", ["شيكل", "كيلو"], horizontal=True)
            val = st.number_input("القيمة", min_value=0.0, step=0.5)
        with col3:
            st.write("##")
            if st.button("➕ أضف"):
                # حساب الكمية والسعر والربح
                p_buy = st.session_state.inventory[item]["شراء"]
                p_sell = st.session_state.inventory[item]["بيع"]
                if mode == "كيلo":
                    q = val
                    total = val * p_sell
                else:
                    q = val / p_sell
                    total = val
                
                profit = (p_sell - p_buy) * q
                st.session_state.cart.append({"الصنف": item, "الكمية": round(q, 2), "المبلغ": round(total, 2), "ربح": profit})

        # عرض السلة
        if st.session_state.cart:
            st.subheader("📝 طلبات الزبون الحالية:")
            cart_df = pd.DataFrame(st.session_state.cart)
            st.table(cart_df[["الصنف", "الكمية", "المبلغ"]])
            
            total_bill = cart_df["المبلغ"].sum()
            st.info(f"💰 الحساب الكلي: {total_bill:.2f} شيكل")
            
            c_done, c_empty = st.columns(2)
            with c_done:
                if st.button("✅ تأكيد وخصم من المخزن"):
                    for entry in st.session_state.cart:
                        st.session_state.inventory[entry["الصنف"]]["كمية"] -= entry["الكمية"]
                        st.session_state.daily_profit += entry["ربح"]
                    st.session_state.cart = [] # تفريغ السلة
                    st.success("تم تسجيل العملية بنجاح!")
                    st.rerun()
            with c_empty:
                if st.button("🗑️ إفراغ السلة"):
                    st.session_state.cart = []
                    st.rerun()

        st.divider()
        st.subheader("📈 أرباح اليوم: " + f"{st.session_state.daily_profit:.2f} شيكل")

    # بقية الأقسام (إضافة وتعديل) كما هي...
    # (يمكنك إضافتها من الكود السابق)
