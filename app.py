import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة الاحترافية
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="🍏")

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

# 2. إدارة ملفات البيانات وتجهيزها
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        if os.path.exists(file):
            df = pd.read_csv(file)
            for c in cols: 
                if c not in df.columns: df[c] = 0.0 if 'amount' in c or 'profit' in c or 'loss' in c or 'qty' in c else ""
            st.session_state[state_key] = df
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv('inventory_final.csv', index_col=0).to_dict('index') if os.path.exists('inventory_final.csv') else {}
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

# حالات التشغيل
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None
if 'success_msg' not in st.session_state: st.session_state.success_msg = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv('inventory_final.csv')
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. واجهة المستخدم (تحسين الخطوط بناءً على طلبك)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    
    /* القائمة الجانبية - خلفية داكنة لإبراز الأبيض */
    [data-testid="stSidebar"] { background-color: #1e272e !important; border-left: 2px solid #27ae60; }
    
    /* جعل الخط أبيض وعريض جداً وضخم في القائمة */
    div[data-testid="stSidebar"] .stRadio div label p { 
        color: white !important; 
        font-weight: 900 !important; 
        font-size: 26px !important; 
        padding: 5px; 
    }
    
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 32px; text-align: center; margin-bottom: 25px; border-bottom: 3px solid #27ae60; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1,2,1])
    with col_l2:
        with st.form("login_form"):
            pwd = st.text_input("كلمة مرور الإدارة", type="password")
            if st.form_submit_button("دخول النظام"):
                if pwd == "123": st.session_state.logged_in = True; st.rerun()
                else: st.error("كلمة المرور غير صحيحة")
else:
    # القائمة الجانبية
    st.sidebar.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("التنقل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج آمن"):
        st.session_state.clear(); st.rerun()

    # --- 1. نقطة البيع (نفس كودك الأصلي) ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة بيع البضاعة</h1>", unsafe_allow_html=True)
        if st.session_state.show_cust_fields:
            with st.status("✅ تم حفظ الفاتورة بنجاح!"):
                c_n = st.text_input("اسم الزبون")
                c_p = st.text_input("رقم الهاتف")
                c_col1, c_col2 = st.columns(2)
                if c_col1.button("💾 حفظ وربط"):
                    mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                    st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                    auto_save(); st.session_state.show_cust_fields = False; st.rerun()
                if c_col2.button("⏩ تخطي"):
                    st.session_state.show_cust_fields = False; st.rerun()
        else:
            col_h1, col_h2 = st.columns([3, 1])
            with col_h2: st.session_state.p_method = st.radio("طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
            search_q = st.text_input("🔍 ابحث عن صنف...")
            bill_items = []
            for cat in st.session_state.categories:
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                if search_q: items = {k: v for k, v in items.items() if search_q in k}
                if items:
                    with st.expander(f"📂 {cat}", expanded=True):
                        for item, data in items.items():
                            c1, c2, c3 = st.columns([2, 1, 2])
                            c1.markdown(f"**{item}** \n<small>المتوفر: {format_num(data['كمية'])}</small>", unsafe_allow_html=True)
                            mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item}", horizontal=True)
                            val = clean_num(c3.text_input("المقدار", key=f"v_{item}"))
                            if val > 0:
                                qty = val if mode == "كجم" else val / data["بيع"]
                                bill_items.append({"item": item, "qty": qty, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * qty})
            if st.button("🚀 إتمام البيع", type="primary"):
                if bill_items:
                    b_id = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save(); st.session_state.show_cust_fields = True; st.rerun()

    # --- 2. المخزن والجرد (نفس كودك الأصلي) ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزون والجودة</h1>", unsafe_allow_html=True)
        t_list, t_jard, t_waste = st.tabs(["📋 الرصيد", "⚖️ الجرد", "🗑️ التالف"])
        with t_list: st.dataframe(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية": v['كمية']} for k, v in st.session_state.inventory.items()]), use_container_width=True)
        with t_jard:
             # كود الجرد الذي يحسب الفرق ويصحح المخزن
             new_counts = {}
             for item, data in st.session_state.inventory.items():
                 c_n, c_s, c_i = st.columns([2, 1, 2])
                 c_n.write(f"**{item}**")
                 res = c_i.text_input("الوزن الحقيقي", key=f"j_{item}")
                 if res != "": new_counts[item] = clean_num(res)
             if st.button("✔️ اعتماد الجرد"):
                 for it, rq in new_counts.items():
                     diff = st.session_state.inventory[it]['كمية'] - rq
                     st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': it, 'diff_qty': diff, 'loss_value': diff * st.session_state.inventory[it]['شراء']}])], ignore_index=True)
                     st.session_state.inventory[it]['كمية'] = rq
                 auto_save(); st.rerun()

    # --- 3. التقارير المالية (تم إضافة تفصيل اليوم كما طلبت) ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 لوحة التحكم والأرباح</h1>", unsafe_allow_html=True)
        
        # فلترة مبيعات اليوم
        today = datetime.now().strftime("%Y-%m-%d")
        df_s = st.session_state.sales_df.copy()
        df_s['day'] = pd.to_datetime(df_s['date']).dt.strftime("%Y-%m-%d")
        today_sales = df_s[df_s['day'] == today]

        # عرض إجمالي مبيعات اليوم بشكل بارز
        st.markdown(f"""<div style="background-color:#2c3e50; color:white; padding:20px; border-radius:15px; text-align:center; border-right:10px solid #27ae60;">
            <h2 style="margin:0;">إجمالي مبيعات اليوم</h2>
            <h1 style="font-size:50px; color:#27ae60;">{format_num(today_sales['amount'].sum())} ₪</h1>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        col1.metric("💰 كاش (نقداً)", f"{format_num(today_sales[today_sales['method']=='نقداً']['amount'].sum())} ₪")
        col2.metric("📱 تطبيق", f"{format_num(today_sales[today_sales['method']=='تطبيق']['amount'].sum())} ₪")
        
        st.divider()
        # الأرباح الإجمالية (التراكمية)
        tp = st.session_state.sales_df['profit'].sum()
        te = st.session_state.expenses_df['amount'].sum()
        tw = st.session_state.waste_df['loss_value'].sum()
        ta = st.session_state.adjust_df['loss_value'].sum()
        st.subheader(f"📈 صافي الربح النهائي: {format_num(tp - te - tw - ta)} ₪")

    # --- المصروفات والإعدادات (نفس كودك الأصلي) ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("البيان")
            a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                auto_save(); st.rerun()

    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        with st.form("add_i"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            b = st.text_input("شراء")
            s = st.text_input("بيع")
            q = st.text_input("كمية")
            if st.form_submit_button("حفظ الصنف"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                auto_save(); st.rerun()
