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

# --- 📦 المخزن والجرد المطور بميزة المطابقة ---
elif menu == "📦 المخزن والجرد":
st.markdown("<h1 class='main-title'>📦 إدارة ومطابقة المخزن</h1>", unsafe_allow_html=True)
    
    # إنشاء تبويبات: واحد للعرض العادي وواحد للجرد والمطابقة
    tab_view, tab_match = st.tabs(["📋 عرض المخزن الحالي", "🎯 مطابقة وجرد الكميات"])
    
    with tab_view:
        if st.session_state.inventory:
            stock_value = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())
            st.markdown(f"<div class='report-card'><h5>إجمالي قيمة البضاعة الحالية (رأس المال)</h5><h2>{format_num(stock_value)} ₪</h2></div>", unsafe_allow_html=True)
            
            search_stock = st.text_input("🔍 ابحث في الأصناف...")
            cols = st.columns(3)
            for idx, (it, data) in enumerate(st.session_state.inventory.items()):
                if search_stock.lower() in it.lower():
                    with cols[idx % 3]:
                        # تحديد اللون حسب الكمية
                        color = "#27ae60" if data['كمية'] > 5 else ("#f39c12" if data['كمية'] > 0 else "#e74c3c")
                        st.markdown(f"<div class='stock-card' style='border-right: 6px solid {color}; padding:10px; border-radius:10px; background:#fff; box-shadow: 2px 2px 10px #eee; margin-bottom:10px;'><b>{it}</b><br>سعر البيع: {data['بيع']} ₪ | الكمية: <b>{data['كمية']}</b></div>", unsafe_allow_html=True)
                        with st.expander(f"⚙️ تعديل سريع لـ {it}"):
                            nq = st.number_input("الكمية الحقيقية الآن", value=float(data['كمية']), key=f"q_edit_{it}")
                            if st.button("تحديث الكمية", key=f"btn_edit_{it}"):
                                st.session_state.inventory[it]['كمية'] = nq
                                sync_to_google()
                                st.rerun()
        else:
            st.info("لا يوجد أصناف في المخزن.")

    with tab_match:
        st.subheader("🎯 جرد المحل ومطابقة العجز والزيادة")
        st.write("قم بإدخال الكمية التي عددتها بيدك في المحل في عمود 'الكمية الفعلية'.")
        
        if st.session_state.inventory:
            # تجهيز البيانات للجدول التفاعلي
            inventory_list = []
            for it, data in st.session_state.inventory.items():
                inventory_list.append({
                    'الصنف': it,
                    'الكمية في النظام': data['كمية'],
                    'سعر الشراء': data['شراء']
                })
            
            df_match = pd.DataFrame(inventory_list)
            
            # عرض جدول قابل للتعديل (Data Editor)
            edited_df = st.data_editor(
                df_match,
                column_config={
                    "الكمية الفعلية": st.column_config.NumberColumn(
                        "الكمية الفعلية (جرد يدوي)",
                        help="اكتب هنا كم قطعة وجدت على الرف فعلياً",
                        min_value=0,
                        default=0,
                    )
                },
                disabled=["الصنف", "الكمية في النظام", "سعر الشراء"],
                hide_index=True,
                use_container_width=True,
                key="inventory_matcher"
            )

            # الحسابات المالية للفارق
            if "الكمية الفعلية" in edited_df.columns:
                edited_df['الفارق'] = edited_df['الكمية الفعلية'] - edited_df['الكمية في النظام']
                edited_df['قيمة الفارق (₪)'] = edited_df['الفارق'] * edited_df['سعر الشراء']
                
                total_loss_gain = edited_df['قيمة الفارق (₪)'].sum()
                
                st.write("---")
                c1, c2 = st.columns(2)
                with c1:
                    if total_loss_gain < 0:
                        st.markdown(f"<h3 style='color:red;'>إجمالي العجز: {format_num(abs(total_loss_gain))} ₪</h3>", unsafe_allow_html=True)
                    elif total_loss_gain > 0:
                        st.markdown(f"<h3 style='color:green;'>إجمالي الزيادة: {format_num(total_loss_gain)} ₪</h3>", unsafe_allow_html=True)
                    else:
                        st.write("### ✅ المخزن مطابق تماماً")
                
                with c2:
                    if st.button("💾 اعتماد نتائج الجرد وتصحيح المخزن", use_container_width=True):
                        for _, row in edited_df.iterrows():
                            item_name = row['الصنف']
                            st.session_state.inventory[item_name]['كمية'] = row['الكمية الفعلية']
                        sync_to_google()
                        st.success("تم تحديث المخزن بناءً على جردك الفعلي!")
                        st.rerun()
                
                # عرض التفاصيل
                st.dataframe(edited_df[['الصنف', 'الكمية في النظام', 'الكمية الفعلية', 'الفارق', 'قيمة الفارق (₪)']], use_container_width=True)

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

# --- 💸 المصروفات (المعدل مع السجل) ---
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>", unsafe_allow_html=True)
    
    # 1. إحصائية سريعة
    total_exp = pd.to_numeric(st.session_state.expenses_df['amount'], errors='coerce').sum()
    st.markdown(f"<div class='report-card'><h5>إجمالي المصروفات الحالية</h5><h2>{format_num(total_exp)} ₪</h2></div>", unsafe_allow_html=True)
    
    # 2. نموذج إضافة مصروف
    st.write("### ➕ إضافة مصروف جديد")
    with st.form("exp_form"):
        r = st.text_input("البيان (مثلاً: إيجار، كهرباء، كرتون)")
        a = st.number_input("المبلغ (₪)", min_value=0.0, step=1.0)
        if st.form_submit_button("حفظ المصروف"):
            if r and a > 0:
                new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                sync_to_google()
                st.success("تم حفظ المصروف بنجاح")
                st.rerun()
            else:
                st.error("يرجى إدخال البيان والمبلغ بشكل صحيح")

    # 3. سجل المصروفات
    st.write("---")
    st.write("### 📋 سجل المصروفات السابقة")
    if not st.session_state.expenses_df.empty:
        # ترتيب المصاريف من الأحدث للأقدم
        display_exp = st.session_state.expenses_df.copy()
        display_exp.columns = ['التاريخ', 'البيان', 'المبلغ']
        st.dataframe(display_exp.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("لا يوجد مصروفات مسجلة بعد.")

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إضافة أصناف جديدة</h1>", unsafe_allow_html=True)
    with st.form("add_form"):
        n = st.text_input("اسم الصنف"); b = st.number_input("شراء"); s = st.number_input("بيع"); q = st.number_input("الكمية")
        if st.form_submit_button("إضافة للمخزن"):
            st.session_state.inventory[n] = {'شراء': b, 'بيع': s, 'كمية': q}
            sync_to_google(); st.success("تمت الإضافة!"); st.rerun()
