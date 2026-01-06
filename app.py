import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. إعدادات الصفحة الفخمة
st.set_page_config(page_title="إدارة أبو عمر - الماركة", layout="wide", page_icon="🍏")

# 2. ملفات قاعدة البيانات
DB_FILE = 'inventory_v2.csv'
SALES_FILE = 'sales_v2.csv'
CATS_FILE = 'categories_v2.csv'

# --- وظائف التخزين اللحظي ---
def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame({'name': st.session_state.categories}).to_csv(CATS_FILE, index=False)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)

# تحميل البيانات (معالجة البداية)
if 'inventory' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index')
    else:
        st.session_state.inventory = {"بطاطا": {"كمية": 50.0, "شراء": 3.0, "بيع": 4.0, "قسم": "خضار وفواكه"}}

if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])

if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]

# --- 3. تصميم الـ CSS (الهيبة الملكية) ---
st.markdown("""
    <style>
    /* الخلفية والخطوط */
    .stApp { background-color: #f0f2f5; }
    h1, h2, h3 { font-family: 'Cairo', sans-serif; color: #1e4d2b; }
    
    /* بطاقات الإحصائيات */
    .stat-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 5px solid #1e4d2b; text-align: center;
    }
    
    /* تنسيق الأزرار الكبيرة */
    .stButton>button {
        border-radius: 12px; height: 3.5em; font-size: 18px; font-weight: bold;
        transition: all 0.3s; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
    
    /* أزرار الأقسام والبيع */
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; background: transparent !important; }
    .category-box { background: #ffffff; padding: 15px; border-radius: 15px; margin-bottom: 10px; border-right: 8px solid #gold; }
    
    /* إخفاء التسميات لتوفير مساحة */
    label[data-testid="stWidgetLabel"] { font-weight: bold; color: #1e4d2b; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>🔑 نظام أبو عمر</h1>", unsafe_allow_html=True)
        pwd = st.text_input("أدخل كلمة المرور السرية", type="password")
        if st.button("🌟 دخول للنظام الملكي"):
            if pwd == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # القائمة الجانبية (تصميم أنيق)
    st.sidebar.markdown(f"<h2 style='text-align:center;'>🍏 متجر أبو عمر</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("الإدارة العامة:", ["💎 شاشة البيع", "📦 إدارة المخزن", "📂 الأقسام", "📊 التقارير"], label_visibility="collapsed")
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # --- القسم 1: شاشة البيع الفخمة ---
    if menu == "💎 شاشة البيع":
        st.markdown("<h1 style='text-align:center;'>🛒 لوحة البيع السريع</h1>", unsafe_allow_html=True)
        
        # ملخص سريع في الأعلى
        today_sales = st.session_state.sales_df[pd.to_datetime(st.session_state.sales_df['date']).dt.date == datetime.now().date()]
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='stat-card'><h3>💰 مبيعات اليوم</h3><h2 style='color:#2e7d32;'>{today_sales['amount'].sum():.
