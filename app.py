import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

def format_num(val):
    if val == int(val): return str(int(val))
    return str(val)

def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

# 2. ملفات البيانات وتحميلها
DB_FILE = 'inventory_final.csv'
CATS_FILE = 'categories_final.csv'

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv(CATS_FILE, index=False)

# 3. التصميم (CSS)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 700; font-size: 18px; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 22px; text-align: center; margin-bottom: 15px; border-bottom: 1px solid white; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    /* تنسيق الحقول لتكون متناسقة */
    .stTextInput input { text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام القائمة
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    st.sidebar.markdown("<div class='sidebar-user'>مرحباً يا أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 شاشة البيع", "📦 المخزن والتالف", "⚙️ إدارة الأصناف"])

    if menu == "⚙️ إدارة الأصناف":
        st.markdown("<h1 class='main-title'>⚙️ إضافة وتعديل الأصناف</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🆕 إضافة صنف جديد", "✏️ تعديل صنف موجود"])

        with tab1:
            with st.form("add_new_item_form"):
                col_name, col_cat = st.columns([2, 1])
                name = col_name.text_input("اسم الصنف (مثلاً: تفاح أمريكي)")
                cat = col_cat.selectbox("القسم", st.session_state.categories)
                
                # المربعات الصغيرة بجانب بعضها
                c1, c2, c3 = st.columns(3)
                buy = c1.text_input("سعر الشراء (₪)")
                sell = c2.text_input("سعر البيع (₪)")
                qty = c3.text_input("الكمية المتوفرة")
                
                if st.form_submit_button("✅ إضافة الصنف للمخزن", use_container_width=True):
                    if name:
                        st.session_state.inventory[name] = {
                            "قسم": cat, 
                            "شراء": clean_num(buy), 
                            "بيع": clean_num(sell), 
                            "كمية": clean_num(qty)
                        }
                        auto_save(); st.success(f"تم إضافة {name} بنجاح!"); st.rerun()

        with tab2:
            edit_item = st.selectbox("اختر الصنف المراد تعديله", [""] + list(st.session_state.inventory.keys()))
            if edit_item:
                data = st.session_state.inventory[edit_item]
                st.write(f"تعديل بيانات: **{edit_item}**")
                
                # المربعات الصغيرة بجانب بعضها في التعديل أيضاً
                ce1, ce2, ce3 = st.columns(3)
                new_buy = ce1.text_input("سعر الشراء", value=format_num(data['شراء']))
                new_sell = ce2.text_input("سعر البيع", value=format_num(data['بيع']))
                new_qty = ce3.text_input("الكمية", value=format_num(data['كمية']))
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("💾 حفظ التعديلات", use_container_width=True):
                    st.session_state.inventory[edit_item].update({
                        "شراء": clean_num(new_buy),
                        "بيع": clean_num(new_sell),
                        "كمية": clean_num(new_qty)
                    })
                    auto_save(); st.success("تم التحديث"); st.rerun()
                
                if col_btn2.button("🗑️ حذف الصنف", use_container_width=True):
                    del st.session_state.inventory[edit_item]
                    auto_save(); st.warning("تم الحذف"); st.rerun()

    # (بقية الأقسام مثل شاشة البيع والمخزن تظل كما هي في الكود السابق)
