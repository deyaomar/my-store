import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

# 2. التنسيق البصري (تركيز كامل على ضخامة ووضوح الخط الأبيض)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Cairo', sans-serif !important;
        text-align: right;
        direction: rtl;
    }

    /* خلفية القائمة الجانبية داكنة لإبراز الأبيض */
    [data-testid="stSidebar"] {
        background-color: #121212 !important;
        min-width: 350px !important;
    }

    /* اسم أبو عمر - كبير جداً */
    .sidebar-user-header {
        color: #27ae60 !important;
        font-size: 38px !important;
        font-weight: 900 !important;
        text-align: center;
        padding: 25px 0px;
        border-bottom: 3px solid #27ae60;
        margin-bottom: 30px;
    }

    /* تصميم خيارات القائمة الجانبية كأزرار ضخمة */
    div[data-testid="stSidebar"] .stRadio div label {
        background-color: #1e1e1e;
        margin-bottom: 15px;
        border-radius: 15px;
        padding: 20px 25px !important;
        border: 2px solid #333;
        transition: 0.3s ease;
    }

    /* النص: أبيض ناصع، ضخم، وعريض جداً */
    div[data-testid="stSidebar"] .stRadio div label p {
        color: #FFFFFF !important; /* أبيض ناصع */
        font-size: 30px !important; /* حجم ضخم وواضح */
        font-weight: 900 !important; /* أقصى عرض للخط */
        line-height: 1.5;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8); /* ظل لزيادة البروز */
    }

    /* عند مرور الماوس أو الاختيار */
    div[data-testid="stSidebar"] .stRadio div label:hover {
        border-color: #27ae60;
        background-color: #262626;
    }

    div[data-testid="stSidebar"] .stRadio div label[data-checked="true"] {
        background-color: #27ae60 !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0px 4px 15px rgba(39, 174, 96, 0.4);
    }

    /* العناوين في الصفحة الرئيسية */
    .main-title {
        color: #2c3e50;
        text-align: center;
        border-bottom: 5px solid #27ae60;
        padding-bottom: 10px;
        font-weight: 900;
        font-size: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. بناء القائمة الجانبية
st.sidebar.markdown("<div class='sidebar-user-header'>أبو عمر 👋</div>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    label="قائمة التحكم",
    options=[
        "📊 التقارير المالية", 
        "🛒 نقطة البيع", 
        "📦 المخزن والجرد", 
        "💸 المصروفات", 
        "⚙️ الإعدادات"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 تسجيل خروج آمن", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# --- الصفحات ---
if menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
    st.success("أهلاً بك يا أبو عمر، تم تحديث الخطوط بناءً على طلبك.")

elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 نقطة البيع</h1>", unsafe_allow_html=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 المخزن والجرد</h1>", unsafe_allow_html=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
