import streamlit as st
import pandas as pd

# كلمة السر
PASSWORD = "123" # غيرها زي ما بدك يا أبو عمر

if 'logged_in' not in st.session_state:
    st.title("🔐 دخول نظام أبو عمر")
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun()
        else: st.error("خطأ!")
else:
    st.title("🍏 جرد محل أبو عمر")
    
    # البضاعة اللي ثبتناها اليوم
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3, "بيع": 3.33},
            "ليمون": {"كمية": 27.5, "شراء": 4, "بيع": 6},
            "تفاح": {"كمية": 23.0, "شراء": 9, "بيع": 12},
            "كلمنتينا": {"كمية": 22.4, "شراء": 4, "بيع": 6},
            "بصل ناشف": {"كمية": 20.9, "شراء": 2.13, "بيع": 3.33},
            "بندورة": {"كمية": 12.0, "شراء": 7, "بيع": 10},
            "خيار": {"كمية": 12.6, "شراء": 5, "بيع": 8}
        }

    # عرض الجرد
    df = pd.DataFrame(st.session_state.inventory).T
    st.table(df)
    
    if st.button("تسجيل خروج"):
        st.session_state.pop('logged_in')
