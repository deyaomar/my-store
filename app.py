import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المحاسبي", layout="wide", page_icon="🍏")

# وظيفة لتحويل النص لرقم
def clean_num(text):
    try:
        if text is None or text == "": return None
        processed = str(text).replace(',', '.').replace('،', '.')
        return float(processed)
    except:
        return None

# 2. ملفات البيانات
DB_FILE = 'inventory_final.csv'
SALES_FILE = 'sales_final.csv'
CATS_FILE = 'categories_final.csv'

def auto_save():
    pd.DataFrame(st.session_state.inventory).T.to_csv(DB_FILE)
    pd.DataFrame({'name': st.session_state.categories}).to_csv(CATS_FILE, index=False)
    st.session_state.sales_df.to_csv(SALES_FILE, index=False)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv(DB_FILE, index_col=0).to_dict('index') if os.path.exists(DB_FILE) else {}
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone'])
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv(CATS_FILE)['name'].tolist() if os.path.exists(CATS_FILE) else ["خضار وفواكه", "مكسرات"]

if 'last_report' not in st.session_state: st.session_state.last_report = None
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"

# 3. الهوية البصرية (CSS)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: 900 !important; font-size: 20px !important; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; color: white !important; height: 3.5em; width: 100%; font-weight: bold; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 25px; }
    .report-card { background: #ffffff; padding: 20px; border-radius: 12px; border-right: 10px solid #2c3e50; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; text-align: center; }
    .invoice-card { background: white; border: 2px solid #27ae60; padding: 20px; border-radius: 10px; color: #2c3e50; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 دخول نظام أبو عمر المحاسبي</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        pwd = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول للنظام"):
            if pwd == "123":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("غلط يا أبو عمر!")
else:
    st.sidebar.markdown("<h2 style='text-align:center;'>🍎 القائمة</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("", ["🛒 شاشة البيع", "📦 إدارة المخزن", "📋 عملية الجرد", "📊 التقارير المالية"], label_visibility="collapsed")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        if st.session_state.last_report:
            st.markdown(st.session_state.last_report, unsafe_allow_html=True)
            if st.button("➕ إنشاء فاتورة جديدة", type="primary"):
                st.session_state.last_report = None; st.rerun()
        else:
            cp1, cp2 = st.columns(2)
            with cp1:
                if st.button("📱 تطبيق", type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
                    st.session_state.p_method = "تطبيق"; st.rerun()
            with cp2:
                if st.button("💵 نـقـداً", type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
                    st.session_state.p_method = "نقداً"; st.rerun()
            
            # خانات بيانات الزبون إذا كان الدفع تطبيق
            cust_name = ""
            cust_phone = ""
            if st.session_state.p_method == "تطبيق":
                st.info("⚠️ الرجاء إدخال بيانات الزبون للبيع البنكي")
                cc1, cc2 = st.columns(2)
                cust_name = cc1.text_input("اسم الزبون")
                cust_phone = cc2.text_input("رقم الجوال")

            st.write("---")
            bill_items = []
            for cat in st.session_state.categories:
                with st.expander(f"📂 {cat}", expanded=True):
                    items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                    for item, data in items.items():
                        c1, c2, c3, c4 = st.columns([0.5, 2, 2, 2])
                        with c1: sel = st.checkbox("", key=f"s_{item}")
                        with c2: st.markdown(f"**{item}**"); st.caption(f"متوفر: {data['كمية']:.1f}")
                        with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
                        with c4: val_txt = st.text_input("0", key=f"v_{item}")
                        val = clean_num(val_txt)
                        if sel and val is not None and val > 0:
                            q = val if mode == "كمية" else val / data["بيع"]
                            bill_items.append({"item": item, "qty": q, "amount": (val if mode == "شيكل" else val * data["بيع"]), "profit": (data["بيع"] - data["شراء"]) * q})

            if st.button("✅ تأكيد عملية البيع", use_container_width=True, type="primary"):
                if bill_items:
                    if st.session_state.p_method == "تطبيق" and (cust_name == "" or cust_phone == ""):
                        st.error("يا أبو عمر، لازم تكتب اسم الزبون ورقم جواله عشان مبيعات التطبيق!")
                    else:
                        total_amt = sum(i['amount'] for i in bill_items)
                        inv_html = f'<div class="invoice-card"><div style="text-align:center;"><h2>🧾 فاتورة مبيعات</h2><p>{datetime.now().strftime("%Y-%m-%d %H:%M")} | {st.session_state.p_method}</p></div>'
                        if st.session_state.p_method == "تطبيق":
                            inv_html += f'<p style="text-align:right;">👤 <b>الزبون:</b> {cust_name} | 📱 {cust_phone}</p>'
                        
                        inv_html += '<table style="width:100%; text-align: right;"><tr><th>الصنف</th><th>الكمية</th><th>السعر</th></tr>'
                        for e in bill_items:
                            st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                            inv_html += f"<tr><td>{e['item']}</td><td>{e['qty']:.2f}</td><td>{e['amount']:.1f} ₪</td></tr>"
                            new_sale = pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': cust_name, 'customer_phone': cust_phone}])
                            st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_sale], ignore_index=True)
                        
                        inv_html += f'</table><hr><h3 style="text-align:center; color:#27ae60;">الإجمالي: {total_amt:.1f} شيكل</h3></div>'
                        st.session_state.last_report = inv_html; auto_save(); st.balloons(); st.rerun()

    # --- 2. إدارة المخزن ---
    elif menu == "📦 إدارة المخزن":
        st.markdown("<h1 class='main-title'>📦 تفاصيل المخزن</h1>", unsafe_allow_html=True)
        # (نفس كود المخزن السابق)
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("add_form", clear_on_submit=True):
                n, c = st.text_input("اسم الصنف"), st.selectbox("القسم", st.session_state.categories)
                q_c, b_c, s_c = st.columns(3); qty, buy, sell = q_c.text_input("الكمية"), b_c.text_input("شراء"), s_c.text_input("بيع")
                if st.form_submit_button("حفظ"):
                    st.session_state.inventory[n] = {"كمية": clean_num(qty) or 0.0, "شراء": clean_num(buy) or 0.0, "بيع": clean_num(sell) or 0.0, "قسم": c}
                    auto_save(); st.rerun()
        if st.session_state.inventory:
            st.table(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "المتبقي": f"{v['كمية']:.1f}", "شراء": f"{v['شراء']} ₪", "بيع": f"{v['بيع']} ₪"} for k, v in st.session_state.inventory.items()]))

    # --- 3. عملية الجرد ---
    elif menu == "📋 عملية الجرد":
        st.markdown("<h1 class='main-title'>📋 جرد المخزن اليدوي</h1>", unsafe_allow_html=True)
        jard_updates = {}
        with st.form("jard_form"):
            for cat in st.session_state.categories:
                st.markdown(f"### 📂 قسم {cat}")
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item, data in items.items():
                    c1, c2, c3 = st.columns([2, 1, 2])
                    c1.write(f"**{item}**"); c2.caption(f"الحالي: {data['كمية']:.1f}"); val = c3.text_input("الكمية الفعلية", key=f"j_{item}")
                    rv = clean_num(val)
                    if rv is not None: jard_updates[item] = rv
            if st.form_submit_button("✅ اعتماد الجرد وتحديث المخزن"):
                for item, new_val in jard_updates.items(): st.session_state.inventory[item]['كمية'] = new_val
                auto_save(); st.success("تم تحديث المخزن!"); st.rerun()

    # --- 4. التقارير المالية ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 ملخص الحسابات والمبيعات البنكية</h1>", unsafe_allow_html=True)
        df = st.session_state.sales_df.copy()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            date_range = st.sidebar.date_input("فترة التقرير", [datetime.now().date(), datetime.now().date()])
            
            if len(date_range) == 2:
                df_f = df[(df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])]
            else:
                df_f = df[df['date'].dt.date == date_range[0]]

            # عرض النتائج العامة
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='report-card'><h3>💰 مبيعات</h3><h2>{df_f['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='report-card'><h3>💵 كاش</h3><h2>{df_f[df_f['method']=='نقداً']['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='report-card'><h3>📱 تطبيق</h3><h2>{df_f[df_f['method']=='تطبيق']['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='report-card' style='border-right-color:#27ae60;'><h3>✅ صافي ربح</h3><h2>{df_f['profit'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            
            # قسم المبيعات البنكية (التطبيق)
            st.write("---")
            st.subheader("💳 سجل مبيعات التطبيق (البنكي)")
            df_bank = df_f[df_f['method'] == 'تطبيق'][['date', 'customer_name', 'customer_phone', 'item', 'amount']]
            if not df_bank.empty:
                df_bank.columns = ['التاريخ', 'اسم الزبون', 'رقم الجوال', 'الصنف', 'المبلغ']
                st.table(df_bank.sort_values(by='التاريخ', ascending=False))
            else:
                st.info("لا توجد مبيعات بنكية في هذه الفترة.")

            st.write("---")
            st.write("### 📜 السجل الشامل للفترة:")
            st.dataframe(df_f.sort_values(by='date', ascending=False), use_container_width=True)
        else:
            st.info("لا يوجد بيانات مبيعات.")
