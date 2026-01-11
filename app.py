import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-right: 8px solid #27ae60; padding-right: 15px; margin-bottom: 25px; }
    .stock-card { background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; transition: 0.3s; }
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال المساعدة المطورة (لضمان الأرقام)
def clean_num(val):
    try:
        if val is None or val == "" or pd.isna(val): return 0.0
        return float(str(val).replace(',', '').replace('₪', '').strip())
    except: return 0.0

def format_num(val):
    return f"{clean_num(val):,.2f}"

# 3. الاتصال وقاعدة البيانات
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_to_google():
    try:
        inv_data = [{'item': k, **v} for k, v in st.session_state.inventory.items()]
        sales_to_save = st.session_state.sales_df.copy()
        if not sales_to_save.empty:
            sales_to_save['profit'] = pd.to_numeric(sales_to_save['profit'], errors='coerce').fillna(0).round(2)
            sales_to_save['amount'] = pd.to_numeric(sales_to_save['amount'], errors='coerce').fillna(0).round(2)

        conn.update(worksheet="Inventory", data=pd.DataFrame(inv_data))
        conn.update(worksheet="Sales", data=sales_to_save)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"خطأ في المزامنة: {e}")
        return False

# 4. تحميل البيانات مع التحويل الرقمي
if 'inventory' not in st.session_state:
    try:
        inv_df = conn.read(worksheet="Inventory", ttl=0)
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        
        s_df = conn.read(worksheet="Sales", ttl=0)
        if not s_df.empty:
            s_df['profit'] = pd.to_numeric(s_df['profit'], errors='coerce').fillna(0).round(2)
            s_df['amount'] = pd.to_numeric(s_df['amount'], errors='coerce').fillna(0).round(2)
        st.session_state.sales_df = s_df
        
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        st.session_state.inventory = {}
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount', 'id'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث البيانات"): st.rerun()

