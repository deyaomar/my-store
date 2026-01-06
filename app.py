import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المحاسبي", layout="wide", page_icon="🍏")

# ملفات قاعدة البيانات
DB_FILE = 'inventory_data.csv'
SALES_FILE = 'sales_history.csv'
CATS_FILE = 'categories.csv'

# --- وظائف إدارة البيانات ---
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, index_col=0).to_dict('index')
    return {"بطاطا": {"كمية": 100.0, "شراء": 3.0, "بيع": 4.0, "قسم": "خضار وفواكه"}}

def load_categories():
    if os.path.exists(CATS_FILE):
        return pd.read_csv(CATS_FILE)['name'].tolist()
    return ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]

def load_sales():
    if os.path.exists(SALES_FILE):
        return pd.read_csv(SALES_FILE)
    return pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])

def save_all():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame({'name': st.session_state.categories}).to_csv(CATS_FILE, index=False)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)

# تحميل البيانات في ذاكرة النظام
if 'inventory' not in st.session_state:
    st.session_state.inventory = load_data()
if 'categories' not in st.session_state:
    st.session_state.categories = load_categories()
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = load_sales()

# --- التصميم ---
st.markdown("""
    <style>
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .main-title { color: #1e4d2b; text-align: center; border-bottom: 2px solid gold; }
    .stat-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-right: 5px solid #1e4d2b; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "123":
            st.session_state['logged_in'] = True
            st.rerun()
else:
    st.sidebar.title(f"مرحباً أبو عمر 🍏")
    menu = st.sidebar.radio("القائمة:", ["💎 منصة البيع", "🏪 المخزن والأقسام", "📊 تقارير المبيعات"])

    # --- 1. منصة البيع الماركة ---
    if menu == "💎 منصة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        
        col_pay1, col_pay2 = st.columns(2)
        with col_pay1:
            pay_method = st.radio("طريقة الدفع:", ["نقداً (كاش)", "تطبيق (بنك/محفظة)"], horizontal=True)
        
        bill_items = []
        for cat in st.session_state.categories:
            with st.expander(f"📂 {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                if not items: st.write("لا يوجد أصناف")
                for item, data in items.items():
                    c1, c2, c3, c4 = st.columns([0.5, 2, 2, 2])
                    with c1: sel = st.checkbox("", key=f"s_{item}")
                    with c2: st.write(f"**{item}** (متاح: {data['كمية']:.1f})")
                    with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                    with c4: val = st.number_input("القيمة", min_value=0.0, key=f"v_{item}")
                    
                    if sel and val > 0:
                        q = val if mode == "كمية" else val / data["بيع"]
                        amt = (val if mode == "شيكل" else val * data["بيع"])
                        bill_items.append({"item": item, "qty": q, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * q})

        if st.button("✅ تأكيد العملية والحفظ") and bill_items:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for e in bill_items:
                # تحديث المخزن
                st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                # إضافة لسجل المبيعات
                new_row = pd.DataFrame([{'date': now, 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': pay_method}])
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_row], ignore_index=True)
            
            save_all()
            st.success(f"تم تسجيل المبيعات ({pay_method}) بنجاح!")
            st.balloons()

    # --- 2. المخزن والأقسام (إضافة/حذف أقسام وأصناف) ---
    elif menu == "🏪 المخزن والأقسام":
        st.markdown("<h1 class='main-title'>🏪 إدارة المخزن والأقسام</h1>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📦 إدارة الأصناف", "📂 إدارة الأقسام"])
        
        with tab2:
            st.subheader("إضافة قسم جديد")
            new_cat_name = st.text_input("اسم القسم (مثلاً: منظفات)")
            if st.button("إضافة القسم"):
                if new_cat_name and new_cat_name not in st.session_state.categories:
                    st.session_state.categories.append(new_cat_name)
                    save_all(); st.rerun()
            
            st.subheader("الأقسام الحالية")
            for c in st.session_state.categories:
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.write(c)
                if col_c2.button("حذف", key=f"del_cat_{c}"):
                    st.session_state.categories.remove(c)
                    save_all(); st.rerun()

        with tab1:
            with st.expander("➕ إضافة صنف جديد"):
                with st.form("add_form", clear_on_submit=True):
                    n = st.text_input("اسم الصنف")
                    cat = st.selectbox("القسم", st.session_state.categories)
                    c_a1, c_a2, c_a3 = st.columns(3)
                    q = c_a1.number_input("الكمية")
                    b = c_a2.number_input("شراء")
                    s = c_a3.number_input("بيع")
                    if st.form_submit_button("إضافة للمخزن"):
                        st.session_state.inventory[n] = {"كمية": q, "شراء": b, "بيع": s, "قسم": cat}
                        save_all(); st.rerun()

            for cat in st.session_state.categories:
                st.markdown(f"### 📂 {cat}")
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item, data in items.items():
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    c1.write(item)
                    c2.write(f"الكمية: {data['كمية']:.1f}")
                    if c4.button("🗑️", key=f"del_it_{item}"):
                        del st.session_state.inventory[item]
                        save_all(); st.rerun()

    # --- 3. تقارير المبيعات (يومي وأسبوعي) ---
    elif menu == "📊 تقارير المبيعات":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
        
        df = st.session_state.sales_df.copy()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            today = datetime.now().date()
            last_week = today - timedelta(days=7)
            
            day_sales = df[df['date'].dt.date == today]
            week_sales = df[df['date'].dt.date >= last_week]
            
            c_rep1, c_rep2 = st.columns(2)
            with c_rep1:
                st.markdown(f"<div class='stat-card'><h3>💰 مبيعات اليوم</h3><h2>{day_sales['amount'].sum():.2f} ₪</h2><p>الربح: {day_sales['profit'].sum():.2f}</p></div>", unsafe_allow_html=True)
            with c_rep2:
                st.markdown(f"<div class='stat-card'><h3>📅 مبيعات الأسبوع</h3><h2>{week_sales['amount'].sum():.2f} ₪</h2><p>الربح: {week_sales['profit'].sum():.2f}</p></div>", unsafe_allow_html=True)
            
            st.write("### تفاصيل مبيعات اليوم")
            st.dataframe(day_sales[['date', 'item', 'amount', 'method']])
        else:
            st.info("لا توجد مبيعات مسجلة بعد.")

    if st.sidebar.button("💾 حفظ البيانات"):
        save_all(); st.sidebar.success("تم الحفظ!")
