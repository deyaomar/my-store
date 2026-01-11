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

    .stock-card { background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; transition: 0.3s; }

    .stock-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }

    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

    .bill-section { background: #f8f9fa; padding: 20px; border-radius: 15px; border: 1px dashed #27ae60; margin-top: 20px; }

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

        st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'phone', 'bill_id'])

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
                st.session_state.show_customer_form = True; st.rerun()
        else:
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الهاتف")
            if st.button("✅ تأكيد"):
                bid = str(uuid.uuid4())[:8]
                for e in st.session_state.current_bill_items:
                    st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': e['method'], 'customer_name': c_n, 'customer_phone': c_p, 'bill_id': bid}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.session_state.show_customer_form = False; st.rerun()

    elif menu == "📦 المخزن والجرد":

    st.markdown("<h1 class='main-title'>📦 حالة المخزن والمبيعات</h1>", unsafe_allow_html=True)

    with st.expander("⚠️ تسجيل بضاعة تالفة (فاقد)"):

        with st.form("waste_form"):

            col_w1, col_w2 = st.columns(2)

            w_item = col_w1.selectbox("اختر الصنف التالف", list(st.session_state.inventory.keys()))

            w_qty = col_w2.number_input("الكمية التالفة", min_value=0.0, step=0.1, value=None)

            if st.form_submit_button("تسجيل التالف وخصمه من المخزن"):

                if w_qty is not None and w_qty > 0 and w_qty <= st.session_state.inventory[w_item]['كمية']:

                    st.session_state.inventory[w_item]['كمية'] -= w_qty

                    loss = w_qty * st.session_state.inventory[w_item]['شراء']

                    new_waste = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': w_item, 'qty': w_qty, 'loss_value': loss}

                    st.session_state.waste_df = pd.concat([st.session_state.waste_df, pd.DataFrame([new_waste])], ignore_index=True)

                    sync_to_google(); st.success(f"تم تسجيل {w_qty} من {w_item} كتالف"); st.rerun()

                else: st.error("تأكد من إدخال كمية صحيحة!")



    st.markdown("---")

    if st.session_state.inventory:

        stock_value = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())

        st.markdown(f"<div class='report-card'><h5>إجمالي قيمة البضاعة الحالية (رأس المال)</h5><h2>{format_num(stock_value)} ₪</h2></div><br>", unsafe_allow_html=True)

        c1, c2 = st.columns([1, 2])

        f_cat = c1.selectbox("📂 تصفية حسب القسم", ["الكل"] + st.session_state.CATEGORIES)

        search_st = c2.text_input("🔍 ابحث في الأصناف...")

        cols = st.columns(3); display_idx = 0

        for it, data in st.session_state.inventory.items():

            item_cat = data.get('قسم', 'أخرى')

            if (f_cat == "الكل" or item_cat == f_cat) and (search_st.lower() in it.lower()):

                orig = data.get('أصلي', data['كمية']); sold = orig - data['كمية']

                with cols[display_idx % 3]:

                    card_color = "#27ae60" if data['كمية'] > 5 else ("#f39c12" if data['كمية'] > 0 else "#e74c3c")

                    st.markdown(f"<div class='stock-card' style='border-top: 6px solid {card_color};'><small>{item_cat}</small><h3>{it}</h3><p>المباع: {int(sold)} | المتبقي: {int(data['كمية'])}</p><h4>{data['بيع']} ₪</h4></div>", unsafe_allow_html=True)

                    with st.expander(f"⚙️ جرد {it}"):

                        new_q = st.number_input("الكمية الفعلية", value=None, key=f"inv_q_{it}", placeholder="الرقم الجديد...")

                        if st.button("تحديث", key=f"inv_btn_{it}"):

                            if new_q is not None:

                                st.session_state.inventory[it]['كمية'] = new_q; st.session_state.inventory[it]['أصلي'] = new_q

                                sync_to_google(); st.rerun()

                display_idx += 1

    else: st.info("المخزن فارغ.")



elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقرير المالي الشامل - أبو عمر</h1>", unsafe_allow_html=True)
    
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

    total_original_cap = sum(v['شراء'] * v.get('أصلي', v['كمية']) for v in st.session_state.inventory.values())
    current_stock_cap = sum(v['شراء'] * v['كمية'] for v in st.session_state.inventory.values())

    t_sales = df_sales[df_sales['date'] == today]['amount'].sum()
    t_gross_profit = df_sales[df_sales['date'] == today]['profit'].sum()
    t_exp = df_exp[df_exp['date'] == today]['amount'].sum() if not df_exp.empty else 0
    t_waste = df_waste[df_waste['date'] == today]['loss_value'].sum() if not df_waste.empty else 0
    t_net_profit = t_gross_profit - t_exp - t_waste

    w_sales = df_sales[df_sales['date'] >= last_7_days]['amount'].sum()
    w_gross_profit = df_sales[df_sales['date'] >= last_7_days]['profit'].sum()
    w_exp = df_exp[df_exp['date'] >= last_7_days]['amount'].sum() if not df_exp.empty else 0
    w_waste = df_waste[df_waste['date'] >= last_7_days]['loss_value'].sum() if not df_waste.empty else 0
    w_net_profit = w_gross_profit - w_exp - w_waste

    st.markdown("### 🏦 حالة رأس المال (المخزن)")
    col_cap1, col_cap2 = st.columns(2)
    with col_cap1:
        st.markdown(f"<div style='background: #2c3e50; padding: 20px; border-radius: 15px; color: white; text-align: center;'><p style='margin:0;'>إجمالي رأس المال الأصلي</p><h2 style='margin:0;'>{format_num(total_original_cap)} ₪</h2></div>", unsafe_allow_html=True)
    with col_cap2:
        st.markdown(f"<div style='background: #34495e; padding: 20px; border-radius: 15px; color: white; text-align: center;'><p style='margin:0;'>رأس المال المتوفر حالياً</p><h2 style='margin:0;'>{format_num(current_stock_cap)} ₪</h2></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💰 تقرير الأرباح والمبيعات الصافية")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='background: linear-gradient(135deg, #27ae60, #2ecc71); padding: 20px; border-radius: 15px; color: white; text-align: center;'><p style='margin:0;'>مبيعات اليوم</p><h2 style='margin:0;'>{format_num(t_sales)} ₪</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='background: linear-gradient(135deg, #2980b9, #3498db); padding: 20px; border-radius: 15px; color: white; text-align: center;'><p style='margin:0;'>صافي ربح اليوم</p><h2 style='margin:0;'>{format_num(t_net_profit)} ₪</h2></div>", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"<div style='background: linear-gradient(135deg, #8e44ad, #9b59b6); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-top:15px;'><p style='margin:0;'>مبيعات الأسبوع</p><h2 style='margin:0;'>{format_num(w_sales)} ₪</h2></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div style='background: linear-gradient(135deg, #f39c12, #f1c40f); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-top:15px;'><p style='margin:0;'>صافي ربح الأسبوع</p><h2 style='margin:0;'>{format_num(w_net_profit)} ₪</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
