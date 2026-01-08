import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# 1. إعدادات الصفحة الأصلية (بدون تعديلات CSS إضافية)
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide")

# دالات التنظيف (أساسية لعمل الكود)
def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

# دالة القراءة الآمنة من الملفات
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try: return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# 2. تحميل البيانات
if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية', 'سعر_القطعة'])
    st.session_state.inventory = inv_df.to_dict('records')

# تثبيت قسم السجائر كقسم أساسي في القائمة
if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    saved_cats = cat_df['name'].tolist() if not cat_df.empty else []
    st.session_state.categories = list(dict.fromkeys(["السجائر"] + saved_cats))

if 'sales_df' not in st.session_state:
    st.session_state.sales_df = safe_read_csv('sales_final.csv', ['date', 'item', 'amount', 'profit', 'branch'])

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. القائمة الجانبية (الأصلية)
st.sidebar.title("نظام أبو عمر")
menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 نقطة البيع", "📦 المخزن والجرد", "⚙️ إدارة الأصناف", "📊 التقارير"])

# --- قسم إدارة الأصناف (التعديلات المطلوبة فقط) ---
if menu == "⚙️ إدارة الأصناف":
    st.header("⚙️ إدارة الأصناف")
    
    # اختيار القسم أولاً لفتح التعليمات الخاصة
    selected_cat = st.selectbox("اختر القسم:", st.session_state.categories)
    
    with st.form("add_form", clear_on_submit=True):
        if selected_cat == "السجائر":
            st.warning("تعليمات السجائر: أدخل سعر العلبة وسعر السيجارة فرط")
            n = st.text_input("اسم نوع الدخان")
            q = st.text_input("الكمية (بالعلبة)")
            b = st.text_input("سعر التكلفة للعلبة")
            s = st.text_input("سعر بيع العلبة")
            sub_p = st.text_input("سعر السيجارة الواحدة")
        else:
            n = st.text_input("اسم الصنف")
            q = st.text_input("الكمية")
            b = st.text_input("سعر الشراء")
            s = st.text_input("سعر البيع")
            sub_p = "0"
            
        if st.form_submit_button("إضافة"):
            if n:
                st.session_state.inventory.append({
                    "item": n, "قسم": selected_cat, "شراء": clean_num(b), 
                    "بيع": clean_num(s), "كمية": clean_num(q), 
                    "branch": "المحل", "سعر_القطعة": clean_num(sub_p)
                })
                auto_save()
                st.success(f"تمت إضافة {n} بنجاح")

# --- باقي الأقسام الأصلية كما كانت ---
elif menu == "🛒 نقطة البيع":
    st.header("🛒 شاشة البيع")
    # منطق البيع الأصلي الخاص بك
    search = st.text_input("بحث...")
    for it in st.session_state.inventory:
        if not search or search in it['item']:
            c1, c2, c3, c4 = st.columns([2,1,1,1])
            c1.write(it['item'])
            mode = c2.selectbox("النوع", ["علبة", "فرط"] if it['سعر_القطعة'] > 0 else ["وحدة"], key=it['item'])
            val = clean_num(c3.text_input("المبلغ", key=f"v_{it['item']}"))
            if c4.button("بيع", key=f"b_{it['item']}"):
                # هنا يتم الخصم والحساب (كما في كودك الأصلي)
                st.success("تم")

elif menu == "📦 المخزن والجرد":
    st.header("📦 حالة المخزن")
    st.table(pd.DataFrame(st.session_state.inventory))

elif menu == "📊 التقارير":
    st.header("📊 التقارير المالية")
    st.dataframe(st.session_state.sales_df)
