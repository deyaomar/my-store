import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📊")

# 2. تهيئة نظام الطوارئ
if 'offline_queue_count' not in st.session_state:
    st.session_state.offline_queue_count = 0

# 3. الدوال المساعدة
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

# 4. الربط مع جداول بيانات جوجل
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet_data(worksheet_name, columns):
    try:
        df = conn.read(worksheet=worksheet_name, ttl="0")
        if df.empty: return pd.DataFrame(columns=columns)
        return df
    except:
        return pd.DataFrame(columns=columns)

def sync_to_google():
    """رفع كل البيانات المعدلة إلى جوجل"""
    try:
        if st.session_state.inventory:
            inv_df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index().rename(columns={'index':'item'})
            conn.update(worksheet="Inventory", data=inv_df)
        
        conn.update(worksheet="Sales", data=st.session_state.sales_df)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        
        st.session_state.offline_queue_count = 0
        return True
    except:
        st.session_state.offline_queue_count += 1
        return False

# 5. إدارة البيانات وتحميلها عند البداية
if 'inventory' not in st.session_state:
    inv_df = load_sheet_data("Inventory", ['item', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
    st.session_state.sales_df = load_sheet_data("Sales", ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])
    st.session_state.expenses_df = load_sheet_data("Expenses", ['date', 'reason', 'amount'])
    st.session_state.waste_df = load_sheet_data("Waste", ['date', 'item', 'qty', 'loss_value'])

# 6. التنسيق (CSS) لجمالية الواجهة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .report-card { background: #ffffff; padding: 20px; border-radius: 15px; border-right: 5px solid #27ae60; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
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
    # شريط تنبيه الطوارئ والمزامنة
    if st.session_state.offline_queue_count > 0:
        st.warning(f"⚠️ يوجد {st.session_state.offline_queue_count} عمليات معلقة لم ترفع لجوجل")
        if st.button("🔄 مزامنة البيانات المعلقة الآن"):
            if sync_to_google(): st.success("✅ تمت المزامنة!"); st.rerun()

    with st.sidebar:
        st.markdown(f"<div style='text-align:center; padding:10px; background:#27ae60; color:white; border-radius:10px;'>أهلاً أبو عمر 👋<br>{datetime.now().strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
        menu = st.radio("القائمة الرئيسية", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
        if st.button("🚪 تسجيل خروج", use_container_width=True): st.session_state.logged_in = False; st.rerun()

    # --- 🛒 نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
        if 'show_customer_form' not in st.session_state:
            st.session_state.show_customer_form = False
            st.session_state.current_bill_items = []

        if not st.session_state.show_customer_form:
            c1, c2 = st.columns([1, 2])
            p_meth = c1.selectbox("💳 طريقة الدفع", ["نقداً", "تطبيق"])
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
            c_n = st.text_input("اسم الزبون (اختياري)")
            c_p = st.text_input("رقم الهاتف")
            if st.button("✅ تأكيد"):
                bid = str(uuid.uuid4())[:8]
                for e in st.session_state.current_bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': c_p, 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                sync_to_google()
                st.session_state.show_customer_form = False; st.rerun()

    # --- 📊 التقارير المالية (المطورة) ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التحليل المالي الشامل</h1>", unsafe_allow_html=True)
        
        # معالجة بيانات الوقت
        df_s = st.session_state.sales_df.copy()
        df_s['date'] = pd.to_datetime(df_s['date'])
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # الحسابات
        d_sales = df_s[df_s['date'].dt.date == today]['amount'].sum()
        w_sales = df_s[df_s['date'].dt.date >= week_ago]['amount'].sum()
        m_sales = df_s[df_s['date'].dt.date >= month_ago]['amount'].sum()
        
        total_raw_profit = df_s['profit'].sum()
        total_exp = st.session_state.expenses_df['amount'].sum()
        total_waste = st.session_state.waste_df['loss_value'].sum()
        net_profit = total_raw_profit - total_exp - total_waste
        
        stock_val = sum(v['كمية'] * v['شراء'] for v in st.session_state.inventory.values())

        # العرض العلوي
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='report-card'><h5>💰 مبيعات اليوم</h5><h2>{format_num(d_sales)} ₪</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h5>📅 مبيعات الأسبوع</h5><h2>{format_num(w_sales)} ₪</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h5>🏗️ قيمة المخزن</h5><h2>{format_num(stock_val)} ₪</h2></div>", unsafe_allow_html=True)
        
        p_color = "#27ae60" if net_profit >= 0 else "#e74c3c"
        c4.markdown(f"<div class='report-card' style='border-color:{p_color}'><h5>💵 صافي الربح</h5><h2 style='color:{p_color}'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)

        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("📉 تفاصيل الخصومات")
            st.write(f"**إجمالي المصروفات:** {format_num(total_exp)} ₪")
            st.write(f"**إجمالي التالف:** {format_num(total_waste)} ₪")
            st.bar_chart({"المصروفات": total_exp, "التالف": total_waste})
        
        with col_right:
            st.subheader("📋 سجل آخر 10 مبيعات")
            st.dataframe(st.session_state.sales_df.tail(10), use_container_width=True)

    # --- 📦 المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["📋 الرصيد الحالي", "⚖️ الجرد", "🗑️ التالف"])
        with t1:
            st.dataframe(pd.DataFrame.from_dict(st.session_state.inventory, orient='index'), use_container_width=True)
        with t2:
            audit_list = []
            for it, data in st.session_state.inventory.items():
                c1, c2 = st.columns([3, 1])
                new_q = c2.text_input(f"كمية {it}", key=f"aud_{it}")
                if new_q: audit_list.append({'it': it, 'q': clean_num(new_q)})
            if audit_list and st.button("💾 اعتماد الجرد الجديد"):
                for r in audit_list: st.session_state.inventory[r['it']]['كمية'] = r['q']
                sync_to_google(); st.rerun()
        with t3:
            with st.form("waste"):
                w_it = st.selectbox("الصنف التالف", list(st.session_state.inventory.keys()))
                w_q = st.number_input("الكمية")
                if st.form_submit_button("تسجيل التالف"):
                    st.session_state.inventory[w_it]['كمية'] -= w_q
                    loss = w_q * st.session_state.inventory[w_it]['شراء']
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_it, 'qty': w_q, 'loss_value': loss}])], ignore_index=True)
                    sync_to_google(); st.rerun()

    # --- 💸 المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("بيان المصروف"); a = st.number_input("المبلغ")
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                sync_to_google(); st.rerun()
        st.table(st.session_state.expenses_df.tail(10))

    # --- ⚙️ الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إضافة أصناف جديدة</h1>", unsafe_allow_html=True)
        with st.form("add_new"):
            n = st.text_input("اسم الصنف")
            b = st.text_input("سعر الشراء")
            s = st.text_input("سعر البيع")
            q = st.text_input("الكمية الأولية")
            if st.form_submit_button("حفظ الصنف"):
                st.session_state.inventory[n] = {"شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                sync_to_google(); st.success("تمت الإضافة بنجاح"); st.rerun()