elif menu == "💸 المصروفات":

    st.markdown("<h1 class='main-title'>💸 إدارة وتحكم المصروفات</h1>", unsafe_allow_html=True)

    

    # 1. نموذج إضافة مصروف جديد

    with st.expander("➕ إضافة مصروف جديد", expanded=True):

        with st.form("new_exp_form"):

            col1, col2 = st.columns(2)

            reason = col1.text_input("البيان (صُرف في ماذا؟)")

            # تعديل: استخدام min_value=0 و step=1 لجعل الرقم صحيحاً

            amount = col2.number_input("المبلغ", min_value=0, step=1, value=None, placeholder="0")

            date_exp = st.date_input("التاريخ", datetime.now())

            if st.form_submit_button("حفظ المصروف"):

                if reason and amount is not None and amount > 0:

                    new_row = {'date': date_exp.strftime("%Y-%m-%d"), 'reason': reason, 'amount': amount}

                    st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_row])], ignore_index=True)

                    if sync_to_google():

                        st.success("✅ تم حفظ المصروف بنجاح")

                        st.rerun()

                else:

                    st.error("⚠️ يرجى إدخال البيان والمبلغ بشكل صحيح")



    st.markdown("---")

    

    # 2. عرض سجل المصروفات مع الحذف والتعديل

    if not st.session_state.expenses_df.empty:

        st.subheader("📋 سجل المصروفات المسجلة")

        

        df_display = st.session_state.expenses_df.copy()

        

        for index, row in df_display.iloc[::-1].iterrows():

            with st.container():

                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])

                c1.markdown(f"**📝 {row['reason']}**")

                

                # تعديل: تحويل المبلغ لـ int عند العرض لإخفاء الأصفار

                display_amt = int(row['amount']) if float(row['amount']).is_integer() else row['amount']

                c2.markdown(f"💰 {display_amt} ₪ | 📅 {row['date']}")

                

                if c3.button("📝 تعديل", key=f"edit_btn_{index}"):

                    st.session_state[f"edit_mode_{index}"] = True

                

                if c4.button("🗑️ حذف", key=f"del_btn_{index}"):

                    st.session_state.expenses_df = st.session_state.expenses_df.drop(index).reset_index(drop=True)

                    sync_to_google()

                    st.rerun()

                

                if st.session_state.get(f"edit_mode_{index}", False):

                    with st.form(f"edit_form_{index}"):

                        st.markdown(f"### تعديل: {row['reason']}")

                        edit_reason = st.text_input("البيان الجديد", value=row['reason'])

                        # تعديل: الرقم في الفورم يظهر كصحيح

                        edit_amount = st.number_input("المبلغ الجديد", min_value=0, step=1, value=int(row['amount']))

                        edit_date = st.text_input("التاريخ (YYYY-MM-DD)", value=row['date'])

                        

                        col_save, col_cancel = st.columns(2)

                        if col_save.form_submit_button("💾 حفظ التعديلات"):

                            st.session_state.expenses_df.at[index, 'reason'] = edit_reason

                            st.session_state.expenses_df.at[index, 'amount'] = edit_amount

                            st.session_state.expenses_df.at[index, 'date'] = edit_date

                            del st.session_state[f"edit_mode_{index}"]

                            sync_to_google()

                            st.rerun()

                        if col_cancel.form_submit_button("❌ إلغاء"):

                            del st.session_state[f"edit_mode_{index}"]

                            st.rerun()

                            

            st.markdown("<hr style='margin:5px 0; border-top:1px solid #eee;'>", unsafe_allow_html=True)

    else:

        st.info("لا توجد مصروفات مسجلة حالياً.")

elif menu == "⚙️ الإعدادات":

    st.markdown("<h1 class='main-title'>⚙️ إدارة البضاعة والمشتريات</h1>", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["📥 تزويد كمية", "✨ صنف جديد", "📂 إدارة الأقسام"])

    with t1:

        if st.session_state.inventory:

            with st.form("add_stock_form"):

                item_name = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))

                plus_q = st.number_input("الكمية المضافة", min_value=0.0, value=None, placeholder="اكتب الكمية...")

                if st.form_submit_button("إضافة"):

                    if plus_q is not None and plus_q > 0:

                        st.session_state.inventory[item_name]['كمية'] += plus_q

                        st.session_state.inventory[item_name]['أصلي'] = st.session_state.inventory[item_name]['كمية']

                        sync_to_google(); st.rerun()

    with t2:

        with st.form("add_form"):

            n = st.text_input("اسم الصنف")

            cat = st.selectbox("القسم", st.session_state.CATEGORIES)

            b = st.number_input("سعر الشراء", min_value=0.0, value=None)

            s = st.number_input("سعر البيع", min_value=0.0, value=None)

            q = st.number_input("الكمية", min_value=0.0, value=None)

            if st.form_submit_button("إضافة صنف جديد"):

                if n and b is not None and s is not None and q is not None:

                    st.session_state.inventory[n] = {'قسم': cat, 'شراء': b, 'بيع': s, 'كمية': q, 'أصلي': q}

                    sync_to_google(); st.success(f"تمت إضافة {n}!"); st.rerun()

    with t3:

        new_cat = st.text_input("اسم القسم")

        if st.button("حفظ القسم"):

            if new_cat and new_cat not in st.session_state.CATEGORIES:

                st.session_state.CATEGORIES.append(new_cat); st.success("تمت الإضافة"); st.rerun()
