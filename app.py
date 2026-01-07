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

# تحميل ومعالجة الملفات
if 'sales_df' not in st.session_state:
    if os.path.exists(SALES_FILE):
        df = pd.read_csv(SALES_FILE)
        for col in ['customer_name', 'customer_phone', 'bill_id', 'profit']:
            if col not in df.columns: df[col] = 0.0 if col == 'profit' else ""
        st.session_state.sales_df = df
    else:
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = pd.read_csv(EXPENSES_FILE) if os.path.exists(EXPENSES_FILE) else pd.DataFrame(columns=['date', 'reason', 'amount'])
if 'waste_df' not in st.session_state:
    st.session_state.waste_df = pd.read_csv(WASTE_FILE) if os.path.exists(WASTE_FILE) else pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

# حالات البرنامج
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
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 900; font-size: 18px; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 22px; text-align: center; margin-bottom: 15px; border-bottom: 1px solid white; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
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

    st.sidebar.markdown("<div class='sidebar-user'>مرحباً يا أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 شاشة البيع", "📦 المخزن والتالف", "💸 المصروفات", "📊 التقارير والإحصائيات", "⚙️ إدارة الأصناف"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>")
        if st.session_state.show_cust_fields:
            st.info("👤 بيانات الزبون للتحويل")
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الجوال")
            if st.button("💾 حفظ وفتح فاتورة جديدة", type="primary"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, 'customer_name'] = c_n
                st.session_state.sales_df.loc[mask, 'customer_phone'] = c_p
                auto_save(); st.session_state.show_cust_fields = False; st.rerun()
        else:
            c_p1, c_p2 = st.columns(2)
            if c_p2.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                st.session_state.p_method = "تطبيق"; st.rerun()
            if c_p1.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
                st.session_state.p_method = "نقداً"; st.rerun()
            
            bill_items = []
            for cat in st.session_state.categories:
                with st.expander(f"📂 {cat}", expanded=True):
                    items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                    for item, data in items.items():
                        c1, c2, c3 = st.columns([2, 1, 2])
                        with c1: st.write(f"**{item}**")
                        with c2: mode = st.radio("النوع", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                        with c3: val = clean_num(st.text_input("القيمة", key=f"v_{item}", label_visibility="collapsed"))
                        if val > 0:
                            qty = val if mode == "كمية" else val / data["بيع"]
                            amt = val if mode == "شيكل" else val * data["بيع"]
                            bill_items.append({"item": item, "qty": qty, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * qty})
            
            if st.button("✅ تأكيد البيع والحفظ", type="primary", use_container_width=True):
                if bill_items:
                    b_id = str(uuid.uuid4())
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': '', 'customer_phone': '', 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save()
                    if st.session_state.p_method == "تطبيق": st.session_state.show_cust_fields = True
                    else: st.session_state.success_msg = "✅ تم حفظ البيعة"; st.rerun()

    # --- 2. المخزن والجرد اليدوي (تم التعديل هنا) ---
    elif menu == "📦 المخزن والتالف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
        tab_j1, tab_j2, tab_j3 = st.tabs(["📊 عرض الكميات", "⚖️ الجرد اليدوي", "🗑️ تسجيل تالف"])
        
        with tab_j1:
            if st.session_state.inventory:
                disp_df = pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية الحالية": format_num(v['كمية']), "سعر البيع": format_num(v['بيع'])} for k, v in st.session_state.inventory.items()])
                st.table(disp_df)
        
        with tab_j2:
            st.subheader("⚖️ تعديل الكميات يدوياً")
            with st.form("manual_inventory"):
                item_to_adjust = st.selectbox("اختر الصنف لتعديله", list(st.session_state.inventory.keys()))
                new_qty = st.number_input("الكمية الحقيقية الموجودة حالياً", min_value=0.0, step=0.1)
                if st.form_submit_button("تحديث الكمية في النظام"):
                    old_qty = st.session_state.inventory[item_to_adjust]['كمية']
                    st.session_state.inventory[item_to_adjust]['كمية'] = new_qty
                    auto_save()
                    st.session_state.success_msg = f"✅ تم تحديث كمية {item_to_adjust} من {format_num(old_qty)} إلى {format_num(new_qty)}"
                    st.rerun()
        
        with tab_j3:
            st.subheader("🗑️ تسجيل بضاعة تالفة")
            with st.form("waste_form"):
                item_w = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
                qty_w = st.number_input("الكمية التالفة", min_value=0.0)
                if st.form_submit_button("خصم التالف من المخزن"):
                    loss = qty_w * st.session_state.inventory[item_w]['شراء']
                    st.session_state.inventory[item_w]['كمية'] -= qty_w
                    new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': item_w, 'qty': qty_w, 'loss_value': loss}
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                    auto_save()
                    st.session_state.success_msg = f"⚠️ تم تسجيل تالف لـ {item_w} بقيمة {format_num(loss)} ₪"
                    st.rerun()

    # --- باقي الأقسام ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>")
        with st.form("exp"):
            r = st.text_input("البيان")
            a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                auto_save(); st.session_state.success_msg = "✅ تم الحفظ"; st.rerun()
        st.dataframe(st.session_state.expenses_df.sort_index(ascending=False), use_container_width=True)

    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التقارير المادية</h1>")
        total_sales = st.session_state.sales_df['amount'].sum()
        total_profit = st.session_state.sales_df['profit'].sum()
        total_exp = st.session_state.expenses_df['amount'].sum()
        total_waste = st.session_state.waste_df['loss_value'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي المبيعات", f"{format_num(total_sales)} ₪")
        c2.metric("إجمالي المصروفات", f"{format_num(total_exp)} ₪")
        c3.metric("صافي الربح", f"{format_num(total_profit - total_exp - total_waste)} ₪")

    elif menu == "⚙️ إدارة الأصناف":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>")
        with st.form("add"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            c1, c2, c3 = st.columns(3)
            buy, sell, qty = c1.text_input("شراء"), c2.text_input("بيع"), c3.text_input("كمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(buy), "بيع": clean_num(sell), "كمية": clean_num(qty)}
                auto_save(); st.session_state.success_msg = f"✅ تم إضافة {n}"; st.rerun()
