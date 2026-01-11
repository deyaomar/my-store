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
    
    # 1. تجهيز البيانات
    df_sales = st.session_state.sales_df.copy()
    df_exp = st.session_state.expenses_df.copy()
    df_waste = st.session_state.waste_df.copy()
    
    # تحويل التواريخ والأرقام لضمان دقة الحسابات
    for df in [df_sales, df_exp, df_waste]:
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date

    today = datetime.now().date()

    # 2. حسابات رأس المال
    total_original_cap = sum(v['شراء'] * v.get('أصلي', v['كمية']) for v in st.session_state.inventory.values())
    current_stock_cap = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())

    # 3. حسابات اليوم (مبيعات، أرباح، مصروفات، تالف)
    day_sales_df = df_sales[df_sales['date'] == today] if not df_sales.empty else pd.DataFrame()
    t_sales = day_sales_df['amount'].sum() if not day_sales_df.empty else 0
    t_gross_profit = day_sales_df['profit'].sum() if not day_sales_df.empty else 0
    
    day_exp_df = df_exp[df_exp['date'] == today] if not df_exp.empty else pd.DataFrame()
    t_exp = pd.to_numeric(day_exp_df['amount'], errors='coerce').sum() if not day_exp_df.empty else 0
    
    day_waste_df = df_waste[df_waste['date'] == today] if not df_waste.empty else pd.DataFrame()
    t_waste = pd.to_numeric(day_waste_df['loss_value'], errors='coerce').sum() if not day_waste_df.empty else 0
    
    # صافي الربح = إجمالي أرباح البيع - المصروفات - قيمة التالف
    t_net_profit = t_gross_profit - t_exp - t_waste

    # --- عرض النتائج ---
    st.markdown("### 🏦 حالة رأس المال (المخزن)")
    col_cap1, col_cap2 = st.columns(2)
    with col_cap1:
        st.markdown(f"<div style='background: #2c3e50; padding: 20px; border-radius: 15px; color: white; text-align: center;'><p style='margin:0;'>إجمالي رأس المال الأصلي</p><h2 style='margin:0;'>{format_num(total_original_cap)} ₪</h2></div>", unsafe_allow_html=True)
    with col_cap2:
        st.markdown(f"<div style='background: #34495e; padding: 20px; border-radius: 15px; color: white; text-align: center;'><p style='margin:0;'>رأس المال المتوفر حالياً</p><h2 style='margin:0;'>{format_num(current_stock_cap)} ₪</h2></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💰 تقرير الأرباح اليومية")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("مبيعات اليوم", f"{format_num(t_sales)} ₪")
    c2.metric("ربح البيع", f"{format_num(t_gross_profit)} ₪")
    c3.metric("مصروفات/تالف اليوم", f"{format_num(t_exp + t_waste)} ₪", delta_color="inverse")
    
    # عرض صافي الربح في كرت ملون
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #27ae60, #2ecc71); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-top: 20px;'>
            <p style='margin:0; font-size: 1.2em;'>صافي ربح اليوم الفعلي (بعد الخصم)</p>
            <h1 style='margin:0; font-size: 3em;'>{format_num(t_net_profit)} ₪</h1>
        </div>
    """, unsafe_allow_html=True)

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

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إدارة البضاعة والمشتريات</h1>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["📥 تزويد كمية", "✨ صنف جديد", "✏️ تعديل/حذف صنف", "📂 إدارة الأقسام"])
    
    with t1:
        if st.session_state.inventory:
            with st.form("add_stock_form"):
                item_name = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
                plus_q = st.number_input("الكمية المضافة", min_value=0.0, value=None)
                if st.form_submit_button("إضافة"):
                    if plus_q:
                        st.session_state.inventory[item_name]['كمية'] += plus_q
                        st.session_state.inventory[item_name]['أصلي'] = st.session_state.inventory[item_name]['كمية']
                        sync_to_google(); st.rerun()
    
    with t2:
        with st.form("add_form"):
            n = st.text_input("اسم الصنف الجديد")
            cat = st.selectbox("القسم", st.session_state.CATEGORIES)
            b = st.number_input("سعر الشراء", value=None)
            s = st.number_input("سعر البيع", value=None)
            q = st.number_input("الكمية", value=None)
            if st.form_submit_button("إضافة صنف جديد"):
                if n and b and s and q:
                    st.session_state.inventory[n] = {'قسم': cat, 'شراء': b, 'بيع': s, 'كمية': q, 'أصلي': q}
                    sync_to_google(); st.rerun()

    with t3:
        if st.session_state.inventory:
            edit_item = st.selectbox("اختر الصنف للتعديل", list(st.session_state.inventory.keys()))
            old_data = st.session_state.inventory[edit_item]
            with st.form("edit_form"):
                new_name = st.text_input("اسم الصنف", value=edit_item)
                new_b = st.number_input("سعر الشراء", value=float(old_data['شراء']))
                new_s = st.number_input("سعر البيع", value=float(old_data['بيع']))
                if st.form_submit_button("💾 حفظ"):
                    if new_name != edit_item: del st.session_state.inventory[edit_item]
                    st.session_state.inventory[new_name] = {'قسم': old_data['قسم'], 'شراء': new_b, 'بيع': new_s, 'كمية': old_data['كمية'], 'أصلي': old_data.get('أصلي', old_data['كمية'])}
                    sync_to_google(); st.rerun()
                if st.form_submit_button("🗑️ حذف نهائي"):
                    del st.session_state.inventory[edit_item]
                    sync_to_google(); st.rerun()
