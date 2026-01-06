import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المحاسبي", layout="wide", page_icon="🍏")

# وظيفة لتحويل النص لرقم (تعالج الفاصلة والنقطة)
def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        processed = str(text).replace(',', '.').replace('،', '.')
        return float(processed)
    except:
        return 0.0

# 2. ملفات البيانات
DB_FILE = 'inventory_final.csv'
SALES_FILE = 'sales_final.csv'
CATS_FILE = 'categories_final.csv'

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame({'name': st.session_state.categories}).to_csv(CATS_FILE, index=False)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

# 3. الهوية البصرية (رصاصي غامق + أخضر فاقع)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: 900 !important; font-size: 20px !important; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; color: white !important; border: 2px solid #2ecc71 !important; height: 3.5em; width: 100%; font-weight: bold; }
    .stButton > button[kind="secondary"] { background-color: #ecf0f1 !important; color: #2c3e50 !important; height: 3.5em; width: 100%; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .success-box { background-color: #d4edda; border-right: 10px solid #28a745; padding: 20px; border-radius: 8px; color: #155724; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd == "123":
                st.session_state.logged_in = True
                st.rerun()
else:
    # القائمة الجانبية
    st.sidebar.markdown("<h2 style='text-align:center;'>🍎 القائمة</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("", ["🛒 شاشة البيع", "📦 المخزن والأصناف", "📊 التقارير"], label_visibility="collapsed")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع (مع تقرير الجرد الفوري) ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        
        # مكان ظهور رسالة النجاح
        success_placeholder = st.empty()
        
        if 'p_method' not in st.session_state: st.session_state.p_method = "نقداً"
        
        cp1, cp2 = st.columns(2)
        with cp1:
            if st.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
                st.session_state.p_method = "نقداً"; st.rerun()
        with cp2:
            if st.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                st.session_state.p_method = "تطبيق"; st.rerun()

        bill_items = []
        for cat in st.session_state.categories:
            with st.expander(f"📂 {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item, data in items.items():
                    c1, c2, c3, c4 = st.columns([0.5, 2, 2, 2])
                    with c1: sel = st.checkbox("", key=f"s_{item}")
                    with c2: 
                        st.markdown(f"**{item}**")
                        st.caption(f"متوفر: {data['كمية']:.1f}")
                    with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
                    with c4: val_txt = st.text_input("0", key=f"v_{item}", label_visibility="collapsed")
                    
                    val = clean_num(val_txt)
                    if sel and val > 0:
                        q = val if mode == "كمية" else val / data["بيع"]
                        bill_items.append({
                            "item": item, 
                            "qty": q, 
                            "amount": (val if mode == "شيكل" else val * data["بيع"]), 
                            "profit": (data["بيع"] - data["شراء"]) * q
                        })

        if st.button("✅ تأكيد عملية البيع", use_container_width=True, type="primary"):
            if bill_items:
                report_text = "### ✅ تم تأكيد عملية البيع بنجاح\n\n"
                report_text += "| الصنف | الكمية المباعة | السعر المدفوع | المتبقي في المخزن |\n"
                report_text += "| :--- | :--- | :--- | :--- |\n"
                
                for e in bill_items:
                    # خصم الكمية
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    remaining = st.session_state.inventory[e["item"]]["كمية"]
                    
                    # إضافة للتقرير
                    report_text += f"| {e['item']} | {e['qty']:.2f} كجم | {e['amount']:.1f} شيكل | **{remaining:.1f} كجم** |\n"
                    
                    # حفظ في السجل
                    new_sale = pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method}])
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_sale], ignore_index=True)
                
                auto_save()
                
                # عرض التقرير في صندوق النجاح
                with success_placeholder.container():
                    st.markdown(f"<div class='success-box'>{report_text}</div>", unsafe_allow_html=True)
                
                st.balloons()
            else:
                st.warning("يا أبو عمر، حدد الأصناف اللي بدك تبيعها أول!")

    # --- باقي الكود (المخزن والتقارير) كما هو لضمان الاستقرار ---
    elif menu == "📦 المخزن والأصناف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        # (بقية كود المخزن...)
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("اسم الصنف")
                c = st.selectbox("القسم", st.session_state.categories)
                q, b, s = st.columns(3)
                qty = q.text_input("الكمية")
                buy = b.text_input("شراء")
                sell = s.text_input("بيع")
                if st.form_submit_button("حفظ"):
                    st.session_state.inventory[n] = {"كمية": clean_num(qty), "شراء": clean_num(buy), "بيع": clean_num(sell), "قسم": c}
                    auto_save(); st.rerun()
        for cat in st.session_state.categories:
            st.markdown(f"### 🏷️ {cat}")
            its = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            for it, d in its.items():
                r1, r2, r3, r4, r5 = st.columns([2, 1, 1, 0.5, 0.5])
                r1.write(f"**{it}**")
                r2.write(f"📦 {d['كمية']:.1f}")
                r3.write(f"💰 {d['بيع']}")
                if r4.button("📝", key=f"e_{it}"): st.session_state.editing = it
                if r5.button("🗑️", key=f"d_{it}"):
                    del st.session_state.inventory[it]; auto_save(); st.rerun()

    elif menu == "📊 التقارير":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
        df = st.session_state.sales_df.copy()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            st.metric("إجمالي المبيعات", f"{df['amount'].sum():.1f} ₪")
            st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
