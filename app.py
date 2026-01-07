import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

# 2. التنسيق البصري (تعديل الكلام نفسه ليكون أبيض وضخم)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Cairo', sans-serif !important;
        text-align: right;
        direction: rtl;
    }

    /* اسم أبو عمر في القائمة الجانبية */
    .sidebar-name {
        color: #27ae60 !important;
        font-size: 35px !important;
        font-weight: 900 !important;
        text-align: center;
        margin-bottom: 20px;
        display: block;
    }

    /* تعديل الكلام (النص) داخل القائمة الجانبية */
    div[data-testid="stSidebar"] .stRadio div label p {
        color: #FFFFFF !important;    /* لون الكلام أبيض ناصع */
        font-size: 28px !important;    /* حجم الكلام كبير جداً */
        font-weight: 900 !important;   /* الكلام عريض جداً */
        padding: 5px 0px;
        margin: 0px;
    }

    /* إزالة الخلفيات المزعجة والتركيز على الكلام */
    div[data-testid="stSidebar"] .stRadio div label {
        background-color: transparent !important; /* خلفية شفافة */
        border: none !important;                 /* بدون إطارات */
        padding: 0px !important;
    }

    /* تحسين شكل الاختيار (نقطة بسيطة أو ظل خفيف للكلام) */
    div[data-testid="stSidebar"] .stRadio div label[data-checked="true"] p {
        color: #27ae60 !important;    /* يتغير لون الكلام للأخضر عند الاختيار */
        text-decoration: underline;    /* خط تحت الكلام المختار للتمييز */
    }

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
st.sidebar.markdown("<span class='sidebar-name'>أبو عمر 👋</span>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    label="التنقل",
    options=[
        "📊 التقارير المالية", 
        "🛒 نقطة البيع", 
        "📦 المخزن والجرد", 
        "💸 المصروفات", 
        "⚙️ الإعدادات"
    ],
    label_visibility="collapsed"
)

# --- عرض المحتوى بناءً على اختيارك ---
if menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
    st.success("تم تكبير الكلام وجعله أبيض وعريض يا أبو عمر.")

elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 نقطة البيع</h1>", unsafe_allow_html=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 المخزن والجرد</h1>", unsafe_allow_html=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
