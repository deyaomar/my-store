import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📊")

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

# 2. إدارة ملفات البيانات
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
    if os.path.exists('inventory_final.csv'):
        try:
            inv_df = pd.read_csv('inventory_final.csv')
            inv_df = inv_df.drop_duplicates(subset=[inv_df.columns[0]], keep='last')
            st.session_state.inventory = inv_df.set_index(inv_df.columns[0]).to_dict('index')
        except: st.session_state.inventory = {}
    else: st.session_state.inventory = {}

if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None

def auto_save():
    if st.session_state.inventory:
        pd.DataFrame.from_dict(st.session_state.inventory, orient='index').to_csv('inventory_final.csv', index=True)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. واجهة المستخدم (التنسيق الكامل)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }

    /* القائمة الجانبية - سواد فخم */
    [data-testid="stSidebar"] { background-color: #000000 !important; border-left: 3px solid #27ae60; min-width: 300px !important; }
    .sidebar-user { background-color: #1a1a1a; padding: 25px 10px; border-radius: 15px; margin: 15px 10px; border: 2px solid #27ae60; text-align: center; color: white !important; font-weight: 900; font-size: 24px; }
    
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        background-color: #1a1a1a !important; color: #ffffff !important;
        padding: 15px 20px !important; border-radius: 12px !important;
        margin-bottom: 10px !important; font-size: 18px !important; font-weight: 900 !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #27ae60 !important; border: 1px solid white; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > span:first-child { display: none !important; }

    /* تنسيق نقطة البيع (البطاقات) */
    .item-card {
        background-color: #fcfcfc; border: 2px solid #eee; border-radius: 15px;
        padding: 15px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: 0.3s;
    }
    .item-card:hover { border-color: #27ae60; background-color: #f0fff4; }
    .price-tag { color: #27ae60; font-weight: 900; font-size: 22px; }
    .stock-label { color: #666; font-size: 14px; font-weight: bold; }
    
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول والتنقل
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    with st.sidebar:
        st.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
        menu = st.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"], label_visibility="collapsed")
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 خروج آمن", use_container_width=True): st.session_state.clear(); st.rerun()

    # --- صفحة نقطة البيع المحسنة ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
        
        if st.session_state.show_cust_fields:
            with st.status("✅ تم حفظ الفاتورة!"):
                c_n = st.text_input("اسم الزبون")
                c_p = st.text_input("رقم الهاتف")
                if st.button("💾 حفظ البيانات"):
                    mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                    st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                    auto_save(); st.session_state.show_cust_fields = False; st.rerun()
                if st.button("⏩ تخطي"): st.session_state.show_cust_fields = False; st.rerun()
        else:
            c_p1, c_p2 = st.columns([1, 2])
            with c_p1: p_method = st.selectbox("💳 الدفع", ["تطبيق", "نقداً"])
            with c_p2: search_q = st.text_input("🔍 ابحث عن صنف...")

            bill_items = []
            for cat in st.session_state.categories:
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                if search_q: items = {k: v for k, v in items.items() if search_q in k}
                if items:
                    st.markdown(f"#### 📂 {cat}")
                    cols = st.columns(2)
                    for idx, (item, data) in enumerate(items.items()):
                        with cols[idx % 2]:
                            st.markdown(f"""<div class='item-card'>
                                <div style='display:flex; justify-content:space-between;'>
                                <b>{item}</b> <span class='price-tag'>{format_num(data['بيع'])} ₪</span>
                                </div><div class='stock-label'>المتوفر: {format_num(data['كمية'])}</div>
                            </div>""", unsafe_allow_html=True)
                            mc1, mc2 = st.columns(2)
                            mode = mc1.radio("بـ", ["₪", "كجم"], key=f"m_{item}", horizontal=True)
                            val = clean_num(mc2.text_input("المقدار", key=f"v_{item}", placeholder="0.0"))
                            if val > 0:
                                qty = val if mode == "كجم" else val / data["بيع"]
                                bill_items.append({"item": item, "qty": qty, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * qty})
            
            if bill_items:
                st.divider()
                total = sum(i['amount'] for i in bill_items)
                st.success(f"💰 إجمالي الحساب: {format_num(total)} شيكل")
                if st.button("🚀 إتمام العملية", use_container_width=True, type="primary"):
                    b_id = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save(); st.session_state.show_cust_fields = True; st.rerun()

    # --- باقي الصفحات بنفس منطق الكود الأصلي ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📋 الرصيد", "⚖️ الجرد"])
        with t1: st.dataframe(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية": v['كمية']} for k, v in st.session_state.inventory.items()]), use_container_width=True)
        with t2:
            new_counts = {}
            for item, data in st.session_state.inventory.items():
                c1, c2 = st.columns([3, 2])
                c1.write(f"**{item}** (الحالي: {data['كمية']})")
                res = c2.text_input("الوزن الحقيقي", key=f"j_{item}")
                if res != "": new_counts[item] = clean_num(res)
            if st.button("✔️ حفظ الجرد"):
                for it, rq in new_counts.items():
                    diff = st.session_state.inventory[it]['كمية'] - rq
                    st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': it, 'diff_qty': diff, 'loss_value': diff * st.session_state.inventory[it]['شراء']}])], ignore_index=True)
                    st.session_state.inventory[it]['كمية'] = rq
                auto_save(); st.rerun()

    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 ملخص الأرباح</h1>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        total_sales = st.session_state.sales_df['amount'].sum()
        total_profit = st.session_state.sales_df['profit'].sum()
        c1.metric("إجمالي المبيعات", f"{format_num(total_sales)} ₪")
        c2.metric("صافي الربح", f"{format_num(total_profit)} ₪")

    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إضافة أصناف</h1>", unsafe_allow_html=True)
        with st.form("add"):
            n = st.text_input("الاسم"); cat = st.selectbox("القسم", st.session_state.categories)
            b, s, q = st.columns(3)
            buy = b.text_input("سعر الشراء"); sell = s.text_input("سعر البيع"); qty = q.text_input("الكمية")
            if st.form_submit_button("حفظ"):
                st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(buy), "بيع": clean_num(sell), "كمية": clean_num(qty)}
                auto_save(); st.success("تم الحفظ"); st.rerun()
