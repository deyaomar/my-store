import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المحاسبي", layout="wide", page_icon="🍏")

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

# 3. الهوية البصرية (رصاصي غامق موحد)
st.markdown("""
    <style>
    /* القائمة الجانبية */
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: 800 !important; font-size: 20px !important; }
    
    /* أزرار الدفع (تلوين الأخضر عند الاختيار) */
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; color: white !important; border: 2px solid #2ecc71 !important; height: 4em; width: 100%; font-weight: bold; }
    .stButton > button[kind="secondary"] { background-color: #ecf0f1 !important; color: #2c3e50 !important; height: 4em; width: 100%; }

    /* العناوين والبطاقات */
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .report-card { background: #f8f9fa; padding: 20px; border-radius: 12px; border-right: 10px solid #2c3e50; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر المحاسبي</h1>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "123":
            st.session_state.logged_in = True
            st.rerun()
else:
    # القائمة المنسدلة المرتبة
    st.sidebar.markdown("<h2 style='text-align:center;'>🍎 القائمة</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("", ["🛒 شاشة البيع", "📦 المخزن والأصناف", "📊 التقارير"], label_visibility="collapsed")
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        
        if 'p_method' not in st.session_state: st.session_state.p_method = "نقداً"
        
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            if st.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
                st.session_state.p_method = "نقداً"; st.rerun()
        with c_p2:
            if st.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                st.session_state.p_method = "تطبيق"; st.rerun()

        bill_items = []
        for cat in st.session_state.categories:
            with st.expander(f"📂 {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item, data in items.items():
                    c1, c2, c3, c4 = st.columns([0.5, 2, 2, 2])
                    with c1: sel = st.checkbox("", key=f"s_{item}")
                    with c2: st.write(f"**{item}** ({data['كمية']:.1f})")
                    with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
                    with c4: val = st.number_input("0.0", min_value=0.0, key=f"v_{item}", label_visibility="collapsed")
                    if sel and val > 0:
                        q = val if mode == "كمية" else val / data["بيع"]
                        bill_items.append({"item": item, "qty": q, "amount": (val if mode == "شيكل" else val * data["بيع"]), "profit": (data["بيع"] - data["شراء"]) * q})

        if st.button("✅ تأكيد البيع", use_container_width=True, type="primary"):
            if bill_items:
                for e in bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_sale = pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method}])
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_sale], ignore_index=True)
                auto_save(); st.success("تم الحفظ!"); st.balloons(); st.rerun()

    # --- 2. المخزن والأصناف ---
    elif menu == "📦 المخزن والأصناف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        
        # إضافة قسم جديد
        with st.expander("📂 إضافة / حذف الأقسام"):
            nc = st.text_input("اسم القسم الجديد")
            if st.button("إضافة"):
                st.session_state.categories.append(nc); auto_save(); st.rerun()
            sc = st.selectbox("حذف قسم", st.session_state.categories)
            if st.button("حذف القسم المختار"):
                st.session_state.categories.remove(sc); auto_save(); st.rerun()

        # إضافة صنف جديد
        with st.expander("➕ إضافة صنف جديد للمخزن"):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("اسم الصنف")
                c = st.selectbox("القسم", st.session_state.categories)
                q, b, s = st.columns(3); qty = q.number_input("كمية"); buy = b.number_input("شراء"); sell = s.number_input("بيع")
                if st.form_submit_button("حفظ"):
                    st.session_state.inventory[n] = {"كمية": qty, "شراء": buy, "بيع": sell, "قسم": c}
                    auto_save(); st.rerun()

        # عرض الأصناف مع التعديل والحذف
        for cat in st.session_state.categories:
            st.markdown(f"### 🏷️ {cat}")
            items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            for it, data in items.items():
                c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 0.5, 0.5])
                c1.write(f"**{it}**")
                c2.write(f"📦 {data['كمية']:.1f}")
                c3.write(f"💰 {data['بيع']}")
                if c4.button("📝", key=f"e_{it}"): st.session_state.edit_it = it
                if c5.button("🗑️", key=f"d_{it}"):
                    del st.session_state.inventory[it]; auto_save(); st.rerun()

        if 'edit_it' in st.session_state:
            target = st.session_state.edit_it
            st.markdown(f"--- \n ### 🛠️ تعديل سريع: {target}")
            uq = st.number_input("الكمية الجديدة", value=st.session_state.inventory[target]["كمية"])
            us = st.number_input("سعر البيع الجديد", value=st.session_state.inventory[target]["بيع"])
            if st.button("تحديث البيانات"):
                st.session_state.inventory[target]["كمية"] = uq
                st.session_state.inventory[target]["بيع"] = us
                del st.session_state.edit_it; auto_save(); st.rerun()

    # --- 3. التقارير ---
    elif menu == "📊 التقارير":
        st.markdown("<h1 class='main-title'>📊 الأداء المالي</h1>", unsafe_allow_html=True)
        df = st.session_state.sales_df.copy()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            today = datetime.now().date()
            last_7 = today - timedelta(days=7)
            
            col1, col2 = st.columns(2)
            d_s = df[df['date'].dt.date == today]
            with col1: st.markdown(f"<div class='report-card'><h3>💰 مبيعات اليوم</h3><h2>{d_s['amount'].sum():.1f} ₪</h2><p>الربح: {d_s['profit'].sum():.1f}</p></div>", unsafe_allow_html=True)
            
            w_s = df[df['date'].dt.date >= last_7]
            with col2: st.markdown(f"<div class='report-card'><h3>📅 آخر 7 أيام</h3><h2>{w_s['amount'].sum():.1f} ₪</h2><p>الربح: {w_s['profit'].sum():.1f}</p></div>", unsafe_allow_html=True)
            
            st.write("---")
            st.write("### سجل المبيعات التفصيلي:")
            st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
