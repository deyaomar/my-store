import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

# 2. التنسيق البصري (تعديل الخطوط لتكون بيضاء وعريضة جداً)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Cairo', sans-serif !important;
        text-align: right;
        direction: rtl;
    }

    /* خلفية القائمة الجانبية */
    [data-testid="stSidebar"] {
        background-color: #1e272e !important;
    }

    /* اسم أبو عمر */
    .sidebar-user-header {
        color: #27ae60 !important;
        font-size: 32px !important;
        font-weight: 900 !important;
        text-align: center;
        padding: 20px 0px;
        border-bottom: 2px solid #27ae60;
        margin-bottom: 20px;
    }

    /* تنسيق خيارات القائمة الجانبية */
    div[data-testid="stSidebar"] .stRadio div label {
        background-color: #2f3640;
        margin-bottom: 10px;
        border-radius: 12px;
        padding: 15px 20px !important;
        border: 1px solid #3d4652;
    }

    /* جعل النص أبيض وعريض جداً */
    div[data-testid="stSidebar"] .stRadio div label p {
        color: #FFFFFF !important; /* لون أبيض ناصع */
        font-size: 22px !important; /* حجم كبير */
        font-weight: 900 !important; /* عريض جداً */
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5); /* لزيادة الوضوح */
    }

    /* عند اختيار القسم */
    div[data-testid="stSidebar"] .stRadio div label[data-checked="true"] {
        background-color: #27ae60 !important;
        border: 2px solid #ffffff !important;
    }
    
    div[data-testid="stSidebar"] .stRadio div label[data-checked="true"] p {
        color: #FFFFFF !important;
    }

    .main-title {
        color: #2c3e50;
        text-align: center;
        border-bottom: 5px solid #27ae60;
        padding-bottom: 10px;
        font-weight: 900;
        font-size: 35px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. بناء القائمة الجانبية
st.sidebar.markdown("<div class='sidebar-user-header'>أبو عمر 👋</div>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    label="القائمة الأساسية",
    options=[
        "📊 التقارير المالية", 
        "🛒 نقطة البيع", 
        "📦 المخزن والجرد", 
        "💸 المصروفات", 
        "⚙️ الإعدادات"
    ],
    label_visibility="collapsed"
)

st.sidebar.divider()

# --- عرض المحتوى بناءً على اختيارك ---
if menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
    st.write("مرحباً بك يا أبو عمر في قسم التقارير.")

elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 نقطة البيع</h1>", unsafe_allow_html=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 المخزن والجرد</h1>", unsafe_allow_html=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
