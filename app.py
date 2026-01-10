import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

# 2. الدوال المساعدة
def format_num(val):
    try:
        val = float(val)
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

def clean_num(text):
    try:
        if text is None or text == "" or pd.isna(text): return 0.0
        cleaned = str(text).replace(',', '').replace('₪', '').strip()
        return float(cleaned)
    except: return 0.0

# 3. الربط مع جداول بيانات جوجل
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet_data(worksheet_name, columns):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df is None or df.empty: return pd.DataFrame(columns=columns)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame(columns=columns)

def sync_to_google():
    try:
        if st.session_state.inventory:
            inv_df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index().rename(columns={'index':'item'})
            conn.update(worksheet="Inventory", data=inv_df)
        conn.update(worksheet="Sales", data=st.session_state.sales_df)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        st.cache_data.clear()
        return True
    except: return False

# 4. إدارة البيانات (التحميل الأولي)
if 'inventory' not in st.session_state:
    inv_df = load_sheet_data("Inventory", ['item', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
    st.session_state.sales_df = load_sheet_data("Sales", ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])
    st.session_state.expenses_df = load_sheet_data("Expenses", ['date', 'reason', 'amount'])
    st.session_state.waste_df = load_sheet_data("Waste", ['date', 'item', 'qty', 'loss_value'])

# 5. التنسيق المطور (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-right: 8px solid #27ae60; padding-right: 15px; margin-bottom: 30px; }
    
    /* ستايل بطاقة الصنف */
    .item-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 10px;
    }
    .item-name { font-weight: 700; font-size: 1.1em; color: #333; }
    .item-price { color: #27ae60; font-weight: 900; font-size: 1.2em; margin: 5px 0; }
    .item-qty { font-size: 0.85em; color: #666; background: #f0f2f6; padding: 2px 8px; border-radius: 10px; }
    
    .report-card { background: #ffffff; padding: 20px; border-radius: 15px; border-right: 5px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom:10px; }
    </style>
    """, unsafe_allow_html=True)

# 6. نظام الدخول
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    with st.sidebar:
        st.markdown(f"<div style='text-align:center; padding:10px; background:#27ae60; color:white; border-radius:10px;'>أهلاً أبو عمر 👋<br>{datetime.now().strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
        menu = st.radio("القائمة الرئيسية", ["🛒 شاشة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
        if st.button("🔄 تحديث شامل من جوجل"):
            st.cache_data.clear()
            for key in ['inventory', 'sales_df', 'expenses_df', 'waste_df']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    # --- 🛒 شاشة البيع الميكانيكية ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
        if 'show_customer_form' not in st.session_state:
            st.session_state.show_customer_form = False
            st.session_state.current_bill_items = []

        if not st.session_state.show_customer_form:
            c1, c2 = st.columns([1, 2])
            p_meth = c1.selectbox("💳 الدفع", ["نقداً", "تطبيق"])
            search_q = c2.text_input("🔍 ابحث عن صنف...")
            
            temp_bill = []
            filtered_items = [(k, v) for k, v in st.session_state.inventory.items() if not search_q or search_q in k]
            
            # عرض الأصناف كشبكة بطاقات
            cols = st.columns(4)
            for idx, (it, data) in enumerate(filtered_items):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div class="item-card">
                        <div class="item-name">{it}</div>
                        <div class="item-price">{data['بيع']} ₪</div>
                        <div class="item-qty">متوفر: {format_num(data['كمية'])}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    mc1, mc2 = st.columns([1, 1.2])
                    mode = mc1.radio("بـ", ["₪", "كجم"], key=f"m_{it}", horizontal=True)
                    val = clean_num(mc2.text_input("المقدار", key=f"v_{it}", placeholder="0.0"))
                    
                    if val > 0:
                        q = val if mode == "كجم" else val / data["بيع"]
                        temp_bill.append({"item": it, "qty": q, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * q, "method": p_meth})
            
            if temp_bill and st.button("🚀 مراجعة الطلب وحفظ البيع", use_container_width=True):
                st.session_state.current_bill_items = temp_bill
                st.session_state.show_customer_form = True; st.rerun()
        else:
            st.subheader("📝 تأكيد العملية")
            c_n = st.text_input("اسم الزبون", value="زبون محل")
            if st.button("✅ تأكيد نهائي"):
                bid = str(uuid.uuid4())[:8]
                date_str = datetime.now().strftime("%Y-%m-%d")
                for e in st.session_state.current_bill_items:
                    if e["item"] in st.session_state.inventory:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': date_str, 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': '', 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                sync_to_google()
                st.session_state.show_customer_form = False; st.rerun()

    # --- 📦 المخزن والجرد (التعديل والجرد) ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة وجرد المخزن</h1>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["📋 كشف المخزن", "✏️ تعديل صنف", "⚠️ تسجيل تالف"])
        
        with t1:
            if st.session_state.inventory:
                df_inv = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index()
                df_inv.columns = ['الصنف', 'شراء', 'بيع', 'الكمية']
                df_inv['إجمالي القيمة'] = df_inv['شراء'] * df_inv['الكمية']
                st.dataframe(df_inv, use_container_width=True)
                st.metric("إجمالي رأس المال في المخزن", f"{format_num(df_inv['إجمالي القيمة'].sum())} ₪")
        
        with t2:
            st.subheader("تعديل بيانات صنف (السعر والكمية)")
            item_to_edit = st.selectbox("اختر الصنف المراد تعديله", list(st.session_state.inventory.keys()))
            col_e1, col_e2, col_e3 = st.columns(3)
            new_b = col_e1.number_input("سعر الشراء الجديد", value=float(st.session_state.inventory[item_to_edit]['شراء']))
            new_s = col_e2.number_input("سعر البيع الجديد", value=float(st.session_state.inventory[item_to_edit]['بيع']))
            new_q = col_e3.number_input("الكمية الفعلية الحالية", value=float(st.session_state.inventory[item_to_edit]['كمية']))
            if st.button("💾 حفظ التعديلات"):
                st.session_state.inventory[item_to_edit] = {"شراء": new_b, "بيع": new_sell if 'new_sell' in locals() else new_s, "كمية": new_q}
                sync_to_google(); st.success(f"تم تحديث {item_to_edit}"); st.rerun()
        
        with t3:
            st.subheader("تسجيل بضاعة تالفة")
            w_item = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()), key="waste_select")
            w_qty = st.number_input("الكمية التالفة", min_value=0.0)
            if st.button("🗑️ تسجيل الخسارة"):
                if w_qty <= st.session_state.inventory[w_item]['كمية']:
                    loss = w_qty * st.session_state.inventory[w_item]['شراء']
                    st.session_state.inventory[w_item]['كمية'] -= w_qty
                    new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'loss_value': loss}
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                    sync_to_google(); st.success("تم تسجيل التالف"); st.rerun()

    # --- 📊 التقارير المالية ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
        # ميزة تصفير الأرباح
        with st.expander("🏁 إقفال الدورة المالية"):
            st.warning("هذا سيمسح سجل المبيعات والمصاريف لتبدأ من جديد.")
            conf = st.text_input("اكتب 'تصفير' للتأكيد")
            if st.button("🚀 تصفير"):
                if conf == "تصفير":
                    st.session_state.sales_df = st.session_state.sales_df.iloc[0:0]
                    st.session_state.expenses_df = st.session_state.expenses_df.iloc[0:0]
                    st.session_state.waste_df = st.session_state.waste_df.iloc[0:0]
                    sync_to_google(); st.rerun()
        
        s_df = st.session_state.sales_df.copy()
        raw_p = pd.to_numeric(s_df['profit']).sum() if not s_df.empty else 0
        ex = pd.to_numeric(st.session_state.expenses_df['amount']).sum() if not st.session_state.expenses_df.empty else 0
        wa = pd.to_numeric(st.session_state.waste_df['loss_value']).sum() if not st.session_state.waste_df.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("أرباح المبيعات", f"{format_num(raw_p)} ₪")
        c2.metric("مصاريف وتالف", f"{format_num(ex + wa)} ₪", delta_color="inverse")
        c3.metric("صافي الربح", f"{format_num(raw_p - ex - wa)} ₪")
        st.write("---")
        st.dataframe(s_df.sort_values(by='date', ascending=False), use_container_width=True)

    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("البيان"); a = st.number_input("المبلغ")
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                sync_to_google(); st.rerun()

    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إضافة صنف جديد</h1>", unsafe_allow_html=True)
        with st.form("add"):
            n = st.text_input("اسم الصنف"); b = st.text_input("شراء"); s = st.text_input("بيع"); q = st.text_input("كمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {"شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                sync_to_google(); st.rerun()
