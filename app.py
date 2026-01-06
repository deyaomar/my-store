import streamlit as st
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام جرد وأرباح أبو عمر", layout="wide")
PASSWORD = "123"

# نظام الدخول
if 'logged_in' not in st.session_state:
    st.title("🔐 دخول نظام أبو عمر")
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun()
        else: st.error("خطأ في كلمة السر!")
else:
    # القائمة الجانبية
    st.sidebar.title("🛠️ لوحة التحكم")
    menu = st.sidebar.radio("اختر العملية:", ["البيع وحساب الأرباح", "إضافة صنف جديد", "تعديل الكميات والأسعار"])
    
    # الجرد الأساسي مع سعر البيع
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3.0, "بيع": 3.33},
            "ليمون": {"كمية": 27.5, "شراء": 4.0, "بيع": 6.0},
            "بندورة": {"كمية": 12.0, "شراء": 7.0, "بيع": 10.0}
        }
    if 'total_profit' not in st.session_state:
        st.session_state.total_profit = 0.0

    # --- الصفحة الأولى: البيع الذكي ---
    if menu == "البيع وحساب الأرباح":
        st.header("🛒 تسجيل مبيعات ذكي")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            item = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
        with c2:
            mode = st.radio("طريقة البيع:", ["بالكيلو", "بمبلغ (شيكل)"])
        with c3:
            val = st.number_input("أدخل القيمة", min_value=0.0, step=0.5)

        if st.button("✅ تنفيذ البيع"):
            price_buy = st.session_state.inventory[item]["شراء"]
            price_sell = st.session_state.inventory[item]["بيع"]
            
            if mode == "بالكيلو":
                qty_to_deduct = val
                sale_amount = val * price_sell
            else:
                qty_to_deduct = val / price_sell
                sale_amount = val
            
            if st.session_state.inventory[item]["كمية"] >= qty_to_deduct:
                st.session_state.inventory[item]["كمية"] -= qty_to_deduct
                profit = (price_sell - price_buy) * qty_to_deduct
                st.session_state.total_profit += profit
                st.success(f"تم بيع {qty_to_deduct:.2f} كيلو بمبلغ {sale_amount:.2f} شيكل. الربح: {profit:.2f}")
            else:
                st.error("الكمية غير كافية!")

        st.divider()
        st.subheader("📈 ملخص الأرباح والجرد")
        st.metric("إجمالي أرباحك اليوم", f"{st.session_state.total_profit:.2f} شيكل")
        
        df = pd.DataFrame(st.session_state.inventory).T
        df['رأس المال المتبقي'] = df['كمية'] * df['شراء']
        st.table(df)

    # --- الصفحة الثانية: إضافة صنف جديد ---
    elif menu == "إضافة صنف جديد":
        st.header("✨ إضافة صنف جديد")
        n = st.text_input("اسم الصنف")
        q = st.number_input("الكمية", min_value=0.0)
        p_buy = st.number_input("سعر الشراء (للكيلو)", min_value=0.0)
        p_sell = st.number_input("سعر البيع (للكيلو)", min_value=0.0)
        if st.button("إضافة"):
            st.session_state.inventory[n] = {"كمية": q, "شراء": p_buy, "بيع": p_sell}
            st.success(f"تم إضافة {n}")

    # --- الصفحة الثالثة: التعديل ---
    elif menu == "تعديل الكميات والأسعار":
        st.header("⚙️ تعديل البيانات")
        item_edit = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
        new_p_sell = st.number_input("تعديل سعر البيع", value=st.session_state.inventory[item_edit]["بيع"])
        if st.button("تحديث السعر"):
            st.session_state.inventory[item_edit]["بيع"] = new_p_sell
            st.success("تم التحديث")
