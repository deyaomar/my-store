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
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .stock-card { background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 20px; transition: 0.3s; }
    .stock-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال المساعدة
def format_num(val):
    return f"{val:,.2f}"

# 3. الاتصال والمزامنة
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
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        st.session_state.sales_df = conn.read(worksheet="Sales", ttl=0)
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        st.session_state.inventory = {}
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# 5. القائمة الجانبية
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث البيانات"): st.rerun()

# --- المنطق الرئيسي ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    cat_sel = c1.selectbox("📂 القسم", ["الكل"] + st.session_state.CATEGORIES)
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
                profit_unit = data['بيع'] - data['شراء']
                if profit_unit < 0:
                    st.error(f"⚠️ خطأ في سعر {it}")
                temp_bill.append({'item': it, 'qty': val, 'amount': val * data['بيع'], 'profit': profit_unit * val})
    
    if temp_bill and st.button("✅ إتمام البيع وحفظ الفاتورة", use_container_width=True):
        bid = str(uuid.uuid4())[:8]
        for row in temp_bill:
            st.session_state.inventory[row['item']]['كمية'] -= row['qty']
            new_row = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': row['item'], 'amount': row['amount'], 'profit': row['profit'], 'method': 'نقدي', 'customer_name': 'زبون محل', 'bill_id': bid}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
        sync_to_google(); st.success("تمت العملية بنجاح!"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 حالة المخزن والجرد</h1>", unsafe_allow_html=True)
    
    # تسجيل التوالف
    with st.expander("⚠️ تسجيل بضاعة تالفة (فاقد)"):
        with st.form("waste_form"):
            col_w1, col_w2 = st.columns(2)
            w_item = col_w1.selectbox("اختر الصنف التالف", list(st.session_state.inventory.keys()))
            w_qty = col_w2.number_input("الكمية التالفة", min_value=0.0, step=0.1)
            if st.form_submit_button("تسجيل التالف وخصمه"):
                if w_qty > 0 and w_qty <= st.session_state.inventory[w_item]['كمية']:
                    st.session_state.inventory[w_item]['كمية'] -= w_qty
                    loss = w_qty * st.session_state.inventory[w_item]['شراء']
                    new_waste = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'loss_value': loss}
                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_waste])], ignore_index=True)
                    sync_to_google(); st.success(f"تم تسجيل التالف"); st.rerun()
                else: st.error("الكمية غير كافية!")

    # عرض حالة المخزن
    if st.session_state.inventory:
        stock_value = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())
        st.markdown(f"<div class='report-card'><h5>إجمالي قيمة رأس المال في البضاعة</h5><h2>{format_num(stock_value)} ₪</h2></div><br>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        f_cat = c1.selectbox("📂 تصفية حسب القسم", ["الكل"] + st.session_state.CATEGORIES)
        search_st = c2.text_input("🔍 ابحث في الأصناف...")
        
        cols = st.columns(3); display_idx = 0
        for it, data in st.session_state.inventory.items():
            item_cat = data.get('قسم', 'أخرى')
            if (f_cat == "الكل" or item_cat == f_cat) and (search_st.lower() in it.lower()):
                with cols[display_idx % 3]:
                    card_color = "#27ae60" if data['كمية'] > 5 else ("#f39c12" if data['كمية'] > 0 else "#e74c3c")
                    st.markdown(f"<div class='stock-card' style='border-top: 6px solid {card_color};'><small>{item_cat}</small><h3>{it}</h3><p>المتبقي: {data['كمية']}</p><h4>بيع: {data['بيع']} ₪</h4></div>", unsafe_allow_html=True)
                    with st.expander(f"⚙️ جرد/تعديل {it}"):
                        new_q = st.number_input("الكمية الفعلية", value=float(data['كمية']), key=f"inv_q_{it}")
                        if st.button("تحديث", key=f"inv_btn_{it}"):
                            st.session_state.inventory[it]['كمية'] = new_q
                            sync_to_google(); st.rerun()
                display_idx += 1
# كود عرض جدول مراجعة الأسعار والكميات - لأبو عمر
st.subheader("📋 كشف مراجعة الأصناف (الأسعار والكميات)")

if st.session_state.inventory:
    # تحويل بيانات المخزن إلى جدول (DataFrame) لسهولة العرض
    inventory_review_df = [{'الصنف': k, 
                            'القسم': v.get('قسم', 'غير مصنف'), 
                            'سعر الشراء (₪)': v['شراء'], 
                            'سعر البيع (₪)': v['بيع'], 
                            'الكمية المتوفرة': v['كمية'],
                            'الحالة': '✅ سليم' if v['بيع'] > v['شراء'] else '❌ خطأ (البيع أقل من الشراء)'} 
                           for k, v in st.session_state.inventory.items()]
    
    df_review = pd.DataFrame(inventory_review_df)

    # عرض الجدول مع تنسيق الألوان لتنبيهك للأخطاء
    def color_errors(val):
        color = '#ffcccc' if '❌' in str(val) else ''
        return f'background-color: {color}'

    st.dataframe(
        df_review.style.applymap(color_errors, subset=['الحالة']),
        use_container_width=True,
        hide_index=True
    )

    # إضافة زر لتصدير هذه القائمة إذا احتجت
    st.info("💡 نصيحة: أي صنف حالته '❌ خطأ' يعني أنك سجلت سعر الشراء أعلى من البيع، وهذا هو سبب ظهور الأرباح بالسالب.")
else:
    st.warning("لا توجد أصناف في المخزن حالياً.")

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقرير المالي الدقيق - أبو عمر</h1>", unsafe_allow_html=True)
    today_dt = datetime.now().date()

    def get_safe_sum(df, date_col, value_col):
        if df is None or df.empty: return 0.0
        try:
            temp = df.copy()
            temp[date_col] = pd.to_datetime(temp[date_col], errors='coerce').dt.date
            today_data = temp[temp[date_col] == today_dt]
            if not today_data.empty and value_col in today_data.columns:
                return pd.to_numeric(today_data[value_col], errors='coerce').fillna(0).sum()
            return 0.0
        except: return 0.0

    t_sales = get_safe_sum(st.session_state.sales_df, 'date', 'amount')
    t_gross_profit = get_safe_sum(st.session_state.sales_df, 'date', 'profit')
    t_exp = get_safe_sum(st.session_state.expenses_df, 'date', 'amount')
    t_waste = get_safe_sum(st.session_state.waste_df, 'date', 'loss_value')
    net_profit = t_gross_profit - t_exp - t_waste

    st.markdown(f"### 🕒 تقرير اليوم: {today_dt}")
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='report-card'><h5>مبيعات اليوم</h5><h2 style='color:#27ae60;'>{format_num(t_sales)} ₪</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='report-card' style='border-top-color: #e67e22;'><h5>مصاريف وتوالف اليوم</h5><h2 style='color:#e67e22;'>{format_num(t_exp + t_waste)} ₪</h2></div>", unsafe_allow_html=True)
    color = "#27ae60" if net_profit >= 0 else "#e74c3c"
    col3.markdown(f"<div class='report-card' style='border-top-color: {color};'><h5>صافي ربح اليوم</h5><h2 style='color:{color};'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)

    st.divider()
    if not st.session_state.sales_df.empty:
        st.subheader("📄 عمليات اليوم")
        temp_sales = st.session_state.sales_df.copy()
        temp_sales['date'] = pd.to_datetime(temp_sales['date'], errors='coerce').dt.date
        today_sales = temp_sales[temp_sales['date'] == today_dt]
        st.dataframe(today_sales, use_container_width=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_form"):
        r = st.text_input("البيان")
        a = st.number_input("المبلغ (₪)", min_value=0.0)
        if st.form_submit_button("حفظ المصروف"):
            if r and a > 0:
                new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                sync_to_google(); st.rerun()

    st.subheader("سجل المصروفات")
    if not st.session_state.expenses_df.empty:
        for idx, row in st.session_state.expenses_df.iterrows():
            colx, coly, colz = st.columns([3, 2, 1])
            colx.write(f"📌 {row['reason']}")
            coly.write(f"💰 {row['amount']} ₪")
            if colz.button("حذف", key=f"del_exp_{idx}"):
                st.session_state.expenses_df = st.session_state.expenses_df.drop(idx)
                sync_to_google(); st.rerun()

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف والأقسام</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📥 تزويد كمية", "✨ صنف جديد", "📂 إدارة الأقسام"])
    
    with t1:
        if st.session_state.inventory:
            with st.form("add_stock_form"):
                item_name = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
                plus_q = st.number_input("الكمية المضافة", min_value=0.0)
                if st.form_submit_button("إضافة للمخزن"):
                    st.session_state.inventory[item_name]['كمية'] += plus_q
                    sync_to_google(); st.success("تم التحديث"); st.rerun()

    with t2:
        with st.form("add_form"):
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.CATEGORIES)
            b = st.number_input("سعر الشراء")
            s = st.number_input("سعر البيع")
            q = st.number_input("الكمية الأولية")
            if st.form_submit_button("إضافة صنف جديد"):
                if n:
                    st.session_state.inventory[n] = {'قسم': cat, 'شراء': b, 'بيع': s, 'كمية': q}
                    sync_to_google(); st.success(f"تمت إضافة {n}"); st.rerun()

    with t3:
        new_cat = st.text_input("اسم القسم الجديد")
        if st.button("حفظ القسم"):
            if new_cat and new_cat not in st.session_state.CATEGORIES:
                st.session_state.CATEGORIES.append(new_cat); st.rerun()
        st.write("الأقسام الحالية:", st.session_state.CATEGORIES)
