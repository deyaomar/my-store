import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

# 2. التنسيق البصري المتكامل (CSS الاحترافي)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    /* الخط العام وتنسيق اللغة */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Cairo', sans-serif !important;
        text-align: right;
        direction: rtl;
    }

    /* تحسين شكل القائمة الجانبية بالكامل */
    [data-testid="stSidebar"] {
        background-color: #1a1c1e !important; /* لون كحلي غامق جداً وفخم */
        border-left: 2px solid #27ae60;
        min-width: 320px !important;
    }

    /* حاوية اسم أبو عمر */
    .user-profile {
        padding: 30px 10px;
        text-align: center;
        background: linear-gradient(135deg, #1a1c1e 0%, #27ae60 400%);
        border-bottom: 1px solid #34495e;
        margin-bottom: 20px;
    }

    .user-profile h1 {
        color: #27ae60 !important;
        font-size: 36px !important;
        font-weight: 900 !important;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    /* تنسيق الكلام داخل القائمة - أبيض وعريض جداً */
    div[data-testid="stSidebar"] .stRadio div label p {
        color: #FFFFFF !important;    /* كلام أبيض ناصع */
        font-size: 26px !important;    /* حجم كبير وواضح جداً */
        font-weight: 900 !important;   /* خط عريض (Bold) */
        padding: 10px 0px;
        transition: 0.3s;
    }

    /* تحسين خلفية الخيارات عند التصفح */
    div[data-testid="stSidebar"] .stRadio div label {
        background-color: transparent !important;
        border-radius: 12px;
        margin-bottom: 12px;
        padding-right: 15px !important;
        transition: 0.3s;
    }

    /* عند تمرير الماوس (Hover) */
    div[data-testid="stSidebar"] .stRadio div label:hover {
        background-color: rgba(39, 174, 96, 0.1) !important;
    }

    /* تنسيق القسم المختار حالياً */
    div[data-testid="stSidebar"] .stRadio div label[data-checked="true"] {
        background-color: #27ae60 !important; /* يتحول الخلفية للأخضر عند الاختيار */
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    
    div[data-testid="stSidebar"] .stRadio div label[data-checked="true"] p {
        color: #FFFFFF !important; /* يبقى الكلام أبيض عند الاختيار */
    }

    /* إخفاء الدائرة الصغيرة الأصلية للاختيار */
    div[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        display: none;
    }

    /* تصميم العناوين الرئيسية في الصفحة */
    .main-header {
        background-color: #ffffff;
        color: #2c3e50;
        padding: 20px;
        border-radius: 15px;
        border-right: 8px solid #27ae60;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. بناء القائمة الجانبية المحسنة
with st.sidebar:
    st.markdown("""
        <div class="user-profile">
            <h1>أبو عمر 👋</h1>
        </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio(
        "القائمة الرئيسية",
        ["📊 التقارير المالية", "🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "⚙️ الإعدادات"],
        key="main_menu"
    )
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if st.button("🚪 خروج آمن", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 4. محتوى الصفحات
if menu == "📊 التقارير المالية":
    st.markdown("<div class='main-header'><h1>📊 التقارير المالية والأرباح</h1></div>", unsafe_allow_html=True)
    st.success("أهلاً بك يا أبو عمر في النسخة المطورة من نظامك.")

elif menu == "🛒 نقطة البيع":
    st.markdown("<div class='main-header'><h1>🛒 شاشة البيع المباشر</h1></div>", unsafe_allow_html=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<div class='main-header'><h1>📦 إدارة المخزن والجرد</h1></div>", unsafe_allow_html=True)

elif menu == "💸 المصروفات":
    st.markdown("<div class='main-header'><h1>💸 سجل المصروفات</h1></div>", unsafe_allow_html=True)

elif menu == "⚙️ الإعدادات":
    st.markdown("<div class='main-header'><h1>⚙️ إعدادات النظام</h1></div>", unsafe_allow_html=True)
