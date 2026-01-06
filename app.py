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
    # البيانات الأساسية
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3.0, "بيع": 3.33},
            "ليمون": {"كمية": 27.5, "شراء": 4.0, "بيع": 6.0},
            "تفاح": {"كمية": 23.0, "شراء": 9.0, "بيع": 12.0},
            "بندورة": {"كمية": 12.0, "شراء": 7.0, "بيع": 10.0},
            "خيار": {"كمية": 12.6, "شراء": 5.0, "بيع": 8.0}
        }
    if 'daily_profit' not in st.session_state: st.session_state.daily_profit = 0.0

    st.title("🛒 فاتورة بيع سريعة")
    st.write("حدد الأصناف التي اشتراها الزبون واضغط تأكيد في الأسفل")

    # إنشاء قائمة المشتريات المؤقتة
    bill_items = []
    
    # عرض الأصناف تحت بعض مع مربعات اختيار
    st.write("---")
    
    # ترويسة الجدول
    h1, h2, h3, h4 = st.columns([1, 2, 2, 2])
    h1.write("**اختر**")
    h2.write("**الصنف**")
    h3.write("**طريقة البيع**")
    h4.write("**القيمة (كمية أو شيكل)**")

    for item in st.session_state.inventory.keys():
        c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
        
        with c1:
            selected = st.checkbox("", key=f"check_{item}")
        with c2:
            st.write(f"**{item}**")
        with c3:
            mode = st.radio("نوع:", ["شيكل", "كيلو"], key=f"mode_{item}", horizontal=True, label_visibility="collapsed")
        with c4:
            val = st.number_input("القيمة", min_value=0.0, step=0.5, key=f"val_{item}", label_visibility="collapsed")
        
        if selected and val > 0:
            p_buy = st.session_state.inventory[item]["شراء"]
            p_sell = st.session_state.inventory[item]["بيع"]
            
            if mode == "كيلو":
                qty = val
                total = val * p_sell
            else:
                qty = val / p_sell
                total = val
            
            profit = (p_sell - p_buy) * qty
            bill_items.append({"صنف": item, "كمية": qty, "مبلغ": total, "ربح": profit})

    st.write("---")

    # المجموع وزر التأكيد
    if bill_items:
        total_bill = sum(item['مبلغ'] for item in bill_items)
        st.subheader(f"💰 مجموع الفاتورة: {total_bill:.2f} شيكل")
        
        if st.button("✅ تأكيد البيع وخصم الكل من المخزن", use_container_width=True):
            for entry in bill_items:
                st.session_state.inventory[entry["صنف"]]["كمية"] -= entry["كمية"]
                st.session_state.daily_profit += entry["ربح"]
            st.success("تم تسجيل الفاتورة بنجاح!")
            st.rerun()
    else:
        st.info("قم باختيار الأصناف من الأعلى لتجهيز الفاتورة")

    st.divider()
    # عرض الأرباح والجرد المتبقي
    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("📈 أرباح اليوم", f"{st.session_state.daily_profit:.2f} شيكل")
    
    with st.expander("📊 عرض الجرد المتبقي في المخزن"):
        df = pd.DataFrame(st.
