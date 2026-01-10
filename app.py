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
    
    /* ستايل بطاقة المخزن */
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
    .status-badge {
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        color: white;
    }
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
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        st.session_state.sales_df = conn.read(worksheet="Sales", ttl=0)
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        st.session_state.inventory = {}
        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount'])
        st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

# 5. القائمة الجانبية
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "💸 المصروفات", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث البيانات"): st.rerun()

# --- 📦 المخزن والجرد (التصميم الاحترافي الجديد) ---
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

# --- بقية الأقسام (البيع، التقارير، المصروفات، الإعدادات) ---
# سأبقيها تعمل كما هي في كودك الأخير لضمان الاستقرار
elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
    search = st.text_input("🔍 ابحث عن صنف لبيعه...")
    items = {k: v for k, v in st.session_state.inventory.items() if search.lower() in k.lower()}
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

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير والتحليل المالي</h1>", unsafe_allow_html=True)
    sales = st.session_state.sales_df.copy(); sales['amount'] = pd.to_numeric(sales['amount'], errors='coerce').fillna(0); sales['profit'] = pd.to_numeric(sales['profit'], errors='coerce').fillna(0)
    exp = st.session_state.expenses_df.copy(); exp['amount'] = pd.to_numeric(exp['amount'], errors='coerce').fillna(0)
    waste = st.session_state.waste_df.copy(); waste['loss_value'] = pd.to_numeric(waste['loss_value'], errors='coerce').fillna(0)
    
    t_sales = sales['amount'].sum(); t_raw_p = sales['profit'].sum(); t_exp = exp['amount'].sum(); t_waste = waste['loss_value'].sum(); n_profit = t_raw_p - t_exp - t_waste
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div class='report-card'><h5>إجمالي المبيعات</h5><h2>{format_num(t_sales)} ₪</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='report-card'><h5>أرباح المبيعات</h5><h2>{format_num(t_raw_p)} ₪</h2></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='report-card'><h5>مصاريف + تالف</h5><h2 style='color:red;'>{format_num(t_exp + t_waste)} ₪</h2></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='report-card'><h5>صافي الربح</h5><h2 style='color:green;'>{format_num(n_profit)} ₪</h2></div>", unsafe_allow_html=True)
    st.subheader("📝 تفاصيل العمليات")
    st.dataframe(sales.sort_index(ascending=False), use_container_width=True)

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_form"):
        r = st.text_input("البيان"); a = st.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ المصروف"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}])], ignore_index=True)
            sync_to_google(); st.rerun()

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إضافة أصناف جديدة</h1>", unsafe_allow_html=True)
    with st.form("add_form"):
        n = st.text_input("اسم الصنف"); b = st.number_input("شراء"); s = st.number_input("بيع"); q = st.number_input("الكمية")
        if st.form_submit_button("إضافة للمخزن"):
            st.session_state.inventory[n] = {'شراء': b, 'بيع': s, 'كمية': q}
            sync_to_google(); st.success("تمت الإضافة!"); st.rerun()
