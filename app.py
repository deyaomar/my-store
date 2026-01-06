import streamlit as st
import pandas as pd

# إعدادات الصفحة بشكل مهيب
st.set_page_config(page_title="نظام أبو عمر - الإدارة الفخمة", layout="wide", page_icon="🍏")

# إضافة لمسة جمالية بالألوان (CSS)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1e4d2b; color: white; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #2e7d32; border: 1px solid #gold; }
    .metric-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border-right: 5px solid #1e4d2b; }
    h1 { color: #1e4d2b; text-align: center; font-family: 'Arial'; border-bottom: 2px solid #gold; padding-bottom: 10px; }
    </style>
    """, unsafe_style_html=True)

# نظام الدخول بتصميم أرتب
if 'logged_in' not in st.session_state:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("<h1>🔐 دخول الإدارة</h1>", unsafe_style_html=True)
        pwd = st.text_input("كلمة المرور المهيبة", type="password")
        if st.button("دخول للنظام"):
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
            "بندورة": {"كمية": 12.0, "شراء": 7.0, "بيع": 10.0},
            "خيار": {"كمية": 12.6, "شراء": 5.0, "بيع": 8.0}
        }
    if 'daily_profit' not in st.session_state: st.session_state.daily_profit = 0.0

    # القائمة الجانبية (Sidebar) بتصميم مهيب
    st.sidebar.markdown(f"<h2 style='text-align:center; color:#1e4d2b;'>🍏 محل أبو عمر</h2>", unsafe_style_html=True)
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("اختر القسم:", 
                            ["💎 منصة البيع السريع", 
                             "📦 إضافة بضاعة جديدة", 
                             "🛠️ تعديل الأسعار", 
                             "🍂 قسم التوالف والخسائر"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.
