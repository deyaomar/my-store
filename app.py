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

# 2. الدوال المساعدة
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

if 'inventory' not in st.session_state:
    try:
        inv_df = conn.read(worksheet="Inventory", ttl=0)
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        
        s_df = conn.read(worksheet="Sales", ttl=0)
        if not s_df.empty:
            # حذف السطور الفارغة تماماً وتنسيق التاريخ بأمان
            s_df = s_df.dropna(subset=['date']) 
            s_df['date'] = pd.to_datetime(s_df['date'], errors='coerce')
            s_df = s_df.dropna(subset=['date']) # حذف أي سطر فشل تحويل تاريخه
            st.session_state.sales_df = s_df
        else:
            st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
            
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحميل البيانات: {e}")
        st.session_state.inventory = {}
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])

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
        
        if temp_bill and st.button("🚀 إتمام العملية"):
            st.session_state.current_bill_items = temp_bill
            st.session_state.show_customer_form = True
            st.rerun()
    else:
        c_n = st.text_input("اسم الزبون")
        c_p = st.text_input("رقم الهاتف")
        if st.button("✅ تأكيد"):
            bid = str(uuid.uuid4())[:8]
            for e in st.session_state.current_bill_items:
                st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': c_p, 'bill_id': bid}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            sync_to_google()
            st.session_state.show_customer_form = False
            st.rerun()

