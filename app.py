import streamlit as st
import pandas as pd
import os

# إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر - الحفظ التلقائي", layout="wide", page_icon="🍏")

# ملف قاعدة البيانات
DB_FILE = 'inventory_data.csv'

# وظيفة لتحميل البيانات من الملف
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, index_col=0).to_dict('index')
    else:
        # بيانات افتراضية لأول مرة
        return {
            "بطاطا": {"كمية": 100.0, "شراء": 3.0, "بيع": 4.0, "قسم": "خضار وفواكه"},
            "ليمون": {"كمية": 50.0, "شراء": 4.0, "بيع": 6.0, "قسم": "خضار وفواكه"}
        }

# وظيفة لحفظ البيانات للملف
def save_data():
    df = pd.DataFrame(st.session_state.inventory).T
    df.to_csv(DB_FILE)

# تحميل البيانات في ذاكرة النظام
if 'inventory' not in st.session_state:
    st.session_state.inventory = load_data()

if 'daily_profit' not in st.session_state:
    st.session_state.daily_profit = 0.0

# --- التصميم والجسم الرئيسي للتطبيق ---
st.markdown("""
    <style>
    .stButton>button { background-color: #1e4d2b; color: white; border-radius: 8px; }
    .category-header { background-color: #f0f2f6; padding: 10px; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# نظام الدخول (كلمة السر 123)
if 'logged_in' not in st.session_state:
    st.title("🔐 دخول نظام أبو عمر")
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "123":
            st.session_state['logged_in'] = True
            st.rerun()
else:
    menu = st.sidebar.radio("القائمة:", ["💎 منصة البيع", "🏪 المخزن الشامل", "🍂 قسم التوالف"])

    # 1. منصة البيع مع حفظ تلقائي
    if menu == "💎 منصة البيع":
        st.header("🛒 فاتورة المبيعات")
        st.write(f"📈 أرباح الجلسة الحالية: {st.session_state.daily_profit:.2f} ₪")
        
        bill_items = []
        for cat in ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]:
            with st.expander(f"📂 {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item, data in items.items():
                    c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
                    with c1: sel = st.checkbox("", key=f"s_{item}")
                    with c2: st.write(f"**{item}** (متاح: {data['كمية']:.1f})")
                    with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                    with c4: val = st.number_input("القيمة", min_value=0.0, key=f"v_{item}")
                    
                    if sel and val > 0:
                        q = val if mode == "كمية" else val / data["بيع"]
                        bill_items.append({"صنف": item, "كمية": q, "مبلغ": (val if mode == "شيكل" else val * data["بيع"]), "ربح": (data["بيع"] - data["شراء"]) * q})

        if st.button("✅ تأكيد البيع والحفظ"):
            for e in bill_items:
                st.session_state.inventory[e["صنف"]]["كمية"] -= e["كمية"]
                st.session_state.daily_profit += e["ربح"]
            save_data() # حفظ فوري في الملف
            st.success("تم البيع وحفظ البيانات في الملف بنجاح!")
            st.balloons()

    # 2. المخزن الشامل (إضافة/تعديل/حذف مع حفظ)
    elif menu == "🏪 المخزن الشامل":
        st.header("🏪 إدارة المخزن")
        
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("add_item", clear_on_submit=True):
                name = st.text_input("اسم الصنف")
                cat = st.selectbox("القسم", ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"])
                c1, c2, c3 = st.columns(3)
                q = c1.number_input("الكمية")
                b = c2.number_input("شراء")
                s = c3.number_input("بيع")
                if st.form_submit_button("إضافة"):
                    st.session_state.inventory[name] = {"كمية": q, "شراء": b, "بيع": s, "قسم": cat}
                    save_data() # حفظ فوري
                    st.success(f"تمت إضافة {name}")

        # عرض الأصناف مع زر حذف
        for cat in ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]:
            st.markdown(f"<div class='category-header'>{cat}</div>", unsafe_allow_html=True)
            items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            for item, data in items.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"{item} - متبقي: {data['كمية']:.1f}")
                if col3.button("🗑️", key=f"del_{item}"):
                    del st.session_state.inventory[item]
                    save_data()
                    st.rerun()

    # خيار لمزامنة الملف يدوياً
    if st.sidebar.button("💾 حفظ يدوي للمخزن"):
        save_data()
        st.sidebar.success("تم الحفظ!")
