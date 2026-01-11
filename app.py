import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-right: 8px solid #27ae60; padding-right: 15px; margin-bottom: 25px; }
    
    .stock-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #eee;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        transition: 0.3s;
    }
    .stock-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال المساعدة
def clean_num(text):
    try:
        if text is None or text == "" or pd.isna(text): return 0.0
        return float(str(text).replace(',', '').replace('₪', '').strip())
    except: return 0.0

def format_num(val):
    return f"{val:,.2f}"

# 3. الاتصال بقاعدة البيانات
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_to_google():
    try:
        inv_data = [{'item': k, **v} for k, v in st.session_state.inventory.items()]
        conn.update(worksheet="Inventory", data=pd.DataFrame(inv_data))
        conn.update(worksheet="Sales", data=st.session_state.sales_df)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"خطأ في المزامنة: {e}")
        return False

# 4. تحميل البيانات
if 'inventory' not in st.session_state:
    try:
        inv_df = conn.read(worksheet="Inventory", ttl=0)
        if not inv_df.empty and 'أصلي' not in inv_df.columns: inv_df['أصلي'] = inv_df['كمية']
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        st.session_state.sales_df = conn.read(worksheet="Sales", ttl=0)
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        st.session_state.inventory = {}
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

# قائمة الأقسام المتاحة
CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# 5. القائمة الجانبية
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث البيانات"): st.rerun()

