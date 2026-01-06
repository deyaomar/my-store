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

# 3. التنسيق (CSS)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; }
    [data-testid="stSidebar"] * { color: white !important; font-weight: 900 !important; font-size: 20px !important; }
    .stButton > button[kind="primary"] { background-color: #27ae60 !important; color: white !important; height: 3.5em; width: 100%; font-weight: bold; }
    .stButton > button[kind="secondary"] { background-color: #ecf0f1 !important; color: #2c3e50 !important; height: 3.5em; width: 100%; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 25px; }
    .success-box { background-color: #d4edda; border-right: 12px solid #28a745; padding: 20px; border-radius: 8px; color: #155724; margin-bottom: 25px; }
    .report-card { background: #f8f9fa; padding: 15px; border-radius: 10px; border-right: 8px solid #2c3e50; text-align: center; margin-bottom: 10px; }
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
    menu = st.sidebar.radio("", ["🛒 شاشة البيع", "📦 إدارة المخزن", "📊 التقارير"], label_visibility="collapsed")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 فاتورة البيع</h1>", unsafe_allow_html=True)
        if st.session_state.last_report:
            st.markdown(f"<div class='success-box'>{st.session_state.last_report}</div>", unsafe_allow_html=True)
            if st.button("➕ فاتورة جديدة"):
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
                    res_table = f"### ✅ تم تأكيد الفاتورة ({st.session_state.p_method})\n| الصنف | الكمية | السعر | المتبقي |\n| :--- | :--- | :--- | :--- |\n"
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        rem = st.session_state.inventory[e["item"]]["كمية"]
                        res_table += f"| {e['item']} | {e['qty']:.2f} | {e['amount']:.1f} | **{rem:.1f}** |\n"
                        new_sale = pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method}])
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, new_sale], ignore_index=True)
                    res_table += f"\n\n ### 💰 الإجمالي: {total_amt:.1f} شيكل"
                    st.session_state.last_report = res_table; auto_save(); st.balloons(); st.rerun()

    # --- 2. إدارة المخزن (تعديل نظام الجدول) ---
    elif menu == "📦 إدارة المخزن":
        st.markdown("<h1 class='main-title'>📦 تفاصيل المخزن والجرد</h1>", unsafe_allow_html=True)
        
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("اسم الصنف")
                c = st.selectbox("القسم", st.session_state.categories)
                q_c, b_c, s_c = st.columns(3)
                qty = q_c.text_input("الكمية (كيلو/عدد)")
                buy = b_c.text_input("سعر الشراء")
                sell = s_c.text_input("سعر البيع")
                if st.form_submit_button("حفظ"):
                    st.session_state.inventory[n] = {"كمية": clean_num(qty), "شراء": clean_num(buy), "بيع": clean_num(sell), "قسم": c}
                    auto_save(); st.rerun()

        # عرض المخزن بنظام جدول تفصيلي
        if st.session_state.inventory:
            inv_data = []
            for item, data in st.session_state.inventory.items():
                inv_data.append({
                    "الصنف": item,
                    "القسم": data.get('قسم', '-'),
                    "الكمية الكلية": f"{data['كمية']:.1f}",
                    "سعر الشراء": f"{data['شراء']:.1f} ₪",
                    "سعر البيع": f"{data['بيع']:.1f} ₪",
                    "المتبقي في المخزن": f"{data['كمية']:.1f}"
                })
            
            df_inv = pd.DataFrame(inv_data)
            st.table(df_inv) # عرض الجدول بشكل ثابت وواضح
            
            st.write("---")
            st.write("### 🛠️ عمليات سريعة (تعديل/حذف):")
            for item in list(st.session_state.inventory.keys()):
                col_i, col_e, col_d = st.columns([3, 1, 1])
                col_i.write(f"**{item}**")
                if col_e.button("📝 تعديل", key=f"edit_{item}"): st.session_state.editing = item
                if col_d.button("🗑️ حذف", key=f"del_{item}"):
                    del st.session_state.inventory[item]; auto_save(); st.rerun()
            
            if 'editing' in st.session_state:
                t = st.session_state.editing
                st.info(f"تعديل بيانات: {t}")
                eq = st.text_input("الكمية الجديدة", value=str(st.session_state.inventory[t]["كمية"]))
                es = st.text_input("سعر البيع الجديد", value=str(st.session_state.inventory[t]["بيع"]))
                if st.button("تحديث"):
                    st.session_state.inventory[t]["كمية"] = clean_num(eq)
                    st.session_state.inventory[t]["بيع"] = clean_num(es)
                    del st.session_state.editing; auto_save(); st.rerun()

    # --- 3. التقارير ---
    elif menu == "📊 التقارير":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
        df = st.session_state.sales_df.copy()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            today = datetime.now().date()
            df_t = df[df['date'].dt.date == today]
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='report-card'><h3>💰 مبيعات اليوم</h3><h2>{df_t['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='report-card'><h3>💵 كاش</h3><h2>{df_t[df_t['method']=='نقداً']['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='report-card'><h3>📱 تطبيق</h3><h2>{df_t[df_t['method']=='تطبيق']['amount'].sum():.1f} ₪</h2></div>", unsafe_allow_html=True)
            st.write("---")
            st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
