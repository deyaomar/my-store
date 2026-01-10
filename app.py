import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import random
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

# 2. تهيئة نظام الطوارئ
if 'offline_queue_count' not in st.session_state:
    st.session_state.offline_queue_count = 0

# 3. الدوال المساعدة
def format_num(val):
    try:
        val = float(val)
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

def clean_num(text):
    try:
        if text is None or text == "" or pd.isna(text): return 0.0
        # تنظيف الأرقام من الفواصل أو الرموز
        cleaned = str(text).replace(',', '').replace('₪', '').strip()
        return float(cleaned)
    except: return 0.0

# 4. الربط مع جداول بيانات جوجل
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet_data(worksheet_name, columns):
    try:
        # استخدام ttl=0 لضمان جلب بيانات حية دائماً
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df is None or df.empty: 
            return pd.DataFrame(columns=columns)
        # تنظيف أسماء الأعمدة من أي فراغات مخفية
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame(columns=columns)

def sync_to_google():
    try:
        if st.session_state.inventory:
            inv_df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index().rename(columns={'index':'item'})
            conn.update(worksheet="Inventory", data=inv_df)
        conn.update(worksheet="Sales", data=st.session_state.sales_df)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        # مسح الكاش لضمان القراءة الحية في الخطوة القادمة
        st.cache_data.clear()
        st.session_state.offline_queue_count = 0
        return True
    except:
        st.session_state.offline_queue_count += 1
        return False

