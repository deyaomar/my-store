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
ADJUST_FILE = 'inventory_adjustments.csv'
CATS_FILE = 'categories_final.csv'

# تجهيز البيانات في Session State
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

# حالات البرنامج للتحكم في التنقل
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None
if 'success_msg' not in st.session_state: st.session_state.success_msg = None
if 'active_tab' not in st.session_state: st.session_state.active_tab = 0 # للتحكم في التبويبات

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
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 25px; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; width: 100%; color: white !important; font-weight: 900; }
    .report-box { background-color: #f8f9fa; border-right: 5px solid #27ae60; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

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
    menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 شاشة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير والإحصائيات", "⚙️ إدارة الأصناف"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        if st.session_state.show_cust_fields:
            with st.container(border=True):
                st.subheader("👤 ربط البيعة بزبون (اختياري)")
                c_n = st.text_input("اسم الزبون")
                c_p = st.text_input("رقم الجوال")
                col_c1, col_c2 = st.columns(2)
                if col_c1.button("💾 حفظ البيانات", type="primary"):
                    mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                    st.session_state.sales_df.loc[mask, 'customer_name'] = c_n
                    st.session_state.sales_df.loc[mask, 'customer_phone'] = c_p
                    auto_save(); st.session_state.show_cust_fields = False; st.session_state.success_msg = f"✅ تم الحفظ للزبون {c_n}"; st.rerun()
                if col_c2.button("➕ بيعة جديدة"):
                    st.session_state.show_cust_fields = False; st.rerun()
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
            
            if st.button("✅ تأكيد البيع والحفظ", type="primary"):
                if bill_items:
                    b_id = str(uuid.uuid4())
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save(); st.session_state.success_msg = "✅ تم حفظ الفاتورة"; st.session_state.show_cust_fields = True; st.rerun()

    # --- 2. المخزن والجرد المطور ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
        
        # استخدامactive_tab لنقل المستخدم تلقائياً
        tabs = st.tabs(["📋 قائمة الأصناف", "⚖️ الجرد اليدوي", "🗑️ تسجيل تالف", "🎯 نتائج الجرد الأخير"])
        
        with tabs[0]:
            if st.session_state.inventory:
                st.table(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية المسجلة": format_num(v['كمية'])} for k, v in st.session_state.inventory.items()]))
        
        with tabs[1]:
            st.subheader("⚖️ أدخل الكميات الموجودة حالياً بالمحل")
            new_counts = {}
            for item, data in st.session_state.inventory.items():
                cn, cs, ci = st.columns([2, 1, 2])
                cn.write(f"**{item}**")
                cs.info(f"النظام: {format_num(data['كمية'])}")
                res = ci.text_input("الواقع", key=f"real_{item}")
                if res != "": new_counts[item] = clean_num(res)
            
            if st.button("💾 اعتماد الجرد ونقلي للتقرير", type="primary"):
                recs = []
                today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                for it, rq in new_counts.items():
                    sq = st.session_state.inventory[it]['كمية']
                    if rq != sq:
                        diff = sq - rq
                        lv = diff * st.session_state.inventory[it]['ش شراء'] if 'شراء' in st.session_state.inventory[it] else diff * st.session_state.inventory[it].get('شراء', 0)
                        st.session_state.inventory[it]['كمية'] = rq
                        recs.append({'التاريخ': today_str, 'الصنف': it, 'الفارق بالوزن': diff, 'الفارق بالشيكل': lv})
                
                if recs:
                    new_adj = pd.DataFrame(recs).rename(columns={'الفارق بالوزن': 'diff_qty', 'الفارق بالشيكل': 'loss_value', 'التاريخ': 'date', 'الصنف': 'item'})
                    st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, new_adj], ignore_index=True)
                    auto_save()
                    st.session_state.success_msg = "✅ تم الجرد! انظر للنتائج في التبويب الرابع"
                    # هنا التغيير: نقوم بتخزين النتائج الأخيرة للعرض المباشر
                    st.session_state.last_jard = recs
                    st.rerun()

        with tabs[2]:
            with st.form("waste_f"):
                wi = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
                wq = st.number_input("الكمية", min_value=0.0)
                if st.form_submit_button("تسجيل"):
                    lv = wq * st.session_state.inventory[wi]['شراء']
                    st.session_state.inventory[wi]['كمية'] -= wq
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': wi, 'qty': wq, 'loss_value': lv}])], ignore_index=True)
                    auto_save(); st.rerun()

        with tabs[3]:
            st.subheader("🎯 تقرير الجرد الذي تم تنفيذه الآن")
            if 'last_jard' in st.session_state:
                df_last = pd.DataFrame(st.session_state.last_jard)
                st.table(df_last)
                total_loss = df_last['الفارق بالشيكل'].sum()
                st.warning(f"إجمالي خسارة هذا الجرد: {format_num(total_loss)} شيكل")
            else:
                st.info("لا يوجد جرد تم تنفيذه في هذه الجلسة بعد.")

    # --- 4. التقارير ---
    elif menu == "📊 التقارير والإحصائيات":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية والزبائن</h1>", unsafe_allow_html=True)
        tp = st.session_state.sales_df['profit'].sum()
        te = st.session_state.expenses_df['amount'].sum()
        tw = st.session_state.waste_df['loss_value'].sum()
        ta = st.session_state.adjust_df['loss_value'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("أرباح البيع", f"{format_num(tp)} ₪")
        c2.metric("المصروفات", f"{format_num(te)} ₪")
        c3.metric("عجز/تالف", f"{format_num(tw + ta)} ₪")
        c4.metric("صافي الربح الحقيقي", f"{format_num(tp - te - tw - ta)} ₪")
        
        st.markdown("---")
        st.subheader("👤 سجل المبيعات والزبائن")
        if not st.session_state.sales_df.empty:
            cust_rep = st.session_state.sales_df.groupby('bill_id').agg({'date':'first','customer_name':'first','amount':'sum'}).sort_values('date', ascending=False)
            st.table(cust_rep.rename(columns={'date':'التاريخ','customer_name':'اسم الزبون','amount':'المبلغ الكلي'}))
        
        st.markdown("---")
        st.subheader("⚖️ سجل فوارق الجرد التاريخي")
        if not st.session_state.adjust_df.empty:
            st.table(st.session_state.adjust_df.rename(columns={'date':'التاريخ','item':'الصنف','diff_qty':'الفارق بالوزن','loss_value':'الفارق بالشيكل'}))

    # --- باقي الأقسام ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 المصروفات</h1>")
        with st.form("exp"):
            r, a = st.text_input("البيان"), st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                auto_save(); st.rerun()

    elif menu == "⚙️ إدارة الأصناف":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>")
        with st.form("add"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            cb, cs, cq = st.columns(3)
            b, s, q = cb.text_input("شراء"), cs.text_input("بيع"), cq.text_input("كمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.rerun()
