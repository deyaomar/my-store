import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المحاسبي", layout="wide", page_icon="🍏")

# وظيفة لتحويل النص لرقم (تعالج الفاصلة والنقطة)
def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        processed = str(text).replace(',', '.').replace('،', '.')
        return float(processed)
    except:
        return 0.0

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
    st.session_state.sales_df = pd.read_csv(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method'])
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
    .stButton > button[kind="secondary"] { background-color: #ecf0f1 !important; color: #2c3e50 !important; height: 3.5em; width: 100%; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 25px; }
    
    .invoice-card { background-color: #ffffff; border: 2px solid #27ae60; border-radius: 15px; padding: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); color: #2c3e50; direction: rtl; }
    .total-line { font-size: 24px; font-weight: 900; color: #27ae60; text-align: center; border-top: 2px dashed #bdc3c7; padding-top: 15px; margin-top: 15px; }
    
    .report-card { background: #ffffff; padding: 20px; border-radius: 12px; border-right: 10px solid #2c3e50; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .profit-text { color: #27ae60; font-weight: bold; }
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
    menu = st.sidebar.radio("", ["🛒 شاشة البيع", "📦 إدارة المخزن", "📊 التقارير المالية"], label_visibility="collapsed")
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
                        with c4: val_txt = st.text_input("0", key=f"v_{item}", label_visibility="collapsed")
                        val = clean_num(val_txt)
                        if sel and val > 0:
                            q = val if mode == "كمية" else val / data["بيع"]
                            bill_items.append({"item": item, "qty": q, "amount": (val if mode == "شيكل" else val * data["بيع"]), "profit": (data["بيع"] - data["شراء"]) * q})

            if st.button("✅ تأكيد عملية البيع", use_container_width=True, type="primary"):
                if bill_items:
                    total_amt = sum(i['amount'] for i in bill_items)
                    inv_html = f'<div class="invoice-card"><div style="text-align:center;"><h2>🧾 فاتورة مبيعات</h2><p>{datetime.now().strftime("%Y-%m-%d %H:%M")} | {st.session_state.p_method}</p></div><table style="width:100%; text-align: right; border-bottom: 2px solid #eee;"><tr><th>الصنف</th><th>الكمية</th><th>السعر</th></tr>'
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        inv_html += f"<tr><td>{e['item']}</td><td>{e['qty']:.2f}</td><td>{e['amount']:.1f} ₪</td></tr>"
                        new_sale = pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method}])
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_sale], ignore_index=True)
                    inv_html += f'</table><div class="total-line">المبلغ الإجمالي: {total_amt:.1f} شيكل</div></div>'
                    st.session_state.last_report = inv_html; auto_save(); st.balloons(); st.rerun()

    # --- 2. إدارة المخزن ---
    elif menu == "📦 إدارة المخزن":
        st.markdown("<h1 class='main-title'>📦 تفاصيل المخزن والجرد</h1>", unsafe_allow_html=True)
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("add_form", clear_on_submit=True):
                n, c = st.text_input("اسم الصنف"), st.selectbox("القسم", st.session_state.categories)
                q_c, b_c, s_c = st.columns(3); qty, buy, sell = q_c.text_input("الكمية"), b_c.text_input("شراء"), s_c.text_input("بيع")
                if st.form_submit_button("حفظ"):
                    st.session_state.inventory[n] = {"كمية": clean_num(qty), "شراء": clean_num(buy), "بيع": clean_num(sell), "قسم": c}
                    auto_save(); st.rerun()
        if st.session_state.inventory:
            st.table(pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "المتبقي": f"{v['كمية']:.1f}", "شراء": f"{v['شراء']} ₪", "بيع": f"{v['بيع']} ₪"} for k, v in st.session_state.inventory.items()]))

    # --- 3. التقارير المالية (التحديث الجديد) ---
    elif menu == "📊 التقارير المالية":
        st.markdown("<h1 class='main-title'>📊 ملخص الأرباح والمبيعات</h1>", unsafe_allow_html=True)
        df = st.session_state.sales_df.copy()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            df_today = df[df['date'].dt.date == today]
            df_week = df[df['date'].dt.date >= week_ago]

            # صف تقارير اليوم
            st.subheader("📅 ملخص مبيعات اليوم")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"<div class='report-card'><h3>💰 مبيعات اليوم</h3><h2>{df_today['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='report-card'><h3>💵 كاش</h3><h2>{df_today[df_today['method']=='نقداً']['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='report-card'><h3>📱 تطبيق</h3><h2>{df_today[df_today['method']=='تطبيق']['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='report-card' style='border-right-color:#27ae60;'><h3>✅ ربح اليوم</h3><h2 class='profit-text'>{df_today['profit'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)

            # صف تقارير الأسبوع
            st.write("---")
            st.subheader("🗓️ ملخص مبيعات الأسبوع (آخر 7 أيام)")
            w1, w2 = st.columns(2)
            with w1: st.markdown(f"<div class='report-card'><h3>📈 إجمالي مبيعات الأسبوع</h3><h2>{df_week['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            with w2: st.markdown(f"<div class='report-card' style='border-right-color:#27ae60;'><h3>💸 صافي أرباح الأسبوع</h3><h2 class='profit-text'>{df_week['profit'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)

            st.write("### 📜 سجل العمليات المفصل:")
            st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
        else:
            st.info("لا يوجد بيانات مبيعات بعد.")
