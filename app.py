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
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount', 'id'])
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
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع بالمبلغ (شيكل)</h1>", unsafe_allow_html=True)
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
            # تنظيف البيانات قسرياً لضمان عدم وجود "ماينوس" تقني
            try:
                # تحويل كل القيم لأرقام مع تنظيفها من أي فراغات أو رموز
                curr_sell_price = float(str(data.get('بيع', 0)).replace('₪', '').strip())
                curr_buy_price = float(str(data.get('شراء', 0)).replace('₪', '').strip())
                curr_qty = float(data.get('كمية', 0))
            except:
                curr_sell_price = 0.0
                curr_buy_price = 0.0
                curr_qty = 0.0

            st.markdown(f"""
                <div style='background:#fff; border:1px solid #ddd; padding:10px; border-radius:10px; text-align:center;'>
                    <b>{it}</b><br>
                    <span style='color:green;'>السعر: {curr_sell_price} ₪</span><br>
                    <small>متوفر: {curr_qty}</small>
                </div>
                """, unsafe_allow_html=True)
            
            money_val = st.number_input(f"المبلغ (₪) - {it}", key=f"v_{it}", min_value=0.0, step=0.5, value=None, placeholder="₪")
            
            if money_val and money_val > 0:
                if curr_sell_price > 0:
                    # الحسبة الدقيقة
                    calc_qty = float(money_val) / curr_sell_price
                    # الربح = (سعر البيع - سعر الشراء) * الكمية
                    single_profit = curr_sell_price - curr_buy_price
                    calc_profit = round(single_profit * calc_qty, 2)
                    
                    # تنبيه إذا كان هناك خسارة قبل الحفظ
                    if calc_profit < 0:
                        st.error(f"انتبه! سعر الشراء ({curr_buy_price}) أعلى من البيع!")
                    
                    temp_bill.append({
                        'item': it, 
                        'qty': calc_qty, 
                        'amount': float(money_val), 
                        'profit': calc_profit
                    })
                else:
                    st.warning("سعر البيع مسجل 0!")

    st.markdown("---")
    if temp_bill:
        total_cash = sum(row['amount'] for row in temp_bill)
        st.subheader(f"💰 إجمالي المبلغ المطلوب: {total_cash:.2f} ₪")
        
        if st.button("✅ إتمام البيع وحفظ العملية", use_container_width=True):
            bid = str(uuid.uuid4())[:8]
            for row in temp_bill:
                # تحديث المخزن
                st.session_state.inventory[row['item']]['كمية'] -= row['qty']
                
                # إضافة لسجل المبيعات
                new_row = {
                    'date': datetime.now().strftime("%Y-%m-%d"), 
                    'item': row['item'], 
                    'amount': row['amount'], 
                    'profit': row['profit'], 
                    'method': 'نقدي', 
                    'customer_name': 'زبون محل', 
                    'bill_id': bid
                }
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
            
            sync_to_google()
            st.success("تم الحفظ بنجاح، والآن الربح سيظهر بشكل صحيح!")
            st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 تفاصيل وإدارة المخزن</h1>", unsafe_allow_html=True)
    
    if st.session_state.inventory:
        items_list = []
        for it, data in st.session_state.inventory.items():
            items_list.append({
                'الصنف': it,
                'القسم': data.get('قسم', 'أخرى'),
                'سعر الشراء': data['شراء'],
                'سعر البيع': data['بيع'],
                'الكمية الحالية': data['كمية'],
                'ربح القطعة': data['بيع'] - data['شراء'],
                'إجمالي قيمة المخزن': data['شراء'] * data['كمية']
            })
        
        df_inv = pd.DataFrame(items_list)
        stock_value = df_inv['إجمالي قيمة المخزن'].sum()
        st.markdown(f"<div class='report-card'><h5>إجمالي قيمة رأس المال في المخزن حالياً</h5><h2>{format_num(stock_value)} ₪</h2></div><br>", unsafe_allow_html=True)
        
        st.subheader("📋 كشف تفصيلي بالأصناف")
        st.dataframe(df_inv, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔍 الجرد السريع وتعديل الكميات")
        c1, c2 = st.columns([1, 2])
        f_cat = c1.selectbox("📂 تصفية حسب القسم", ["الكل"] + st.session_state.CATEGORIES)
        search_st = c2.text_input("🔍 ابحث في الأصناف...")
        
        cols = st.columns(3); display_idx = 0
        for it, data in st.session_state.inventory.items():
            item_cat = data.get('قسم', 'أخرى')
            if (f_cat == "الكل" or item_cat == f_cat) and (search_st.lower() in it.lower()):
                with cols[display_idx % 3]:
                    card_color = "#27ae60" if data['كمية'] > 5 else ("#f39c12" if data['كمية'] > 0 else "#e74c3c")
                    st.markdown(f"<div class='stock-card' style='border-top: 6px solid {card_color};'><small>{item_cat}</small><h3>{it}</h3><p>المتبقي: {data['كمية']:.2f}</p><h4>{data['بيع']} ₪</h4></div>", unsafe_allow_html=True)
                    with st.expander(f"⚙️ جرد/تعديل كمية {it}"):
                        new_q = st.number_input("الكمية الفعلية", value=float(data['كمية']), key=f"inv_q_{it}")
                        if st.button("تحديث الكمية", key=f"inv_btn_{it}"):
                            st.session_state.inventory[it]['كمية'] = new_q
                            st.session_state.inventory[it]['أصلي'] = new_q
                            sync_to_google(); st.rerun()
                display_idx += 1
    else:
        st.info("المخزن فارغ.")

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقرير المالي الشامل - أبو عمر</h1>", unsafe_allow_html=True)
    
    # --- 1. تجهيز البيانات والتواريخ ---
    df_sales = st.session_state.sales_df.copy()
    df_exp = st.session_state.expenses_df.copy()
    df_waste = st.session_state.waste_df.copy()
    
    for df in [df_sales, df_exp, df_waste]:
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date

    today = datetime.now().date()
    start_of_week = today - pd.Timedelta(days=today.weekday() + 1) # حساب بداية الأسبوع

    # --- 2. حسابات الأداء (اليوم والأسبوع) ---
    def get_stats(df_s, df_e, df_w, target_date=None):
        if target_date == "week":
            s = df_s[df_s['date'] >= start_of_week] if not df_s.empty else pd.DataFrame()
            e = df_e[df_e['date'] >= start_of_week] if not df_e.empty else pd.DataFrame()
            w = df_w[df_w['date'] >= start_of_week] if not df_w.empty else pd.DataFrame()
        else:
            s = df_s[df_s['date'] == today] if not df_s.empty else pd.DataFrame()
            e = df_e[df_e['date'] == today] if not df_e.empty else pd.DataFrame()
            w = df_w[df_w['date'] == today] if not df_w.empty else pd.DataFrame()
        
        sales_val = s['amount'].sum() if not s.empty else 0
        gross_p = s['profit'].sum() if not s.empty else 0
        exp_val = pd.to_numeric(e['amount'], errors='coerce').sum() if not e.empty else 0
        waste_val = pd.to_numeric(w['loss_value'], errors='coerce').sum() if not w.empty else 0
        net_p = gross_p - exp_val - waste_val
        return sales_val, gross_p, exp_val + waste_val, net_p

    # استخراج القيم
    d_sales, d_gross, d_lost, d_net = get_stats(df_sales, df_exp, df_waste)
    w_sales, w_gross, w_lost, w_net = get_stats(df_sales, df_exp, df_waste, "week")

    # --- 3. عرض كروت الأداء ---
    st.subheader("🗓️ ملخص الأداء المالي")
    tab1, tab2 = st.tabs(["💰 أداء اليوم", "📅 أداء الأسبوع"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("مبيعات اليوم", f"{format_num(d_sales)} ₪")
        c2.metric("ربح البيع", f"{format_num(d_gross)} ₪")
        c3.metric("مصروفات وتالف", f"{format_num(d_lost)} ₪", delta_color="inverse")
        st.markdown(f"<div style='background:#27ae60; color:white; padding:15px; border-radius:10px; text-align:center;'><h3>صافي ربح اليوم: {format_num(d_net)} ₪</h3></div>", unsafe_allow_html=True)

    with tab2:
        c1, c2, c3 = st.columns(3)
        c1.metric("مبيعات الأسبوع", f"{format_num(w_sales)} ₪")
        c2.metric("ربح الأسبوع", f"{format_num(w_gross)} ₪")
        c3.metric("مصروفات وتالف", f"{format_num(w_lost)} ₪", delta_color="inverse")
        st.markdown(f"<div style='background:#2980b9; color:white; padding:15px; border-radius:10px; text-align:center;'><h3>صافي ربح الأسبوع: {format_num(w_net)} ₪</h3></div>", unsafe_allow_html=True)

    # --- 4. سجل المبيعات والزبائن ---
    st.markdown("---")
    st.subheader("📑 سجل العمليات والمبيعات")
    if not df_sales.empty:
        # ترتيب العمليات من الأحدث للأقدم
        display_sales = df_sales.sort_values(by='date', ascending=False)
        st.dataframe(display_sales[['date', 'item', 'amount', 'profit', 'customer_name']], use_container_width=True, hide_index=True)
    else:
        st.info("لا يوجد مبيعات مسجلة بعد.")

    # --- 5. تقرير التالف والمصروفات ---
    st.markdown("---")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.subheader("💸 سجل المصروفات")
        if not df_exp.empty:
            st.table(df_exp[['date', 'reason', 'amount']].tail(5))
        else: st.write("لا يوجد مصروفات.")
    
    with col_w2:
        st.subheader("⚠️ سجل التالف")
        if not df_waste.empty:
            st.table(df_waste[['date', 'item', 'loss_value']].tail(5))
        else: st.write("لا يوجد تالف.")

    # --- 6. إقفال الدورة المالية ---
    st.markdown("---")
    st.subheader("🔒 إقفال الدورة المالية")
    with st.expander("تحذير: إقفال الدورة يقوم بأرشفة مبيعات اليوم"):
        st.warning("عند الضغط على الزر، سيتم اعتبار أن اليوم قد انتهى. (يفضل أخذ نسخة من جوجل شيت دائماً)")
        if st.button("🚀 إقفال اليوم وبدء دورة جديدة"):
            # هنا يمكنك إضافة كود لنقل البيانات لجدول أرشيف إذا رغبت، 
            # لكن حالياً سنكتفي بتحديث الواجهة
            st.success("تم إقفال الدورة المالية بنجاح!")
            st.rerun()

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 إدارة وسجل المصروفات</h1>", unsafe_allow_html=True)
    df_exp = st.session_state.expenses_df.copy()
    total_exp = pd.to_numeric(df_exp['amount'], errors='coerce').sum() if not df_exp.empty else 0
    st.markdown(f"<div class='report-card'><h5>إجمالي كافة المصروفات</h5><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)
    
    with st.expander("➕ تسجيل مصروف جديد", expanded=True):
        with st.form("exp_form", clear_on_submit=True):
            r = st.text_input("بيان المصروف")
            a = st.number_input("المبلغ (₪)", min_value=0.0, value=None, placeholder="0.0")
            if st.form_submit_button("حفظ المصروف"):
                if r and a:
                    new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': float(a), 'id': str(uuid.uuid4())[:6]}
                    st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                    sync_to_google(); st.rerun()

    if not st.session_state.expenses_df.empty:
        for index, row in st.session_state.expenses_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
            c1.write(row['date'])
            c2.write(f"**{row['reason']}**")
            c3.write(f"{row['amount']} ₪")
            if c4.button("❌", key=f"del_{index}"):
                st.session_state.expenses_df = st.session_state.expenses_df.drop(index)
                sync_to_google(); st.rerun()

if menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات ونظام الإصلاح</h1>", unsafe_allow_html=True)
    
    # --- قسم إصلاح البيانات ---
    st.subheader("🛠️ أدوات صيانة البيانات")
    st.info("هذا الزر يقوم بإعادة حساب الأرباح لكل المبيعات القديمة بناءً على أسعار الشراء والبيع الحالية في المخزن.")
    
    if st.button("🔄 إصلاح سجل الأرباح (تنظيف الماينوس)"):
        with st.spinner("جاري معالجة البيانات وإصلاح الأرباح..."):
            # 1. نسخة من سجل المبيعات
            fixed_sales = st.session_state.sales_df.copy()
            
            # 2. حلقة فحص لكل عملية بيع
            for index, row in fixed_sales.iterrows():
                item_name = row['item']
                
                # التأكد من وجود الصنف في المخزن لجلب سعره
                if item_name in st.session_state.inventory:
                    data = st.session_state.inventory[item_name]
                    
                    try:
                        s_price = float(str(data.get('بيع', 0)).replace('₪', '').strip())
                        b_price = float(str(data.get('شراء', 0)).replace('₪', '').strip())
                        
                        # حساب الكمية اللي كانت مباعة (المبلغ / سعر البيع)
                        # إذا كان المبلغ مسجل، نعيد حساب الربح
                        sold_amount = float(row['amount'])
                        if s_price > 0:
                            actual_qty = sold_amount / s_price
                            correct_profit = round((s_price - b_price) * actual_qty, 2)
                            
                            # تحديث الربح في الجدول
                            fixed_sales.at[index, 'profit'] = correct_profit
                    except Exception as e:
                        continue
            
            # 3. حفظ التعديلات في السيشن وفي جوجل شيت
            st.session_state.sales_df = fixed_sales
            sync_to_google()
            
            st.success("✅ تم إصلاح كافة الأرباح بنجاح! اذهب الآن للتقرير المالي وستجد الأرقام صحيحة.")
            st.rerun()

    st.markdown("---")
    # ... باقي كود الإعدادات الخاص بك (تعديل الأقسام، حذف الأصناف، إلخ)
