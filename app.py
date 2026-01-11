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

# --- 🛒 نقطة البيع (بتصميم البطاقات الملونة للدفع) ---
if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع بالمبلغ (شيكل)</h1>", unsafe_allow_html=True)

    # 1. نظام اختيار طريقة الدفع في أعلى الشاشة (بطاقات ملونة)
    if 'pay_method_selected' not in st.session_state:
        st.session_state.pay_method_selected = "نقدي 💵"

    st.markdown("### 💳 اختر طريقة الدفع")
    col_m1, col_m2 = st.columns(2)
    
    # بطاقة النقدي
    cash_style = "border: 3px solid #27ae60; background: #ebf9f1;" if st.session_state.pay_method_selected == "نقدي 💵" else "border: 1px solid #ddd; background: #fff;"
    if col_m1.button("💵 الدفع نقدي (Cash)", use_container_width=True):
        st.session_state.pay_method_selected = "نقدي 💵"
        st.rerun()
    col_m1.markdown(f"<div style='{cash_style} text-align:center; padding:5px; border-radius:10px; margin-top:-10px;'><small>تم اختيار النقدي</small></div>" if st.session_state.pay_method_selected == "نقدي 💵" else "", unsafe_allow_html=True)

    # بطاقة التطبيق
    app_style = "border: 3px solid #2980b9; background: #eaf2f8;" if st.session_state.pay_method_selected == "تطبيق 📱" else "border: 1px solid #ddd; background: #fff;"
    if col_m2.button("📱 الدفع تطبيق (App)", use_container_width=True):
        st.session_state.pay_method_selected = "تطبيق 📱"
        st.rerun()
    col_m2.markdown(f"<div style='{app_style} text-align:center; padding:5px; border-radius:10px; margin-top:-10px;'><small>تم اختيار التطبيق</small></div>" if st.session_state.pay_method_selected == "تطبيق 📱" else "", unsafe_allow_html=True)

    st.divider()

    # 2. الفلترة والبحث
    c1, c2 = st.columns([1, 2])
    cat_sel = c1.selectbox("📂 القسم", ["الكل"] + st.session_state.CATEGORIES)
    search = c2.text_input("🔍 ابحث عن صنف لبيعه...")
    
    # منطق تصفية الأصناف
    items_to_sell = st.session_state.inventory.items()
    if cat_sel != "الكل":
        items_to_sell = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat_sel}.items()
    
    items = {k: v for k, v in items_to_sell if search.lower() in k.lower()}
    
    # 3. عرض الأصناف
    cols = st.columns(4)
    temp_bill = []
    
    for idx, (it, data) in enumerate(items.items()):
        with cols[idx % 4]:
            try:
                curr_sell_price = float(str(data.get('بيع', 0)).replace('₪', '').strip())
                curr_buy_price = float(str(data.get('شراء', 0)).replace('₪', '').strip())
                curr_qty = float(data.get('كمية', 0))
            except:
                curr_sell_price = 0.0; curr_buy_price = 0.0; curr_qty = 0.0

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
                    calc_qty = float(money_val) / curr_sell_price
                    single_profit = curr_sell_price - curr_buy_price
                    calc_profit = round(single_profit * calc_qty, 2)
                    
                    temp_bill.append({
                        'item': it, 'qty': calc_qty, 'amount': float(money_val), 'profit': calc_profit
                    })

    st.markdown("---")
    
    # 4. إتمام العملية
    if temp_bill:
        total_cash = sum(row['amount'] for row in temp_bill)
        
        col_end1, col_end2 = st.columns([2, 1])
        with col_end1:
            st.subheader(f"💰 المبلغ المطلوب: {total_cash:.2f} ₪ ({st.session_state.pay_method_selected})")
        with col_end2:
            cust_name = st.text_input("👤 اسم الزبون", value="زبون محل")

        if st.button(f"✅ إتمام البيع ({st.session_state.pay_method_selected})", use_container_width=True):
            bid = str(uuid.uuid4())[:8]
            for row in temp_bill:
                # تحديث الكمية في المخزن
                st.session_state.inventory[row['item']]['كمية'] -= row['qty']
                
                # تسجيل العملية
                new_row = {
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    'item': row['item'], 
                    'amount': row['amount'], 
                    'profit': row['profit'], 
                    'method': st.session_state.pay_method_selected, # القيمة المختارة من البطاقات
                    'customer_name': cust_name, 
                    'bill_id': bid
                }
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
            
            sync_to_google()
            st.success(f"تم تسجيل الفاتورة بنجاح - طريقة الدفع: {st.session_state.pay_method_selected}")
            st.rerun()

