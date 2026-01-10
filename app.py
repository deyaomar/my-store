import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

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
        if df is None or df.empty: return pd.DataFrame(columns=columns)
        return df
    except:
        return pd.DataFrame(columns=columns)

def sync_to_google():
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

# 5. إدارة البيانات
if 'inventory' not in st.session_state:
    inv_df = load_sheet_data("Inventory", ['item', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
    st.session_state.sales_df = load_sheet_data("Sales", ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id'])
    st.session_state.expenses_df = load_sheet_data("Expenses", ['date', 'reason', 'amount'])
    st.session_state.waste_df = load_sheet_data("Waste", ['date', 'item', 'qty', 'loss_value'])

# 6. التنسيق (CSS) المتطور للمخزن
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background: #f0f2f5; border-radius: 10px 10px 0 0; padding: 10px 20px; }
    
    /* ستايل بطاقة الصنف في المخزن */
    .stock-card {
        background: white; border-radius: 15px; padding: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #eee;
        transition: 0.3s; margin-bottom: 15px;
    }
    .stock-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
    .status-ok { color: #27ae60; font-weight: bold; }
    .status-low { color: #e74c3c; font-weight: bold; }
    .price-badge { background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 5px; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# 7. نظام الدخول
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
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
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الهاتف")
            if st.button("✅ تأكيد"):
                bid = str(uuid.uuid4())[:8]
                for e in st.session_state.current_bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': c_p, 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                sync_to_google()
                st.session_state.show_customer_form = False; st.rerun()

    # --- 📦 المخزن والجرد (المطور) ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h2 style='color:#1a1a1a;'>📦 إدارة وجرد المخزن</h2>", unsafe_allow_html=True)
        
        # إحصائيات علوية للمخزن
        total_items = len(st.session_state.inventory)
        total_stock_value = sum(v['كمية'] * v['شراء'] for v in st.session_state.inventory.values())
        
        stat1, stat2 = st.columns(2)
        stat1.metric("عدد الأصناف", total_items)
        stat2.metric("إجمالي قيمة البضاعة (بالشراء)", f"{format_num(total_stock_value)} ₪")
        
        st.divider()
        
        t1, t2, t3 = st.tabs(["📋 عرض الرصيد الحالي", "⚖️ جرد المخزن", "🗑️ التالف"])
        
        with t1:
            search_stock = st.text_input("🔍 بحث سريع في المخزن...")
            st.write("### قائمة الأصناف")
            cols = st.columns(3)
            idx = 0
            for item, data in st.session_state.inventory.items():
                if search_stock and search_stock not in item: continue
                
                qty = data['كمية']
                status_class = "status-ok" if qty > 5 else "status-low"
                status_text = "متوفر" if qty > 5 else "كمية منخفضة!"
                
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="stock-card">
                        <div style="display:flex; justify-content:space-between;">
                            <b>{item}</b>
                            <span class="{status_class}">{status_text}</span>
                        </div>
                        <hr style="margin:10px 0;">
                        <div style="font-size:0.9em; color:#666;">
                            📦 الكمية الحالية: <b style="color:#333; font-size:1.2em;">{format_num(qty)}</b><br>
                            💵 سعر الشراء: <span class="price-badge">{data['شراء']} ₪</span><br>
                            💰 سعر البيع: <span class="price-badge">{data['بيع']} ₪</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                idx += 1

        with t2:
            st.warning("⚠️ أدخل الكمية الجديدة لكل صنف لاعتماده في الجرد")
            audit_data = []
            for it, data in st.session_state.inventory.items():
                col_name, col_old, col_new = st.columns([2,1,1])
                col_name.write(f"**{it}**")
                col_old.write(f"الحالي: {format_num(data['كمية'])}")
                new_q = col_new.text_input("الجديد", key=f"audit_val_{it}", placeholder="0.0")
                if new_q: audit_data.append({'item': it, 'qty': clean_num(new_q)})
            
            if audit_data:
                if st.button("💾 حفظ الجرد وتحديث المخزن"):
                    for entry in audit_data:
                        st.session_state.inventory[entry['item']]['كمية'] = entry['qty']
                    if sync_to_google():
                        st.success("✅ تم تحديث المخزن بنجاح")
                        st.rerun()

        with t3:
            st.write("### تسجيل بضاعة تالفة")
            with st.form("waste_form"):
                w_item = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
                w_qty = st.number_input("الكمية التالفة", min_value=0.0, step=0.1)
                submit_w = st.form_submit_button("تسجيل الخسارة")
                if submit_w and w_qty > 0:
                    st.session_state.inventory[w_item]['كمية'] -= w_qty
                    loss = w_qty * st.session_state.inventory[w_item]['شراء']
                    new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'loss_value': loss}
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                    sync_to_google()
                    st.success(f"تم تسجيل تلف {w_item} بخسارة {loss} ₪")
                    st.rerun()

    # --- باقي القوائم تبقى كما هي مع الاحتفاظ بتعديلات التاريخ ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 التحليل المالي</h1>", unsafe_allow_html=True)
        df_s = st.session_state.sales_df.copy()
        df_s['date'] = pd.to_datetime(df_s['date'], errors='coerce')
        df_s = df_s.dropna(subset=['date'])
        
        today = datetime.now().date()
        d_sales = df_s[df_s['date'].dt.date == today]['amount'].sum()
        total_raw_profit = df_s['profit'].sum()
        total_exp = st.session_state.expenses_df['amount'].sum()
        total_waste = st.session_state.waste_df['loss_value'].sum()
        net_profit = total_raw_profit - total_exp - total_waste
        
        c1, c2, c3 = st.columns(3)
        c1.metric("مبيعات اليوم", f"{format_num(d_sales)} ₪")
        c2.metric("صافي الربح", f"{format_num(net_profit)} ₪")
        c3.metric("المصروفات", f"{format_num(total_exp)} ₪")
        st.divider()
        st.write("#### سجل المبيعات")
        st.dataframe(df_s.tail(20), use_container_width=True)

    elif menu == "💸 المصروفات":
        st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("بيان المصروف"); a = st.number_input("المبلغ")
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
                sync_to_google(); st.rerun()
        st.table(st.session_state.expenses_df.tail(10))

    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
        with st.form("add_new"):
            n = st.text_input("اسم الصنف الجديد")
            b = st.text_input("سعر الشراء")
            s = st.text_input("سعر البيع")
            q = st.text_input("الكمية")
            if st.form_submit_button("إضافة للمخزن"):
                st.session_state.inventory[n] = {"شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                sync_to_google(); st.success("تم الحفظ"); st.rerun()