# --- 🛒 نقطة البيع ---
if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
    if 'pay_method_selected' not in st.session_state: st.session_state.pay_method_selected = "نقدي 💵"

    col_m1, col_m2 = st.columns(2)
    if col_m1.button("💵 نقدي (Cash)", use_container_width=True):
        st.session_state.pay_method_selected = "نقدي 💵"
        st.rerun()
    if col_m2.button("📱 تطبيق (App)", use_container_width=True):
        st.session_state.pay_method_selected = "تطبيق 📱"
        st.rerun()

    c1, c2 = st.columns([1, 2])
    cat_sel = c1.selectbox("📂 القسم", ["الكل"] + st.session_state.CATEGORIES)
    search = c2.text_input("🔍 ابحث عن صنف...")
    
    items = {k: v for k, v in st.session_state.inventory.items() if (cat_sel == "الكل" or v.get('قسم') == cat_sel) and search.lower() in k.lower()}
    
    cols = st.columns(4)
    temp_bill = []
    
    for idx, (it, data) in enumerate(items.items()):
        with cols[idx % 4]:
            curr_sell = clean_num(data.get('بيع', 0))
            curr_buy = clean_num(data.get('شراء', 0))
            st.markdown(f"<div style='background:#f9f9f9; padding:10px; border-radius:10px; border:1px solid #ddd; text-align:center;'><b>{it}</b><br><span style='color:green;'>{curr_sell} ₪</span></div>", unsafe_allow_html=True)
            money_val = st.number_input(f"المبلغ", key=f"v_{it}", min_value=0.0, step=0.5, value=None)
            
            if money_val and money_val > 0 and curr_sell > 0:
                calc_qty = money_val / curr_sell
                calc_profit = round((curr_sell - curr_buy) * calc_qty, 2)
                temp_bill.append({'item': it, 'qty': calc_qty, 'amount': float(money_val), 'profit': float(calc_profit)})

    if temp_bill:
        total_cash = sum(row['amount'] for row in temp_bill)
        st.subheader(f"💰 الإجمالي: {total_cash:.2f} ₪")
        if st.button(f"✅ إتمام البيع", use_container_width=True):
            bid = str(uuid.uuid4())[:8]
            for row in temp_bill:
                st.session_state.inventory[row['item']]['كمية'] -= row['qty']
                new_row = {'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'item': row['item'], 'amount': row['amount'], 'profit': row['profit'], 'method': st.session_state.pay_method_selected, 'customer_name': "زبون محل", 'bill_id': bid}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
            sync_to_google()
            st.success("تم الحفظ!")
            st.rerun()

# --- 📦 المخزن والجرد (تمت استعادته وإصلاحه) ---
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
    if st.session_state.inventory:
        search_stock = st.text_input("🔍 ابحث في المخزن...")
        cols = st.columns(3)
        for idx, (it, data) in enumerate(st.session_state.inventory.items()):
            if search_stock.lower() in it.lower():
                qty = clean_num(data.get('كمية', 0))
                buy_p = clean_num(data.get('شراء', 0))
                sell_p = clean_num(data.get('بيع', 0))
                
                # تنبيه في حال كان سعر البيع أقل من الشراء (سبب السالب)
                loss_alert = ""
                if sell_p < buy_p: loss_alert = "<br><span style='color:red; font-weight:bold;'>⚠️ السعر يسبب خسارة!</span>"

                with cols[idx % 3]:
                    st.markdown(f"""<div class="stock-card">
                        <b>{it}</b>{loss_alert}<br>
                        الكمية: {qty} | الشراء: {buy_p} | <span style='color:green;'>البيع: {sell_p}</span>
                    </div>""", unsafe_allow_html=True)
                    with st.expander("تعديل الصنف"):
                        nq = st.number_input("الكمية", value=qty, key=f"q_{it}")
                        nb = st.number_input("سعر الشراء", value=buy_p, key=f"b_{it}")
                        ns = st.number_input("سعر البيع", value=sell_p, key=f"s_{it}")
                        if st.button("حفظ", key=f"btn_{it}"):
                            st.session_state.inventory[it].update({'كمية': nq, 'شراء': nb, 'بيع': ns})
                            sync_to_google()
                            st.rerun()

# --- 📊 التقارير المالية ---
# --- 📊 التقارير المالية ---



elif menu == "📊 التقارير المالية":



    from datetime import timedelta # تأكد من وجود هذا الاستيراد في أعلى الملف



    



    st.markdown("<h1 class='main-title'>📊 التقارير المالية الشاملة</h1>", unsafe_allow_html=True)



    



    # تحويل التواريخ لضمان الحسابات الصحيحة



    if not st.session_state.sales_df.empty:



        st.session_state.sales_df['date_only'] = pd.to_datetime(st.session_state.sales_df['date']).dt.strftime('%Y-%m-%d')



    else:



        st.session_state.sales_df['date_only'] = None







    today = datetime.now().strftime("%Y-%m-%d")



    last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")



    



    # --- 1. حساب القيم المالية ---



    daily_sales = st.session_state.sales_df[st.session_state.sales_df['date_only'] == today]['amount'].sum() if not st.session_state.sales_df.empty else 0



    weekly_sales = st.session_state.sales_df[st.session_state.sales_df['date_only'] >= last_week]['amount'].sum() if not st.session_state.sales_df.empty else 0



    



    # رأس المال (قيمة البضاعة الحالية بالمخزن)



    cap_stock = sum(v.get('كمية', 0) * v.get('شراء', 0) for v in st.session_state.inventory.values())



    



    # الأرباح والمصاريف



    raw_profit = st.session_state.sales_df['profit'].sum() if not st.session_state.sales_df.empty else 0



    total_exp = pd.to_numeric(st.session_state.expenses_df['amount'], errors='coerce').sum() if not st.session_state.expenses_df.empty else 0



    total_waste = pd.to_numeric(st.session_state.waste_df['loss_value'], errors='coerce').sum() if not st.session_state.waste_df.empty else 0



    



    net_profit = raw_profit - total_exp - total_waste







    # --- 2. عرض الصف الأول من البطاقات ---



    c1, c2, c3 = st.columns(3)



    c1.markdown(f"<div class='report-card'><h3>💰 مبيعات اليوم</h3><h2>{format_num(daily_sales)} ₪</h2></div>", unsafe_allow_html=True)



    c2.markdown(f"<div class='report-card'><h3>📅 مبيعات الأسبوع</h3><h2>{format_num(weekly_sales)} ₪</h2></div>", unsafe_allow_html=True)



    c3.markdown(f"<div class='report-card'><h3>🏗️ رأس المال الحالي</h3><h2>{format_num(cap_stock)} ₪</h2></div>", unsafe_allow_html=True)



    



    st.markdown("<br>", unsafe_allow_html=True)



    



    # --- 3. عرض الصف الثاني من البطاقات ---



    c4, c5, c6 = st.columns(3)



    p_color = "#27ae60" if net_profit >= 0 else "#e74c3c"



    



    c4.markdown(f"<div class='report-card' style='border-top: 5px solid {p_color}'><h3>💵 صافي الأرباح العام</h3><h2 style='color:{p_color}'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)



    c5.markdown(f"<div class='report-card' style='border-top: 5px solid #e74c3c'><h3>🗑️ إجمالي التالف</h3><h2 style='color:#e74c3c'>{format_num(total_waste)} ₪</h2></div>", unsafe_allow_html=True)



    c6.markdown(f"<div class='report-card' style='border-top: 5px solid #34495e'><h3>📉 إجمالي المصروفات</h3><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)







    st.divider()







    # --- 4. سجل الزبائن اليومي ---



    st.subheader("👥 سجل الزبائن والعمليات اليومي")



    sel_date = st.date_input("اختر التاريخ للعرض", datetime.now()).strftime('%Y-%m-%d')



    



    if not st.session_state.sales_df.empty:



        cust_df = st.session_state.sales_df[st.session_state.sales_df['date_only'] == sel_date].copy()



        



        if not cust_df.empty:



            # التأكد من وجود الأعمدة المطلوبة حتى لا يحدث خطأ



            for col in ['customer_phone', 'method']:



                if col not in cust_df.columns: cust_df[col] = "-"







            display_df = cust_df[['date', 'customer_name', 'customer_phone', 'item', 'amount', 'method']].rename(columns={



                'date': 'الوقت/التاريخ',



                'customer_name': 'الزبون',



                'customer_phone': 'الهاتف',



                'item': 'الصنف',



                'amount': 'المبلغ (₪)',



                'method': 'طريقة الدفع'



            })



            st.table(display_df)



        else:



            st.warning(f"لا توجد عمليات بيع مسجلة في تاريخ {sel_date}")



    else:



        st.info("سجل المبيعات فارغ تماماً.")



# --- 💸 المصروفات ---
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_f"):
        reason = st.text_input("السبب")
        amount = st.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("إضافة مصروف"):
            new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': reason, 'amount': amount, 'id': str(uuid.uuid4())[:6]}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
            sync_to_google()
            st.rerun()
    st.table(st.session_state.expenses_df)

# --- ⚙️ الإعدادات ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
    if st.button("🛠️ إصلاح تضارب أرقام المبيعات"):
        st.session_state.sales_df['profit'] = pd.to_numeric(st.session_state.sales_df['profit'], errors='coerce').fillna(0).round(2)
        sync_to_google()
        st.success("تم الإصلاح!")
