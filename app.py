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
ADJUST_FILE = 'inventory_adjustments.csv' # ملف جديد لسجل فروقات الجرد
CATS_FILE = 'categories_final.csv'

# تحميل الملفات وضمان وجود الأعمدة
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = pd.read_csv(EXPENSES_FILE) if os.path.exists(EXPENSES_FILE) else pd.DataFrame(columns=['date', 'reason', 'amount'])
if 'waste_df' not in st.session_state:
    st.session_state.waste_df = pd.read_csv(WASTE_FILE) if os.path.exists(WASTE_FILE) else pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])
if 'adjust_df' not in st.session_state:
    st.session_state.adjust_df = pd.read_csv(ADJUST_FILE) if os.path.exists(ADJUST_FILE) else pd.DataFrame(columns=['date', 'item', 'diff_qty', 'loss_value'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)
    st.session_state.expenses_df.to_csv(EXPENSES_FILE, index=False)
    st.session_state.waste_df.to_csv(WASTE_FILE, index=False)
    st.session_state.adjust_df.to_csv(ADJUST_FILE, index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv(CATS_FILE, index=False)

# 3. التنسيق الجمالي
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 900; font-size: 19px; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; margin-bottom: 20px; border-bottom: 2px solid white; padding-bottom: 10px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; width: 100%; color: white !important; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.form("login"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    if st.session_state.get('success_msg'):
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None

    st.sidebar.markdown("<div class='sidebar-user'>مرحباً يا أبو عمر</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 شاشة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير والإحصائيات", "⚙️ إدارة الأصناف"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        # (نفس كود البيع السابق لضمان الاستقرار)
        if st.session_state.get('show_cust_fields'):
            st.info("👤 بيانات الزبون")
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الجوال")
            if st.button("💾 حفظ البيانات", type="primary"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, 'customer_name'] = c_n
                st.session_state.sales_df.loc[mask, 'customer_phone'] = c_p
                auto_save(); st.session_state.show_cust_fields = False; st.rerun()
        else:
            m1, m2 = st.columns(2)
            if m2.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                st.session_state.p_method = "تطبيق"; st.rerun()
            if m1.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
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
            
            if st.button("✅ تأكيد البيع", type="primary"):
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

    # --- 2. المخزن والجرد المطور ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 الجرد اليدوي والمخزن</h1>", unsafe_allow_html=True)
        tab_list, tab_adjust = st.tabs(["📋 قائمة البضاعة الحالية", "⚖️ تنفيذ جرد كامل للمحل"])
        
        with tab_list:
            if st.session_state.inventory:
                st.table(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية في النظام": format_num(v['كمية'])} for k, v in st.session_state.inventory.items()]))
        
        with tab_adjust:
            st.subheader("قم بتسجيل الكميات الحقيقية الموجودة على الرف:")
            st.write("ملاحظة: الصنف الذي تتركه فارغاً لن يتم تعديله.")
            
            new_counts = {}
            for item, data in st.session_state.inventory.items():
                col_i, col_sys, col_real = st.columns([2, 1, 2])
                col_i.write(f"**{item}**")
                col_sys.info(f"المسجل: {format_num(data['كمية'])}")
                new_val = col_real.text_input("الكمية الحقيقية", key=f"adj_{item}", placeholder="أدخل الرقم هنا")
                if new_val != "":
                    new_counts[item] = clean_num(new_val)
            
            if st.button("💾 اعتماد الجرد وحساب الفوارق", type="primary"):
                adjust_records = []
                for it, real_q in new_counts.items():
                    sys_q = st.session_state.inventory[it]['كمية']
                    if real_q != sys_q:
                        diff = sys_q - real_q # الفرق (إذا موجب يعني نقص/عجز)
                        loss = diff * st.session_state.inventory[it]['شراء']
                        # تحديث المخزن
                        st.session_state.inventory[it]['كمية'] = real_q
                        # تسجيل في ملف الفوارق
                        adjust_records.append({'date': datetime.now().strftime("%Y-%m-%d"), 'item': it, 'diff_qty': diff, 'loss_value': loss})
                
                if adjust_records:
                    st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame(adjust_records)], ignore_index=True)
                    auto_save()
                    st.session_state.success_msg = "✅ تم تحديث المخزن وتسجيل فوارق الجرد"
                    st.rerun()
                else:
                    st.info("لا توجد فوارق في الكميات التي أدخلتها.")

    # --- 4. التقارير (إضافة فوارق الجرد) ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
        
        ts = st.session_state.sales_df['amount'].sum()
        tp = st.session_state.sales_df['profit'].sum()
        te = st.session_state.expenses_df['amount'].sum()
        tw = st.session_state.waste_df['loss_value'].sum()
        ta = st.session_state.adjust_df['loss_value'].sum() # خسائر فروقات الجرد
        
        # صافي الربح = ربح المبيعات - (مصروفات + تالف + عجز جرد)
        net_profit = tp - te - tw - ta
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي المبيعات", f"{format_num(ts)} ₪")
        c2.metric("المصروفات والتالف", f"{format_num(te + tw)} ₪")
        c3.metric("عجز الجرد اليدوي", f"{format_num(ta)} ₪")
        c4.metric("صافي الربح النهائي", f"{format_num(net_profit)} ₪", delta=format_num(net_profit))
        
        st.markdown("---")
        st.subheader("📋 تقرير فروقات الجرد اليدوي")
        if not st.session_state.adjust_df.empty:
            st.dataframe(st.session_state.adjust_df.sort_index(ascending=False), use_container_width=True)
        else:
            st.write("لم يتم تسجيل فوارق جرد بعد.")

    # --- باقي القوائم لضمان عمل الكود ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp_f"):
            r = st.text_input("البيان")
            a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                auto_save(); st.rerun()
        st.dataframe(st.session_state.expenses_df.sort_index(ascending=False), use_container_width=True)

    elif menu == "⚙️ إدارة الأصناف":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        with st.form("add_i"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            c1, c2, c3 = st.columns(3)
            b, s, q = c1.text_input("شراء"), c2.text_input("بيع"), c3.text_input("كمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.rerun()