# 5. إدارة البيانات (التحميل الأولي)
if 'inventory' not in st.session_state:
    inv_df = load_sheet_data("Inventory", ['item', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
    st.session_state.sales_df = load_sheet_data("Sales", ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])
    st.session_state.expenses_df = load_sheet_data("Expenses", ['date', 'reason', 'amount'])
    st.session_state.waste_df = load_sheet_data("Waste", ['date', 'item', 'qty', 'loss_value'])

# 6. التنسيق (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .report-card { background: #ffffff; padding: 20px; border-radius: 15px; border-right: 5px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom:10px; }
    .stock-card { background: white; border-radius: 15px; padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #eee; margin-bottom: 15px; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-bottom: 5px solid #27ae60; padding-bottom: 5px; margin-bottom: 30px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# 7. نظام الدخول
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

        if st.button("🚪 تسجيل خروج", use_container_width=True): st.session_state.logged_in = False; st.rerun()

    # --- 🛒 نقطة البيع ---
    if menu == "🛒 نقطة البيع":
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
                    st.markdown(f'<div style="background:white; padding:10px; border-radius:10px; border:1px solid #eee; text-align:center;"><b>{it}</b><br><span style="color:#27ae60">{data["بيع"]} ₪</span></div>', unsafe_allow_html=True)
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
            c_p = st.text_input("رقم الهاتف", value="")
            if st.button("✅ تأكيد البيع"):
                bid = str(uuid.uuid4())[:8]
                date_str = datetime.now().strftime("%Y-%m-%d")
                for e in st.session_state.current_bill_items:
                    if e["item"] in st.session_state.inventory:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': date_str, 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': c_p, 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                sync_to_google()
                st.session_state.show_customer_form = False; st.rerun()

    # --- 📊 التقارير المالية (تم الإصلاح للعرض الفوري) ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التحليل المالي الشامل</h1>", unsafe_allow_html=True)
        
        if st.button("🔄 تحديث التقارير الآن"):
            st.cache_data.clear()
            st.rerun()

        with st.spinner('جاري مزامنة المبيعات...'):
            df_s = load_sheet_data("Sales", ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])
        
        if not df_s.empty:
            # معالجة الأرقام
            df_s['amount'] = pd.to_numeric(df_s['amount'], errors='coerce').fillna(0)
            df_s['profit'] = pd.to_numeric(df_s['profit'], errors='coerce').fillna(0)
            
            # معالجة التاريخ (تحويل ذكي)
            df_s['date_dt'] = pd.to_datetime(df_s['date'], errors='coerce')
            
            # الفلترة لليوم
            today_str = datetime.now().strftime("%Y-%m-%d")
            # الحسابات
            d_sales = df_s[df_s['date'].astype(str).str.contains(today_str)]['amount'].sum()
            total_raw_profit = df_s['profit'].sum()
            
            exp_df = load_sheet_data("Expenses", ['date', 'reason', 'amount'])
            total_exp = pd.to_numeric(exp_df['amount'], errors='coerce').sum() if not exp_df.empty else 0
            
            net_profit = total_raw_profit - total_exp
            stock_val = sum(v['كمية'] * v['شراء'] for v in st.session_state.inventory.values())

            # عرض الكروت
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='report-card'><h5>💰 مبيعات اليوم</h5><h2>{format_num(d_sales)} ₪</h2></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='report-card'><h5>💸 المصروفات</h5><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='report-card'><h5>🏗️ قيمة المخزن</h5><h2>{format_num(stock_val)} ₪</h2></div>", unsafe_allow_html=True)
            
            p_color = "#27ae60" if net_profit >= 0 else "#e74c3c"
            c4.markdown(f"<div class='report-card' style='border-color:{p_color}'><h5>💵 صافي الربح</h5><h2 style='color:{p_color}'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)

            st.divider()
            st.write("### 📈 آخر العمليات المسجلة في جوجل شيت")
            st.dataframe(df_s.tail(15), use_container_width=True)
        else:
            st.warning("لم يتم العثور على مبيعات بعد.")

    # --- 📦 المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h2 class='main-title'>📦 إدارة المخزن</h2>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["📋 الرصيد", "⚖️ الجرد", "🗑️ التالف"])
        with t1:
            cols = st.columns(3)
            for idx, (item, data) in enumerate(st.session_state.inventory.items()):
                with cols[idx % 3]:
                    color = "#27ae60" if data['كمية'] > 5 else "#e74c3c"
                    st.markdown(f"""<div class='stock-card'><b>{item}</b><br>الكمية: <span style='color:{color}'>{format_num(data['كمية'])}</span><br><small>شراء: {data['شراء']} | بيع: {data['بيع']}</small></div>""", unsafe_allow_html=True)
        with t2:
            audit_data = []
            for it, data in st.session_state.inventory.items():
                c1, c2 = st.columns([2,1])
                new_q = c2.text_input(f"تعديل {it}", key=f"aud_{it}", placeholder=str(data['كمية']))
                if new_q: audit_data.append({'item': it, 'qty': clean_num(new_q)})
            if audit_data and st.button("💾 حفظ تعديلات الجرد"):
                for entry in audit_data: st.session_state.inventory[entry['item']]['كمية'] = entry['qty']
                sync_to_google(); st.rerun()
        with t3:
            with st.form("waste_form"):
                w_it = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
                w_q = st.number_input("الكمية التالفة", step=0.1)
                if st.form_submit_button("تسجيل تالف"):
                    st.session_state.inventory[w_it]['كمية'] -= w_q
                    loss = w_q * st.session_state.inventory[w_it]['شراء']
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_it, 'qty': w_q, 'loss_value': loss}])], ignore_index=True)
                    sync_to_google(); st.rerun()

    # --- 💸 المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp_form"):
            r = st.text_input("بيان المصروف")
            a = st.number_input("المبلغ ₪", min_value=0.0)
            if st.form_submit_button("حفظ المصروف"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                sync_to_google(); st.rerun()
        st.table(st.session_state.expenses_df.tail(10))

    # --- ⚙️ الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إضافة صنف جديد</h1>", unsafe_allow_html=True)
        with st.form("add_item_form"):
            n = st.text_input("اسم الصنف")
            b = st.text_input("سعر الشراء")
            s = st.text_input("سعر البيع")
            q = st.text_input("الكمية الأولية")
            if st.form_submit_button("إضافة للمخزن"):
                st.session_state.inventory[n] = {"شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                sync_to_google(); st.rerun()