# --- 📦 المخزن والجرد ---
if menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن الذكية</h1>", unsafe_allow_html=True)
    
    if st.session_state.inventory:
        # إحصائيات سريعة للمخزن
        total_items = len(st.session_state.inventory)
        low_stock = sum(1 for v in st.session_state.inventory.values() if v['كمية'] <= 5 and v['كمية'] > 0)
        out_of_stock = sum(1 for v in st.session_state.inventory.values() if v['كمية'] <= 0)
        stock_value = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='report-card'><h5>إجمالي الأصناف</h5><h2>{total_items}</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h5>أصناف قاربت تنفد</h5><h2 style='color:orange;'>{low_stock}</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h5>أصناف نافدة</h5><h2 style='color:red;'>{out_of_stock}</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='report-card'><h5>قيمة المخزن (شراء)</h5><h2>{format_num(stock_value)} ₪</h2></div>", unsafe_allow_html=True)

        st.write("---")
        
        # البحث والفلترة
        search_stock = st.text_input("🔍 ابحث عن صنف في المخزن لسرعة الوصول...")
        
        # عرض الأصناف كبطاقات
        cols = st.columns(3)
        for idx, (it, data) in enumerate(st.session_state.inventory.items()):
            if search_stock.lower() in it.lower():
                with cols[idx % 3]:
                    # تحديد اللون حسب الحالة
                    if data['كمية'] <= 0:
                        status, color, bg = "ناقص ❌", "#e74c3c", "#fdeaea"
                    elif data['كمية'] <= 5:
                        status, color, bg = "قارب على النفاذ ⚠️", "#f39c12", "#fff5e6"
                    else:
                        status, color, bg = "متوفر ✅", "#27ae60", "#ebf9f1"

                    st.markdown(f"""
                        <div class="stock-card" style="background-color: {bg}; border-right: 6px solid {color};">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <b style="font-size: 1.2rem;">{it}</b>
                                <span class="status-badge" style="background:{color};">{status}</span>
                            </div>
                            <hr style="margin: 10px 0;">
                            <div style="display:flex; justify-content:space-between;">
                                <span>سعر الشراء: <b>{data['شراء']} ₪</b></span>
                                <span>الكمية: <b style="font-size: 1.1rem;">{data['كمية']}</b></span>
                            </div>
                            <div style="margin-top:5px;">سعر البيع: <b>{data['بيع']} ₪</b></div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # أزرار الإجراءات السريعة
                    with st.expander(f"⚙️ إدارة {it}"):
                        sub1, sub2 = st.tabs(["✏️ تعديل سريع", "⚠️ تالف"])
                        with sub1:
                            nb = st.number_input("شراء جديد", value=float(data['شراء']), key=f"nb_{it}")
                            ns = st.number_input("بيع جديد", value=float(data['بيع']), key=f"ns_{it}")
                            nq = st.number_input("الكمية الفعلية", value=float(data['كمية']), key=f"nq_{it}")
                            if st.button("حفظ التعديل", key=f"btn_{it}"):
                                st.session_state.inventory[it] = {'شراء': nb, 'بيع': ns, 'كمية': nq}
                                sync_to_google(); st.rerun()
                        with sub2:
                            w_qty = st.number_input("الكمية التالفة", min_value=0.0, max_value=float(data['كمية']), key=f"wq_{it}")
                            if st.button("تأكيد التالف", key=f"wb_{it}"):
                                loss = w_qty * data['شراء']
                                st.session_state.inventory[it]['كمية'] -= w_qty
                                new_w = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': it, 'qty': w_qty, 'loss_value': loss}
                                st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_w])], ignore_index=True)
                                sync_to_google(); st.rerun()
    else:
        st.info("المخزن فارغ! توجه للإعدادات لإضافة أصناف.")

# --- 📊 التقارير المالية ---
elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية الشاملة</h1>", unsafe_allow_html=True)
    
    # تحويل آمن للتاريخ لمعالجة القيم الفارغة أو الخاطئة ومنع الـ ValueError
    if not st.session_state.sales_df.empty:
        # تحويل العمود مع تحويل الأخطاء إلى قيم فارغة (NaT)
        temp_dates = pd.to_datetime(st.session_state.sales_df['date'], errors='coerce')
        # إنشاء عمود التاريخ فقط للفلترة
        st.session_state.sales_df['date_only'] = temp_dates.dt.strftime('%Y-%m-%d')
    else:
        st.session_state.sales_df['date_only'] = None

    today = datetime.now().strftime("%Y-%m-%d")
    last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    # الحسابات المالية مع التأكد من وجود بيانات
    sales_df = st.session_state.sales_df
    daily_sales = sales_df[sales_df['date_only'] == today]['amount'].apply(clean_num).sum()
    weekly_sales = sales_df[sales_df['date_only'] >= last_week]['amount'].apply(clean_num).sum()
    
    cap_stock = sum(clean_num(v.get('كمية', 0)) * clean_num(v.get('شراء', 0)) for v in st.session_state.inventory.values())
    raw_profit = sales_df['profit'].apply(clean_num).sum()
    
    total_exp = st.session_state.expenses_df['amount'].apply(clean_num).sum() if not st.session_state.expenses_df.empty else 0
    total_waste = st.session_state.waste_df['loss_value'].apply(clean_num).sum() if not st.session_state.waste_df.empty else 0
    
    net_profit = raw_profit - total_exp - total_waste

    # عرض البطاقات العلوية
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='report-card'><h3>💰 مبيعات اليوم</h3><h2>{format_num(daily_sales)} ₪</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='report-card'><h3>📅 مبيعات الأسبوع</h3><h2>{format_num(weekly_sales)} ₪</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='report-card'><h3>🏗️ رأس المال الحالي</h3><h2>{format_num(cap_stock)} ₪</h2></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # عرض البطاقات السفلية (الأرباح والمصاريف)
    c4, c5, c6 = st.columns(3)
    p_color = "#27ae60" if net_profit >= 0 else "#e74c3c"
    c4.markdown(f"<div class='report-card' style='border-color:{p_color}'><h3>💵 صافي الأرباح</h3><h2 style='color:{p_color}'>{format_num(net_profit)} ₪</h2></div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='report-card' style='border-color:#e74c3c'><h3>🗑️ إجمالي التالف</h3><h2>{format_num(total_waste)} ₪</h2></div>", unsafe_allow_html=True)
    c6.markdown(f"<div class='report-card'><h3>📉 إجمالي المصروفات</h3><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)

    st.divider()
    
    # سجل الزبائن
    st.subheader("👥 سجل الزبائن اليومي")
    sel_date = st.date_input("اختر التاريخ", datetime.now()).strftime('%Y-%m-%d')
    cust_df = sales_df[sales_df['date_only'] == sel_date]
    
    if not cust_df.empty:
        # عرض الجدول مع تحسين المسميات
        display_df = cust_df[['date', 'customer_name', 'customer_phone', 'item', 'amount', 'method']].copy()
        st.table(display_df.rename(columns={
            'date': 'الوقت',
            'customer_name': 'الزبون',
            'customer_phone': 'الهاتف',
            'item': 'الصنف',
            'amount': 'المبلغ',
            'method': 'الطريقة'
        }))
    else:
        st.info("لا توجد مبيعات مسجلة في هذا التاريخ.")

# --- 💸 المصروفات ---
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r = st.text_input("البيان")
        a = st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            new_e = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'reason': r, 'amount': a}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
            sync_to_google()
            st.rerun()
    st.table(st.session_state.expenses_df.sort_values(by='date', ascending=False))

# --- ⚙️ الإعدادات ---
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإعدادات</h1>", unsafe_allow_html=True)
    if st.button("🛠️ إصلاح تضارب البيانات"):
        sync_to_google()
        st.success("تمت المزامنة والإصلاح!")
