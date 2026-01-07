import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

# دالة تنظيف الأرقام للعرض
def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# دالة تنظيف الإدخال
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

# تحميل البيانات
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = pd.read_csv(EXPENSES_FILE) if os.path.exists(EXPENSES_FILE) else pd.DataFrame(columns=['date', 'reason', 'amount'])
if 'waste_df' not in st.session_state:
    st.session_state.waste_df = pd.read_csv(WASTE_FILE) if os.path.exists(WASTE_FILE) else pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'last_report' not in st.session_state: st.session_state.last_report = None
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
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 900 !important; font-size: 18px !important; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 22px; text-align: center; margin-bottom: 15px; border-bottom: 1px solid white; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; width: 100%; color: white !important; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd == "123": st.session_state.logged_in = True; st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
else:
    # إظهار رسالة النجاح في رأس الصفحة إذا وجدت
    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None # تختفي عند التحديث القادم

    st.sidebar.markdown("<div class='sidebar-user'>مرحباً يا أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "🛒 شاشة البيع", 
        "📦 المخزن والتالف", 
        "💸 المصروفات", 
        "📊 التقارير والإحصائيات", 
        "⚙️ إدارة الأصناف"
    ])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        if st.session_state.last_report:
            st.markdown(st.session_state.last_report, unsafe_allow_html=True)
            if st.button("➕ فاتورة جديدة", type="primary"):
                st.session_state.last_report = None; st.rerun()
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
                        with c1: st.write(f"**{item}** (₪{format_num(data['بيع'])})")
                        with c2: mode = st.radio("النوع", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                        with c3: val = clean_num(st.text_input("القيمة", key=f"v_{item}", label_visibility="collapsed"))
                        if val > 0:
                            qty = val if mode == "كمية" else val / data["بيع"]
                            amt = val if mode == "شيكل" else val * data["بيع"]
                            if qty <= data['كمية']:
                                bill_items.append({"item": item, "qty": qty, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * qty})
            
            if st.button("✅ تأكيد البيع", type="primary", use_container_width=True):
                if bill_items:
                    total = sum(i['amount'] for i in bill_items)
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.last_report = f"<div style='border:2px solid green; padding:20px; text-align:center; border-radius:10px;'><h3>تم الحفظ! الإجمالي: {format_num(total)} ₪</h3></div>"
                    auto_save(); st.rerun()

    # --- 2. المخزن والتالف ---
    elif menu == "📦 المخزن والتالف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 الجرد الحالي", "🗑️ تسجيل تالف"])
        with t1:
            if st.session_state.inventory:
                disp_df = pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية": format_num(v['كمية']), "البيع": format_num(v['بيع'])} for k, v in st.session_state.inventory.items()])
                st.table(disp_df)
        with t2:
            with st.form("waste"):
                item_w = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
                qty_w = st.number_input("الكمية", min_value=0.0)
                if st.form_submit_button("تسجيل الخسارة"):
                    loss = qty_w * st.session_state.inventory[item_w]['شراء']
                    st.session_state.inventory[item_w]['كمية'] -= qty_w
                    new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': item_w, 'qty': qty_w, 'loss_value': loss}
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                    auto_save(); st.session_state.success_msg = "✅ تم تسجيل التالف بنجاح"; st.rerun()

    # --- 3. المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            reason = st.text_input("البيان")
            amt_e = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ المصروف"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': reason, 'amount': amt_e}])], ignore_index=True)
                auto_save(); st.session_state.success_msg = "✅ تم حفظ المصروف"; st.rerun()
        st.dataframe(st.session_state.expenses_df, use_container_width=True)

    # --- 4. التقارير ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التقارير المادية</h1>", unsafe_allow_html=True)
        st.write(f"إجمالي المبيعات: {format_num(st.session_state.sales_df['amount'].sum())} ₪")
        st.write(f"صافي الربح: {format_num(st.session_state.sales_df['profit'].sum() - st.session_state.expenses_df['amount'].sum())} ₪")

    # --- 5. إدارة الأصناف ---
    elif menu == "⚙️ إدارة الأصناف":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["🆕 إضافة صنف", "✏️ تعديل/حذف صنف", "📂 إدارة الأقسام"])
        
        with tab1:
            with st.form("add_form"):
                name = st.text_input("اسم الصنف")
                cat = st.selectbox("اختر القسم", st.session_state.categories)
                c1, c2, c3 = st.columns(3)
                buy = c1.text_input("سعر الشراء")
                sell = c2.text_input("سعر البيع")
                qty = c3.text_input("الكمية")
                if st.form_submit_button("إضافة للمخزن"):
                    if name:
                        st.session_state.inventory[name] = {"قسم": cat, "شراء": clean_num(buy), "بيع": clean_num(sell), "كمية": clean_num(qty)}
                        auto_save()
                        st.session_state.success_msg = f"✅ تم إضافة صنف ({name}) بنجاح!" # سيظهر فوق
                        st.rerun()

        with tab2:
            edit_item = st.selectbox("اختر صنف للتعديل", [""] + list(st.session_state.inventory.keys()))
            if edit_item:
                d = st.session_state.inventory[edit_item]
                ce1, ce2, ce3 = st.columns(3)
                n_buy = ce1.text_input("سعر الشراء", value=format_num(d['شراء']))
                n_sell = ce2.text_input("سعر البيع", value=format_num(d['بيع']))
                n_qty = ce3.text_input("الكمية", value=format_num(d['كمية']))
                if st.button("حفظ التعديلات"):
                    st.session_state.inventory[edit_item].update({"شراء": clean_num(n_buy), "بيع": clean_num(n_sell), "كمية": clean_num(n_qty)})
                    auto_save(); st.session_state.success_msg = "✅ تم تعديل الصنف"; st.rerun()
                if st.button("🗑️ حذف الصنف"):
                    del st.session_state.inventory[edit_item]
                    auto_save(); st.session_state.success_msg = "⚠️ تم حذف الصنف"; st.rerun()

        with tab3:
            new_cat = st.text_input("إضافة قسم جديد")
            if st.button("➕ إضافة القسم"):
                if new_cat and new_cat not in st.session_state.categories:
                    st.session_state.categories.append(new_cat); auto_save(); st.rerun()
            del_cat = st.selectbox("حذف قسم", st.session_state.categories)
            if st.button("❌ حذف القسم"):
                st.session_state.categories.remove(del_cat); auto_save(); st.rerun()
