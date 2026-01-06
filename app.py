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

# وظيفة الحفظ التلقائي
def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame({'name': st.session_state.categories}).to_csv(CATS_FILE, index=False)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)

# تحميل البيانات
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

# 3. تصميم CSS فاخر واحترافي
st.markdown("""
    <style>
    /* تنسيق القائمة الجانبية */
    [data-testid="stSidebar"] { background-color: #1e4d2b; color: white; border-left: 3px solid gold; }
    [data-testid="stSidebar"] * { color: white !important; font-size: 18px !important; }
    
    /* أزرار الدفع الملونة */
    .active-pay { background-color: #2e7d32 !important; color: white !important; border: 2px solid gold !important; font-weight: bold; }
    .inactive-pay { background-color: #ffffff !important; color: #1e4d2b !important; border: 1px solid #1e4d2b !important; }
    
    /* بطاقات التقارير */
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid gold; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
    
    /* العناوين */
    .main-title { color: #1e4d2b; text-align: center; border-bottom: 2px solid gold; padding-bottom: 10px; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == "123":
            st.session_state.logged_in = True
            st.rerun()
else:
    # القائمة الجانبية الفاخرة
    st.sidebar.markdown("<h2 style='text-align:center;'>🍏 لوحة التحكم</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("انتقل إلى:", ["🛒 شاشة البيع", "📦 المخزن والأصناف", "📊 التقارير المالية"])
    
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة مبيعات جديدة</h1>", unsafe_allow_html=True)
        
        if 'p_method' not in st.session_state: st.session_state.p_method = "نقداً"
        
        st.write("### اختر طريقة الدفع:")
        col_p1, col_p2 = st.columns(2)
        
        # تنسيق الأزرار حسب الاختيار
        cash_style = "active-pay" if st.session_state.p_method == "نقداً" else "inactive-pay"
        app_style = "active-pay" if st.session_state.p_method == "تطبيق" else "inactive-pay"
        
        with col_p1:
            if st.button("💵 نقداً (كاش)", key="btn_cash", use_container_width=True):
                st.session_state.p_method = "نقداً"
                st.rerun()
        with col_p2:
            if st.button("📱 تطبيق بنكي", key="btn_app", use_container_width=True):
                st.session_state.p_method = "تطبيق"
                st.rerun()
        
        st.markdown(f"<div style='text-align:center; padding:10px; border-radius:10px; background-color:#2e7d32; color:white;'>تم اختيار: <b>{st.session_state.p_method}</b></div>", unsafe_allow_html=True)

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

        if st.button("🚀 تأكيد العملية والحفظ", use_container_width=True):
            if bill_items:
                for e in bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_sale = pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method}])
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_sale], ignore_index=True)
                auto_save()
                st.success("تم الحفظ بنجاح!"); st.balloons(); st.rerun()

    # --- 2. المخزن والأصناف مع ميزة التعديل ---
    elif menu == "📦 المخزن والأصناف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("اسم الصنف")
                c = st.selectbox("القسم", st.session_state.categories)
                q, b, s = st.columns(3)
                qty = q.number_input("الكمية")
                buy = b.number_input("شراء")
                sell = s.number_input("بيع")
                if st.form_submit_button("إضافة للمخزن"):
                    st.session_state.inventory[n] = {"كمية": qty, "شراء": buy, "بيع": sell, "قسم": c}
                    auto_save(); st.rerun()

        for cat in st.session_state.categories:
            st.subheader(f"🏷️ {cat}")
            items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            for it, data in items.items():
                c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                c1.write(f"**{it}**")
                c2.write(f"📦 {data['كمية']:.1f}")
                c3.write(f"💰 {data['بيع']}")
                
                # أيقونة التعديل
                if c4.button("📝", key=f"edit_{it}"):
                    st.session_state.edit_item = it
                
                # أيقونة الحذف
                if c5.button("🗑️", key=f"del_{it}"):
                    del st.session_state.inventory[it]
                    auto_save(); st.rerun()

        # نافذة التعديل المنبثقة
        if 'edit_item' in st.session_state:
            target = st.session_state.edit_item
            st.markdown(f"### 🛠️ تعديل: {target}")
            with st.container():
                u_q = st.number_input("الكمية الجديدة", value=st.session_state.inventory[target]["كمية"])
                u_s = st.number_input("سعر البيع الجديد", value=st.session_state.inventory[target]["بيع"])
                if st.button("حفظ التعديل"):
                    st.session_state.inventory[target]["كمية"] = u_q
                    st.session_state.inventory[target]["بيع"] = u_s
                    del st.session_state.edit_item
                    auto_save(); st.rerun()

    # --- 3. التقارير اليومية والأسبوعية ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير والتحليلات</h1>", unsafe_allow_html=True)
        
        df = st.session_state.sales_df.copy()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            today = datetime.now().date()
            last_week = today - timedelta(days=7)
            
            # حسابات اليوم والأسبوع
            day_total = df[df['date'].dt.date == today]['amount'].sum()
            day_profit = df[df['date'].dt.date == today]['profit'].sum()
            week_total = df[df['date'].dt.date >= last_week]['amount'].sum()
            week_profit = df[df['date'].dt.date >= last_week]['profit'].sum()
            
            # عرض البطاقات
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div class='report-card'><h3>📅 اليوم</h3><h2>{day_total:.1f} ₪</h2><p>صافي الربح: {day_profit:.1f}</p></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='report-card'><h3>📅 آخر 7 أيام</h3><h2>{week_total:.1f} ₪</h2><p>صافي الربح: {week_profit:.1f}</p></div>", unsafe_allow_html=True)
            
            st.write("---")
            st.write("### سجل العمليات:")
            st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
        else:
            st.info("لا توجد بيانات مبيعات لعرضها.")
