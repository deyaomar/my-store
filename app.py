import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر 2026", layout="wide", page_icon="🍏")

# دالة تنظيف الأرقام للعرض (إزالة الأصفار الزائدة)
def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# دالة تنظيف الإدخال (تحويل النص لرقم)
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

# تحميل البيانات في الـ Session State
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

# إعدادات الحالة الأولية (الأولوية للتطبيق كما طلبت)
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'last_report' not in st.session_state: st.session_state.last_report = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)
    st.session_state.expenses_df.to_csv(EXPENSES_FILE, index=False)
    st.session_state.waste_df.to_csv(WASTE_FILE, index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv(CATS_FILE, index=False)

# 3. التصميم (CSS) - اللون الكحلي للقائمة، النص الأبيض العريض
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 900 !important; font-size: 18px !important; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 22px; text-align: center; margin-bottom: 15px; border-bottom: 1px solid white; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .report-card { background: #ffffff; padding: 15px; border-radius: 12px; border-right: 8px solid #2c3e50; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; width: 100%; color: white !important; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول والتحكم
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd == "123": st.session_state.logged_in = True; st.rerun()
            else: st.error("كلمة المرور غير صحيحة")
else:
    # القائمة الجانبية
    st.sidebar.markdown("<div class='sidebar-user'>مرحباً يا أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "🛒 شاشة البيع", 
        "📦 المخزن والتالف", 
        "💸 المصروفات", 
        "📊 التقارير والإحصائيات", 
        "⚙️ إدارة الأصناف"
    ])
    
    st.sidebar.markdown("---")
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
            # زر تطبيق هو الأول والأولوية له
            if c_p2.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                st.session_state.p_method = "تطبيق"; st.rerun()
            if c_p1.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
                st.session_state.p_method = "نقداً"; st.rerun()
            
            st.write(f"وسيلة الدفع المختارة: **{st.session_state.p_method}**")
            
            bill_items = []
            for cat in st.session_state.categories:
                with st.expander(f"📂 {cat}", expanded=True):
                    items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                    for item, data in items.items():
                        c1, c2, c3 = st.columns([2, 1, 2])
                        with c1: st.write(f"**{item}** (₪{format_num(data['بيع'])})")
                        with c2: mode = st.radio("النوع", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True)
                        with c3: val_in = st.text_input("القيمة", key=f"v_{item}", label_visibility="collapsed")
                        val = clean_num(val_in)
                        if val > 0:
                            qty = val if mode == "كمية" else val / data["بيع"]
                            amt = val if mode == "شيكل" else val * data["بيع"]
                            if qty <= data['كمية']:
                                bill_items.append({"item": item, "qty": qty, "amount": amt, "profit": (data["بيع"] - data["شراء"]) * qty})
                            else: st.warning(f"المتبقي من {item} هو {format_num(data['كمية'])} فقط")
            
            if st.button("✅ تأكيد البيع والحفظ", type="primary", use_container_width=True):
                if bill_items:
                    total = sum(i['amount'] for i in bill_items)
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.last_report = f"<div style='border:2px solid green; padding:20px; text-align:center; border-radius:10px; background:#f0fff0;'><h2>تم حفظ الفاتورة بنجاح!</h2><h3>الإجمالي: {format_num(total)} ₪</h3></div>"
                    auto_save(); st.rerun()

    # --- 2. المخزن والتالف ---
    elif menu == "📦 المخزن والتالف":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📊 الجرد الحالي", "🗑️ تسجيل تالف"])
        with t1:
            if st.session_state.inventory:
                disp_df = pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية": format_num(v['كمية']), "الشراء": format_num(v['شراء']), "البيع": format_num(v['بيع'])} for k, v in st.session_state.inventory.items()])
                st.table(disp_df)
            else: st.info("المخزن فارغ حالياً")
        with t2:
            with st.form("waste_form"):
                item_w = st.selectbox("اختر الصنف التالف", list(st.session_state.inventory.keys()))
                qty_w = st.number_input("الكمية التالفة", min_value=0.0, step=0.1)
                if st.form_submit_button("تسجيل الخسارة"):
                    if qty_w > 0 and qty_w <= st.session_state.inventory[item_w]['كمية']:
                        loss = qty_w * st.session_state.inventory[item_w]['شراء']
                        st.session_state.inventory[item_w]['كمية'] -= qty_w
                        new_w = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': item_w, 'qty': qty_w, 'loss_value': loss}
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                        auto_save(); st.success(f"تم خصم {qty_w} من {item_w}"); st.rerun()
                    else: st.error("الكمية غير صحيحة أو أكبر من المتوفر")

    # --- 3. المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            reason = st.text_input("بيان المصروف (مثلاً: إيجار، كهرباء)")
            amt_e = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ المصروف"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'reason': reason, 'amount': amt_e}])], ignore_index=True)
                auto_save(); st.success("تم حفظ المصروف بنجاح"); st.rerun()
        st.write("### سجل المصروفات السابقة")
        st.dataframe(st.session_state.expenses_df.sort_values(by='date', ascending=False), use_container_width=True)

    # --- 4. التقارير والإحصائيات ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التحليل المالي</h1>", unsafe_allow_html=True)
        c_d1, c_d2 = st.columns(2)
        start_date = c_d1.date_input("من تاريخ", datetime.now().date())
        end_date = c_d2.date_input("إلى تاريخ", datetime.now().date())
        
        # تصفية البيانات حسب التاريخ
        for df_name in ['sales_df', 'expenses_df', 'waste_df']:
            st.session_state[df_name]['date_only'] = pd.to_datetime(st.session_state[df_name]['date']).dt.date
        
        f_sales = st.session_state.sales_df[(st.session_state.sales_df['date_only'] >= start_date) & (st.session_state.sales_df['date_only'] <= end_date)]
        f_exp = st.session_state.expenses_df[(st.session_state.expenses_df['date_only'] >= start_date) & (st.session_state.expenses_df['date_only'] <= end_date)]
        f_waste = st.session_state.waste_df[(st.session_state.waste_df['date_only'] >= start_date) & (st.session_state.waste_df['date_only'] <= end_date)]
        
        s_sum = f_sales['amount'].sum()
        p_sum = f_sales['profit'].sum()
        e_sum = f_exp['amount'].sum()
        w_sum = f_waste['loss_value'].sum()
        net_profit = p_sum - e_sum - w_sum
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("إجمالي المبيعات", f"{format_num(s_sum)} ₪")
        col2.metric("إجمالي المصاريف", f"{format_num(e_sum)} ₪")
        col3.metric("خسائر التالف", f"{format_num(w_sum)} ₪")
        col4.metric("صافي الربح", f"{format_num(net_profit)} ₪")
        
        if not f_sales.empty:
            st.write("### مبيعات الأصناف")
            fig = px.bar(f_sales.groupby('item')['amount'].sum().reset_index(), x='item', y='amount', color='amount', color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)

    # --- 5. إدارة الأصناف والإعدادات ---
    elif menu == "⚙️ إدارة الأصناف":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات وإدارة الأصناف</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["🆕 إضافة صنف", "✏️ تعديل/حذف صنف", "📂 إدارة الأقسام"])
        
        with tab1:
            with st.form("add_new_item"):
                name = st.text_input("اسم الصنف")
                cat = st.selectbox("اختر القسم", st.session_state.categories)
                # المربعات الصغيرة بجانب بعضها كما طلبت
                c1, c2, c3 = st.columns(3)
                buy = c1.text_input("سعر الشراء")
                sell = c2.text_input("سعر البيع")
                qty = c3.text_input("الكمية")
                if st.form_submit_button("✅ إضافة للمخزن"):
                    if name:
                        st.session_state.inventory[name] = {"قسم": cat, "شراء": clean_num(buy), "بيع": clean_num(sell), "كمية": clean_num(qty)}
                        auto_save()
                        st.success("✅ تم إضافة الصنف بنجاح!") # رسالة النجاح
                        st.rerun()

        with tab2:
            edit_item = st.selectbox("اختر صنف للتعديل", [""] + list(st.session_state.inventory.keys()))
            if edit_item:
                d = st.session_state.inventory[edit_item]
                ce1, ce2, ce3 = st.columns(3)
                n_buy = ce1.text_input("سعر الشراء", value=format_num(d['شراء']))
                n_sell = ce2.text_input("سعر البيع", value=format_num(d['بيع']))
                n_qty = ce3.text_input("الكمية", value=format_num(d['كمية']))
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("💾 حفظ التعديلات", use_container_width=True):
                    st.session_state.inventory[edit_item].update({"شراء": clean_num(n_buy), "بيع": clean_num(n_sell), "كمية": clean_num(n_qty)})
                    auto_save(); st.success("تم التعديل بنجاح"); st.rerun()
                if col_b2.button("🗑️ حذف الصنف نهائياً", use_container_width=True):
                    del st.session_state.inventory[edit_item]
                    auto_save(); st.warning("تم حذف الصنف"); st.rerun()

        with tab3:
            st.subheader("إضافة قسم جديد")
            new_cat_name = st.text_input("اسم القسم الجديد")
            if st.button("➕ إضافة القسم"):
                if new_cat_name and new_cat_name not in st.session_state.categories:
                    st.session_state.categories.append(new_cat_name)
                    auto_save(); st.success(f"تم إضافة قسم {new_cat_name}"); st.rerun()
            
            st.markdown("---")
            st.subheader("حذف قسم")
            del_cat_name = st.selectbox("اختر القسم المراد حذفه", st.session_state.categories)
            if st.button("❌ حذف القسم"):
                if len(st.session_state.categories) > 1:
                    st.session_state.categories.remove(del_cat_name)
                    auto_save(); st.warning(f"تم حذف قسم {del_cat_name}"); st.rerun()
                else: st.error("لا يمكنك حذف كل الأقسام!")
