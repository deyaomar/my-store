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

# 5. التنسيق (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .report-card { background: #ffffff; padding: 20px; border-radius: 15px; border-right: 5px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom:10px; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
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
        menu = st.radio("القائمة الرئيسية", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
        
        if st.button("🔄 تحديث شامل من جوجل"):
            st.cache_data.clear()
            for key in ['inventory', 'sales_df', 'expenses_df', 'waste_df']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    # --- 📊 التقارير المالية ---
    if menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التحليل المالي</h1>", unsafe_allow_html=True)
        
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            with st.expander("🛠️ إدارة الأخطاء (حذف آخر بيع)"):
                if not st.session_state.sales_df.empty:
                    if st.button("🗑️ إلغاء آخر عملية بيع"):
                        last_row = st.session_state.sales_df.iloc[-1]
                        item_name = last_row['item']
                        if item_name in st.session_state.inventory:
                            sell_price = st.session_state.inventory[item_name]['بيع']
                            qty_ret = clean_num(last_row['amount']) / sell_price
                            st.session_state.inventory[item_name]['كمية'] += qty_ret
                        st.session_state.sales_df = st.session_state.sales_df.iloc[:-1]
                        sync_to_google()
                        st.success(f"تم إلغاء مبيعات {item_name}")
                        st.rerun()
        
        with col_ctrl2:
            with st.expander("🏁 إقفال الدورة (تصفير الأرباح)"):
                st.warning("سيتم مسح سجل المبيعات والمصاريف لبدء حساب جديد.")
                confirm = st.text_input("اكتب 'تصفير' للتأكيد")
                if st.button("🚀 تنفيذ الإقفال المالي"):
                    if confirm == "تصفير":
                        st.session_state.sales_df = st.session_state.sales_df.iloc[0:0]
                        st.session_state.expenses_df = st.session_state.expenses_df.iloc[0:0]
                        st.session_state.waste_df = st.session_state.waste_df.iloc[0:0]
                        sync_to_google()
                        st.success("تم تصفير الدورة المالية بنجاح!")
                        st.rerun()

        df_s = st.session_state.sales_df.copy()
        df_s['date_dt'] = pd.to_datetime(df_s['date'], errors='coerce')
        total_raw_profit = pd.to_numeric(df_s['profit'], errors='coerce').sum()
        total_exp = pd.to_numeric(st.session_state.expenses_df['amount'], errors='coerce').sum() if not st.session_state.expenses_df.empty else 0
        total_waste = pd.to_numeric(st.session_state.waste_df['loss_value'], errors='coerce').sum() if not st.session_state.waste_df.empty else 0
        net_profit = total_raw_profit - total_exp - total_waste
        
        st.write("### 💰 ملخص الحسابات الحالي")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='report-card'><h5>إجمالي الأرباح</h5><h2>{format_num(total_raw_profit)} ₪</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h5>مصاريف + تالف</h5><h2 style='color:#e74c3c'>{format_num(total_exp + total_waste)} ₪</h2></div>", unsafe_allow_html=True)
        p_color = "#27ae60" if net_profit >= 0 else "#e74c3c"
        c3.markdown(f"<div class='report-card' style='border-color:{p_color}'><h5>صافي الربح المتاح</h5><h2 style='color:{p_color}'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)
        
        st.divider()
        st.write("### 📈 سجل المبيعات")
        st.dataframe(df_s.sort_values(by='date', ascending=False), use_container_width=True)

    # --- 📦 المخزن والجرد المطور ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📋 عرض المخزن", "✏️ تعديل صنف", "⚠️ تسجيل تالف"])
        
        with tab1:
            if st.session_state.inventory:
                inv_df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index()
                inv_df.columns = ['الصنف', 'سعر الشراء', 'سعر البيع', 'الكمية المتوفرة']
                inv_df['إجمالي القيمة (شراء)'] = inv_df['سعر الشراء'] * inv_df['الكمية المتوفرة']
                st.dataframe(inv_df, use_container_width=True)
                st.info(f"إجمالي رأس المال في المخزن: {format_num(inv_df['إجمالي القيمة (شراء)'].sum())} ₪")
            else:
                st.info("المخزن فارغ حالياً.")

        with tab2:
            st.subheader("تعديل بيانات صنف موجود")
            if st.session_state.inventory:
                edit_item = st.selectbox("اختر الصنف للتعديل", list(st.session_state.inventory.keys()))
                col1, col2, col3 = st.columns(3)
                new_buy = col1.number_input("سعر الشراء الجديد", value=float(st.session_state.inventory[edit_item]['شراء']))
                new_sell = col2.number_input("سعر البيع الجديد", value=float(st.session_state.inventory[edit_item]['بيع']))
                new_qty = col3.number_input("الكمية الحالية", value=float(st.session_state.inventory[edit_item]['كمية']))
                
                if st.button("💾 حفظ التعديلات"):
                    st.session_state.inventory[edit_item] = {"شراء": new_buy, "بيع": new_sell, "كمية": new_qty}
                    sync_to_google()
                    st.success(f"تم تحديث بيانات {edit_item} بنجاح")
                    st.rerun()
            else:
                st.warning("لا توجد أصناف لتعديلها.")

        with tab3:
            st.subheader("تسجيل بضاعة تالفة / مفقودة")
            if st.session_state.inventory:
                waste_item = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
                w_qty = st.number_input("الكمية التالفة", min_value=0.0, step=0.1)
                if st.button("🗑️ تسجيل الخسارة"):
                    if w_qty > 0 and w_qty <= st.session_state.inventory[waste_item]['كمية']:
                        loss = w_qty * st.session_state.inventory[waste_item]['شراء']
                        st.session_state.inventory[waste_item]['كمية'] -= w_qty
                        new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': waste_item, 'qty': w_qty, 'loss_value': loss}
                        st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                        sync_to_google()
                        st.success(f"تم تسجيل تلف {w_qty} من {waste_item}. الخسارة: {loss} ₪")
                        st.rerun()
                    else:
                        st.error("الكمية غير صحيحة أو أكبر من الموجود في المخزن!")

    # --- 🛒 نقطة البيع ---
    elif menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
        if 'show_customer_form' not in st.session_state:
            st.session_state.show_customer_form = False
            st.session_state.current_bill_items = []

        if not st.session_state.show_customer_form:
            c1, c2 = st.columns([1, 2])
            p_meth = c1.selectbox("💳 طريقة الدفع", ["تطبيق", "نقداً"])
            search_q = c2.text_input("🔍 ابحث عن صنف...")
            temp_bill = []
            cols = st.columns(3)
            filtered_items = [(k, v) for k, v in st.session_state.inventory.items() if not search_q or search_q in k]
            
            for idx, (it, data) in enumerate(filtered_items):
                with cols[idx % 3]:
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:10px; border:1px solid #eee; text-align:center;"><b>{it}</b><br><span style="color:#27ae60">{data["بيع"]} ₪</span><br><small>المتوفر: {format_num(data["كمية"])}</small></div>', unsafe_allow_html=True)
                    mc1, mc2 = st.columns(2)
                    mode = mc1.radio("بـ", ["₪", "كجم"], key=f"m_{it}", horizontal=True)
                    val = clean_num(mc2.text_input("المقدار", key=f"v_{it}"))
                    if val > 0:
                        q = val if mode == "كجم" else val / data["بيع"]
                        temp_bill.append({"item": it, "qty": q, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * q, "method": p_meth})
            
            if temp_bill and st.button("🚀 إتمام العملية وحفظ"):
                st.session_state.current_bill_items = temp_bill
                st.session_state.show_customer_form = True; st.rerun()
        else:
            c_n = st.text_input("اسم الزبون", value="زبون محل")
            if st.button("✅ تأكيد البيع"):
                bid = str(uuid.uuid4())[:8]
                date_str = datetime.now().strftime("%Y-%m-%d")
                for e in st.session_state.current_bill_items:
                    if e["item"] in st.session_state.inventory:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': date_str, 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': '', 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                sync_to_google()
                st.session_state.show_customer_form = False; st.rerun()

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
