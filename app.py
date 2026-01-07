import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

# 2. ملفات البيانات
DB_FILE = 'inventory_final.csv'
SALES_FILE = 'sales_final.csv'
EXPENSES_FILE = 'expenses_final.csv'
WASTE_FILE = 'waste_final.csv'
CATS_FILE = 'categories_final.csv'

# تحميل ومعالجة الملفات وضمان وجود الأعمدة
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = pd.read_csv(EXPENSES_FILE) if os.path.exists(EXPENSES_FILE) else pd.DataFrame(columns=['date', 'reason', 'amount'])
if 'waste_df' not in st.session_state:
    st.session_state.waste_df = pd.read_csv(WASTE_FILE) if os.path.exists(WASTE_FILE) else pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None
if 'success_msg' not in st.session_state: st.session_state.success_msg = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)
    st.session_state.expenses_df.to_csv(EXPENSES_FILE, index=False)
    st.session_state.waste_df.to_csv(WASTE_FILE, index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv(CATS_FILE, index=False)

# 3. التصميم (CSS)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 22px; text-align: center; border-bottom: 1px solid white; padding-bottom:10px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .stMetric { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None

    st.sidebar.markdown(f"<div class='sidebar-user'>مرحباً يا أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 شاشة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير والإحصائيات", "⚙️ إدارة الأصناف"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        if st.session_state.show_cust_fields:
            st.success("✅ تم حفظ البيعة! أدخل بيانات الزبون للتحويل:")
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الجوال")
            if st.button("💾 حفظ البيانات وإتمام الفاتورة", type="primary"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, 'customer_name'] = c_n
                st.session_state.sales_df.loc[mask, 'customer_phone'] = c_p
                auto_save(); st.session_state.show_cust_fields = False; st.rerun()
        else:
            m1, m2 = st.columns(2)
            if m2.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary", use_container_width=True):
                st.session_state.p_method = "تطبيق"; st.rerun()
            if m1.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary", use_container_width=True):
                st.session_state.p_method = "نقداً"; st.rerun()
            
            bill_items = []
            for cat in st.session_state.categories:
                with st.expander(f"📂 {cat}", expanded=True):
                    items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                    for item, data in items.items():
                        c1, c2, c3 = st.columns([2, 1, 2])
                        with c1: st.write(f"**{item}** (₪{format_num(data['بيع'])})")
                        with c2: mode = st.radio("النوع", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                        with c3: val = clean_num(st.text_input("القيمة", key=f"v_{item}", label_visibility="collapsed"))
                        if val > 0:
                            qty = val if mode == "كمية" else val / data["بيع"]
                            amt = val if mode == "شيكل" else val * data["بيع"]
                            bill_items.append({"item": item, "qty": qty, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * qty})
            
            if st.button("✅ تأكيد وحفظ الفاتورة", type="primary", use_container_width=True):
                if bill_items:
                    b_id = str(uuid.uuid4())
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': '', 'customer_phone': '', 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save()
                    if st.session_state.p_method == "تطبيق": st.session_state.show_cust_fields = True
                    else: st.session_state.success_msg = "✅ تم تسجيل البيعة النقدية بنجاح"; st.rerun()

    # --- 2. المخزن والجرد (التعديلات المطلوبة هنا) ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📊 عرض الكميات", "⚖️ الجرد اليدوي", "🗑️ تسجيل تالف"])
        
        with tab1:
            if st.session_state.inventory:
                disp_df = pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية المسجلة": format_num(v['كمية']), "سعر البيع": format_num(v['بيع'])} for k, v in st.session_state.inventory.items()])
                st.table(disp_df)
        
        with tab2:
            st.subheader("⚖️ تعديل الكميات (مطابقة الواقع)")
            with st.form("manual_adjust"):
                item_adj = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
                # إظهار الكمية المسجلة الحالية
                current_in_sys = st.session_state.inventory[item_adj]['كمية']
                st.info(f"الكمية المسجلة حالياً في النظام لهذا الصنف: **{format_num(current_in_sys)}**")
                
                new_q = st.number_input("الكمية الفعلية الموجودة في المحل الآن", min_value=0.0, step=0.1)
                if st.form_submit_button("تحديث الكمية"):
                    st.session_state.inventory[item_adj]['كمية'] = new_q
                    auto_save()
                    st.session_state.success_msg = f"✅ تم تحديث كمية ({item_adj}) بنجاح."
                    st.rerun()
        
        with tab3:
            st.subheader("🗑️ تسجيل بضاعة تالفة")
            with st.form("waste_add"):
                w_item = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
                w_qty = st.number_input("الكمية التالفة", min_value=0.0, step=0.1)
                if st.form_submit_button("حفظ التالف وخصمه من المخزن"):
                    if w_qty > 0:
                        loss = w_qty * st.session_state.inventory[w_item]['شراء']
                        st.session_state.inventory[w_item]['كمية'] -= w_qty
                        new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'loss_value': loss}
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                        auto_save()
                        st.session_state.success_msg = f"⚠️ تم تسجيل تالف ({w_item}) وخصم قيمته من الأرباح."
                        st.rerun()

    # --- 4. التقارير (تقرير التالف وخصمه من الربح) ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
        
        total_sales = st.session_state.sales_df['amount'].sum()
        total_profit_from_sales = st.session_state.sales_df['profit'].sum()
        total_expenses = st.session_state.expenses_df['amount'].sum()
        total_waste_loss = st.session_state.waste_df['loss_value'].sum()
        
        # الربح الصافي النهائي
        final_net_profit = total_profit_from_sales - total_expenses - total_waste_loss
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي المبيعات", f"{format_num(total_sales)} ₪")
        c2.metric("إجمالي المصروفات", f"{format_num(total_expenses)} ₪")
        c3.metric("خسائر التالف", f"{format_num(total_waste_loss)} ₪")
        c4.metric("صافي الربح الحقيقي", f"{format_num(final_net_profit)} ₪", delta=format_num(final_net_profit))
        
        st.markdown("---")
        st.subheader("📋 تقرير التالف المفصل")
        if not st.session_state.waste_df.empty:
            st.dataframe(st.session_state.waste_df.sort_index(ascending=False), use_container_width=True)
        else:
            st.write("لا يوجد تالف مسجل حتى الآن.")

    # --- باقي الأقسام ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>")
        with st.form("exp"):
            r = st.text_input("بيان المصروف")
            a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                auto_save(); st.session_state.success_msg = "✅ تم حفظ المصروف"; st.rerun()
        st.dataframe(st.session_state.expenses_df.sort_index(ascending=False), use_container_width=True)

    elif menu == "⚙️ إدارة الأصناف":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>")
        with st.form("add_item"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            c1, c2, c3 = st.columns(3)
            buy, sell, qty = c1.text_input("شراء"), c2.text_input("بيع"), c3.text_input("كمية")
            if st.form_submit_button("إضافة"):
                if n:
                    st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(buy), "بيع": clean_num(sell), "كمية": clean_num(qty)}
                    auto_save(); st.session_state.success_msg = f"✅ تم إضافة {n}"; st.rerun()