# --- المنطق الرئيسي ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    cat_sel = c1.selectbox("📂 القسم", ["الكل"] + CATEGORIES)
    search = c2.text_input("🔍 ابحث عن صنف لبيعه...")
    items_to_sell = st.session_state.inventory.items()
    if cat_sel != "الكل":
        items_to_sell = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat_sel}.items()
    items = {k: v for k, v in items_to_sell if search.lower() in k.lower()}
    cols = st.columns(4)
    temp_bill = []
    for idx, (it, data) in enumerate(items.items()):
        with cols[idx % 4]:
            st.markdown(f"<div style='background:#fff; border:1px solid #ddd; padding:10px; border-radius:10px; text-align:center;'><b>{it}</b><br><span style='color:green;'>{data['بيع']} ₪</span><br><small>متوفر: {data['كمية']}</small></div>", unsafe_allow_html=True)
            val = st.number_input(f"الكمية ({it})", key=f"v_{it}", min_value=0.0, step=0.1)
            if val > 0:
                temp_bill.append({'item': it, 'qty': val, 'amount': val * data['بيع'], 'profit': (data['بيع'] - data['شراء']) * val})
    if temp_bill and st.button("✅ إتمام البيع وحفظ الفاتورة", use_container_width=True):
        bid = str(uuid.uuid4())[:8]
        for row in temp_bill:
            st.session_state.inventory[row['item']]['كمية'] -= row['qty']
            new_row = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': row['item'], 'amount': row['amount'], 'profit': row['profit'], 'method': 'نقدي', 'customer_name': 'زبون محل', 'bill_id': bid}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
        sync_to_google(); st.success("تمت العملية بنجاح!"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 حالة المخزن والمبيعات</h1>", unsafe_allow_html=True)
    with st.expander("⚠️ تسجيل بضاعة تالفة (فاقد)"):
        with st.form("waste_form"):
            col_w1, col_w2 = st.columns(2)
            w_item = col_w1.selectbox("اختر الصنف التالف", list(st.session_state.inventory.keys()))
            w_qty = col_w2.number_input("الكمية التالفة", min_value=0.0, step=0.1)
            if st.form_submit_button("تسجيل التالف وخصمه من المخزن"):
                if w_qty > 0 and w_qty <= st.session_state.inventory[w_item]['كمية']:
                    st.session_state.inventory[w_item]['كمية'] -= w_qty
                    loss = w_qty * st.session_state.inventory[w_item]['شراء']
                    new_waste = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'loss_value': loss}
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_waste])], ignore_index=True)
                    sync_to_google(); st.success(f"تم تسجيل {w_qty} من {w_item} كتالف"); st.rerun()
                else: st.error("الكمية غير كافية!")

    st.markdown("---")
    if st.session_state.inventory:
        stock_value = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())
        st.markdown(f"<div class='report-card'><h5>إجمالي قيمة البضاعة الحالية (رأس المال)</h5><h2>{format_num(stock_value)} ₪</h2></div><br>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        f_cat = c1.selectbox("📂 تصفية حسب القسم", ["الكل"] + CATEGORIES)
        search_st = c2.text_input("🔍 ابحث في الأصناف...")
        cols = st.columns(3); display_idx = 0
        for it, data in st.session_state.inventory.items():
            item_cat = data.get('قسم', 'أخرى')
            if (f_cat == "الكل" or item_cat == f_cat) and (search_st.lower() in it.lower()):
                orig = data.get('أصلي', data['كمية']); sold = orig - data['كمية']
                with cols[display_idx % 3]:
                    card_color = "#27ae60" if data['كمية'] > 5 else ("#f39c12" if data['كمية'] > 0 else "#e74c3c")
                    st.markdown(f"<div class='stock-card' style='border-top: 6px solid {card_color};'><small>{item_cat}</small><h3>{it}</h3><p>المباع: {sold} | المتبقي: {data['كمية']}</p><h4>{data['بيع']} ₪</h4></div>", unsafe_allow_html=True)
                    with st.expander(f"⚙️ جرد {it}"):
                        new_q = st.number_input("الكمية الفعلية", value=float(data['كمية']), key=f"inv_q_{it}")
                        if st.button("تحديث", key=f"inv_btn_{it}"):
                            st.session_state.inventory[it]['كمية'] = new_q; st.session_state.inventory[it]['أصلي'] = new_q
                            sync_to_google(); st.rerun()
                display_idx += 1
    else: st.info("المخزن فارغ.")

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 لوحة التحكم والأداء المالي الشامل</h1>", unsafe_allow_html=True)
    
    if not st.session_state.sales_df.empty:
        # 1. تجهيز البيانات بدقة
        df_sales = st.session_state.sales_df.copy()
        df_sales['date'] = pd.to_datetime(df_sales['date'])
        df_sales['amount'] = pd.to_numeric(df_sales['amount'], errors='coerce').fillna(0)
        df_sales['profit'] = pd.to_numeric(df_sales['profit'], errors='coerce').fillna(0)
        
        df_exp = st.session_state.expenses_df.copy()
        if not df_exp.empty:
            df_exp['date'] = pd.to_datetime(df_exp['date'])
            df_exp['amount'] = pd.to_numeric(df_exp['amount'], errors='coerce').fillna(0)
            
        df_waste = st.session_state.waste_df.copy()
        if not df_waste.empty:
            df_waste['date'] = pd.to_datetime(df_waste['date'])
            df_waste['loss_value'] = pd.to_numeric(df_waste['loss_value'], errors='coerce').fillna(0)

        today = pd.Timestamp(datetime.now().date())
        last_7_days = today - pd.Timedelta(days=7)
        
        # حسابات الأرقام
        w_sales = df_sales[df_sales['date'] >= last_7_days]['amount'].sum()
        w_gross_profit = df_sales[df_sales['date'] >= last_7_days]['profit'].sum()
        w_exp = df_exp[df_exp['date'] >= last_7_days]['amount'].sum() if not df_exp.empty else 0
        w_waste = df_waste[df_waste['date'] >= last_7_days]['loss_value'].sum() if not df_waste.empty else 0
        w_net_profit = w_gross_profit - w_exp - w_waste

        # --- الصف الأول: بطاقات الأداء الخمسة (التصميم الملون الجديد) ---
        st.subheader(f"📅 ملخص الأداء (آخر 7 أيام)")
        
        # تعديل العمدان لـ 5 بطاقات
        c1, c2, c3, c4, c5 = st.columns(5)
        
        with c1:
            st.markdown(f"""<div style='background: linear-gradient(135deg, #27ae60, #2ecc71); padding: 15px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); min-height: 120px;'>
                <p style='margin:0; font-size:14px;'>إجمالي المبيعات</p><h2 style='margin:10px 0;'>{format_num(w_sales)} ₪</h2></div>""", unsafe_allow_html=True)
        
        with c2:
            st.markdown(f"""<div style='background: linear-gradient(135deg, #2980b9, #3498db); padding: 15px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); min-height: 120px;'>
                <p style='margin:0; font-size:14px;'>أرباح البضاعة</p><h2 style='margin:10px 0;'>{format_num(w_gross_profit)} ₪</h2></div>""", unsafe_allow_html=True)

        with c3:
            st.markdown(f"""<div style='background: linear-gradient(135deg, #e67e22, #f39c12); padding: 15px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); min-height: 120px;'>
                <p style='margin:0; font-size:14px;'>إجمالي المصاريف</p><h2 style='margin:10px 0;'>{format_num(w_exp)} ₪</h2></div>""", unsafe_allow_html=True)

        with c4:
            # بطاقة التالف بلون مميز (أحمر غامق)
            st.markdown(f"""<div style='background: linear-gradient(135deg, #c0392b, #e74c3c); padding: 15px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); min-height: 120px;'>
                <p style='margin:0; font-size:14px;'>خسائر التالف</p><h2 style='margin:10px 0;'>{format_num(w_waste)} ₪</h2></div>""", unsafe_allow_html=True)

        with c5:
            # بطاقة الصافي بلون بنفسجي
            st.markdown(f"""<div style='background: linear-gradient(135deg, #8e44ad, #9b59b6); padding: 15px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); min-height: 120px;'>
                <p style='margin:0; font-size:14px;'>الربح الصافي</p><h2 style='margin:10px 0;'>{format_num(w_net_profit)} ₪</h2><small>بعد كل الخصومات</small></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- الصف الثاني: البحث المتقدم ---
        with st.expander("🔍 استعلام وبحث متقدم في الأرشيف", expanded=False):
            c_a, c_b = st.columns(2)
            d_from = c_a.date_input("من تاريخ", value=last_7_days)
            d_to = c_b.date_input("إلى تاريخ", value=today)
            mask = (df_sales['date'] >= pd.Timestamp(d_from)) & (df_sales['date'] <= pd.Timestamp(d_to))
            f_df = df_sales.loc[mask].sort_values(by='date', ascending=False)
            if not f_df.empty:
                st.dataframe(f_df, use_container_width=True)

        # --- الصف الثالث: الجداول التفصيلية ---
        col_tab1, col_tab2 = st.columns(2)
        
        with col_tab1:
            st.markdown("### 📅 الأرشيف اليومي (آخر 7 أيام)")
            daily_summary = df_sales[df_sales['date'] >= last_7_days].groupby(df_sales['date'].dt.date).agg({'amount': 'sum', 'profit': 'sum'}).reset_index()
            days_ara = {"Monday":"الاثنين", "Tuesday":"الثلاثاء", "Wednesday":"الأربعاء", "Thursday":"الخميس", "Friday":"الجمعة", "Saturday":"السبت", "Sunday":"الأحد"}
            daily_summary['اليوم'] = pd.to_datetime(daily_summary['date']).dt.day_name().map(days_ara)
            st.table(daily_summary[['اليوم', 'date', 'amount', 'profit']].sort_values(by='date', ascending=False))

        with col_tab2:
            st.markdown("### ⚠️ تفاصيل البضاعة التالفة")
            if not df_waste.empty:
                w_display = df_waste[df_waste['date'] >= last_7_days].sort_values(by='date', ascending=False)
                if not w_display.empty:
                    st.dataframe(w_display[['date', 'item', 'qty', 'loss_value']], use_container_width=True)
                else: st.info("لا يوجد تالف مسجل في هذه الفترة.")
            else: st.info("سجل التالف فارغ.")

        # الرسم البياني
        st.markdown("### 📈 حركة المبيعات الأسبوعية")
        st.line_chart(daily_summary.set_index('date')['amount'])

    else:
        st.info("لا توجد بيانات مبيعات مسجلة حالياً.")

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>", unsafe_allow_html=True)
    total_exp = pd.to_numeric(st.session_state.expenses_df['amount'], errors='coerce').sum()
    st.markdown(f"<div class='report-card'><h5>إجمالي المصروفات</h5><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)
    with st.form("exp_form"):
        r = st.text_input("البيان"); a = st.number_input("المبلغ (₪)", min_value=0.0)
        if st.form_submit_button("حفظ"):
            if r and a > 0:
                new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                sync_to_google(); st.rerun()

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إدارة البضاعة والمشتريات</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📥 تزويد كمية", "✨ صنف جديد"])
    with t1:
        if st.session_state.inventory:
            with st.form("add_stock_form"):
                item_name = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
                plus_q = st.number_input("الكمية المضافة", min_value=0.0)
                if st.form_submit_button("إضافة"):
                    st.session_state.inventory[item_name]['كمية'] += plus_q
                    st.session_state.inventory[item_name]['أصلي'] = st.session_state.inventory[item_name]['كمية']
                    sync_to_google(); st.rerun()
    with t2:
        with st.form("add_form"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", CATEGORIES)
            b = st.number_input("سعر الشراء")
            s = st.number_input("سعر البيع")
            q = st.number_input("الكمية")
            if st.form_submit_button("إضافة صنف جديد"):
                if n:
                    st.session_state.inventory[n] = {'قسم': cat, 'شراء': b, 'بيع': s, 'كمية': q, 'أصلي': q}
                    sync_to_google(); st.success(f"تمت إضافة {n}!"); st.rerun()