# --- 📦 المخزن والجرد ---
if menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن الذكية</h1>", unsafe_allow_html=True)
    
    if st.session_state.inventory:
        # 1. إحصائيات سريعة للمخزن (البطاقات العلوية)
        total_items = len(st.session_state.inventory)
        low_stock = sum(1 for v in st.session_state.inventory.values() if 0 < float(v.get('كمية', 0)) <= 5)
        out_of_stock = sum(1 for v in st.session_state.inventory.values() if float(v.get('كمية', 0)) <= 0)
        stock_value = sum(float(v.get('شراء', 0)) * float(v.get('كمية', 0)) for v in st.session_state.inventory.values())

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='report-card'><h5>إجمالي الأصناف</h5><h2>{total_items}</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h5>أصناف قاربت تنفد</h5><h2 style='color:orange;'>{low_stock}</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h5>أصناف نافدة</h5><h2 style='color:red;'>{out_of_stock}</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='report-card'><h5>قيمة المخزن (شراء)</h5><h2>{format_num(stock_value)} ₪</h2></div>", unsafe_allow_html=True)

        st.write("---")
        
        # 2. البحث والفلترة
        search_stock = st.text_input("🔍 ابحث عن صنف في المخزن لسرعة الوصول...")
        
        # 3. عرض الأصناف كبطاقات تفاعلية
        cols = st.columns(3)
        display_idx = 0
        
        # ترتيب الأصناف بحيث يظهر الناقص أولاً (اختياري)
        sorted_inventory = dict(sorted(st.session_state.inventory.items(), key=lambda x: float(x[1].get('كمية', 0))))

        for it, data in sorted_inventory.items():
            if search_stock.lower() in it.lower():
                qty = float(data.get('كمية', 0))
                buy_p = float(data.get('شراء', 0))
                sell_p = float(data.get('بيع', 0))
                
                with cols[display_idx % 3]:
                    # تحديد الحالة واللون
                    if qty <= 0:
                        status, color, bg = "ناقص ❌", "#e74c3c", "#fdeaea"
                    elif qty <= 5:
                        status, color, bg = "قارب على النفاذ ⚠️", "#f39c12", "#fff5e6"
                    else:
                        status, color, bg = "متوفر ✅", "#27ae60", "#ebf9f1"

                    # تصميم بطاقة الصنف
                    st.markdown(f"""
                        <div class="stock-card" style="background-color: {bg}; border-right: 6px solid {color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <b style="font-size: 1.1rem;">{it}</b>
                                <span style="background:{color}; color:white; padding:2px 8px; border-radius:15px; font-size:12px;">{status}</span>
                            </div>
                            <hr style="margin: 8px 0; border: 0.5px solid #ddd;">
                            <div style="display:flex; justify-content:space-between; font-size: 14px;">
                                <span>شراء: <b>{buy_p} ₪</b></span>
                                <span>الكمية: <b style="font-size: 1.1rem;">{qty}</b></span>
                            </div>
                            <div style="margin-top:5px; font-size: 14px;">بيع: <b style="color:green;">{sell_p} ₪</b></div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # أزرار الإدارة داخل Expander
                    with st.expander(f"⚙️ إدارة {it}"):
                        tab_edit, tab_waste = st.tabs(["✏️ تعديل سريع", "⚠️ تسجيل تالف"])
                        
                        with tab_edit:
                            nb = st.number_input("سعر الشراء", value=buy_p, key=f"nb_{it}")
                            ns = st.number_input("سعر البيع", value=sell_p, key=f"ns_{it}")
                            nq = st.number_input("الكمية الفعلية", value=qty, key=f"nq_{it}")
                            if st.button("حفظ التعديلات", key=f"btn_{it}", use_container_width=True):
                                st.session_state.inventory[it].update({'شراء': nb, 'بيع': ns, 'كمية': nq})
                                sync_to_google()
                                st.success(f"تم تحديث {it}")
                                st.rerun()
                        
                        with tab_waste:
                            w_qty = st.number_input("الكمية التالفة", min_value=0.0, max_value=qty, key=f"wq_{it}")
                            if st.button("تأكيد التالف", key=f"wb_{it}", use_container_width=True, type="secondary"):
                                if w_qty > 0:
                                    loss = w_qty * buy_p
                                    st.session_state.inventory[it]['كمية'] -= w_qty
                                    new_w = {
                                        'date': datetime.now().strftime("%Y-%m-%d"), 
                                        'item': it, 
                                        'qty': w_qty, 
                                        'loss_value': loss
                                    }
                                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                                    sync_to_google()
                                    st.warning(f"تم تسجيل {w_qty} تالف من {it}")
                                    st.rerun()
                    
                display_idx += 1
    else:
        st.info("المخزن فارغ حالياً! قم بإضافة الأصناف من شاشة الإعدادات.")
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

# 1. إضافة صنف جديد (خانات فارغة لسهولة الإدخال)
    with tab_add:
        st.subheader("📦 إضافة صنف جديد للمخزن")
        with st.form("add_form", clear_on_submit=True):
            name = st.text_input("اسم الصنف", placeholder="مثال: سكر 1 كيلو")
            
            c1, c2, c3 = st.columns(3)
            # استخدام value=None يجعل الخانة فارغة عند البدء
            b_p = c1.number_input("سعر الشراء", min_value=0.0, step=0.1, value=None, placeholder="0.0")
            s_p = c2.number_input("سعر البيع", min_value=0.0, step=0.1, value=None, placeholder="0.0")
            qty = c3.number_input("الكمية المتوفرة", min_value=0.0, step=1.0, value=None, placeholder="0.0")
            
            cat = st.selectbox("القسم", st.session_state.CATEGORIES)
            
            if st.form_submit_button("➕ إضافة للمخزن"):
                if name and b_p is not None and s_p is not None and qty is not None:
                    st.session_state.inventory[name] = {
                        'شراء': float(b_p), 
                        'بيع': float(s_p), 
                        'كمية': float(qty), 
                        'قسم': cat, 
                        'أصلي': float(qty)
                    }
                    if sync_to_google():
                        st.success(f"✅ تم إضافة {name} بنجاح!")
                        st.rerun()
                else:
                    st.error("⚠️ يرجى تعبئة جميع الخانات (الاسم، الشراء، البيع، والكمية)")
