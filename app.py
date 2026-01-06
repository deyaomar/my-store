import streamlit as st
import pandas as pd

# إعداد الصفحة وكلمة السر
st.set_page_config(page_title="جرد محل أبو عمر", layout="wide")
PASSWORD = "123"

if 'logged_in' not in st.session_state:
    st.title("🔐 دخول نظام أبو عمر")
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun()
        else: st.error("خطأ في كلمة السر!")
else:
    st.sidebar.header(f"أهلاً يا أبو عمر")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # البيانات الأساسية للجرد (رأس مالك اللي ثبتناه)
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3},
            "ليمون": {"كمية": 27.5, "شراء": 4},
            "تفاح": {"كمية": 23.0, "شراء": 9},
            "كلمنتينا": {"كمية": 22.4, "شراء": 4},
            "بصل ناشف": {"كمية": 20.9, "شراء": 2.13},
            "بندورة": {"كمية": 12.0, "شراء": 7},
            "خيار": {"كمية": 12.6, "شراء": 5}
        }

    # --- القسم الأول: تسجيل مبيعات ---
    st.header("🛒 تسجيل عملية بيع")
    col1, col2, col3 = st.columns(3)
    with col1:
        item_to_sell = st.selectbox("اختر الصنف المباع", list(st.session_state.inventory.keys()))
    with col2:
        amount_to_sell = st.number_input("الكمية (كيلو)", min_value=0.0, step=0.5)
    with col3:
        if st.button("✅ تأكيد البيع وخصم من الجرد"):
            if st.session_state.inventory[item_to_sell]["كمية"] >= amount_to_sell:
                st.session_state.inventory[item_to_sell]["كمية"] -= amount_to_sell
                st.success(f"تم خصم {amount_to_sell} كيلو من {item_to_sell}")
            else:
                st.error("الكمية المتوفرة لا تكفي!")

    st.divider()

    # --- القسم الثاني: عرض الجدول المحدث ---
    st.header("📊 جدول الجرد والمخزن الحالي")
    df = pd.DataFrame(st.session_state.inventory).T
    df['إجمالي رأس المال'] = df['كمية'] * df['شراء']
    
    # تنسيق الجدول للعرض
    st.table(df)

    # حساب إجمالي رأس المال المتبقي في المحل
    total_capital = df['إجمالي رأس المال'].sum()
    st.metric("إجمالي قيمة البضاعة المتبقية (رأس مال)", f"{total_capital:,.2f} شيكل")
