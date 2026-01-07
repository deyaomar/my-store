import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# --- 1. الإعدادات العامة والتنسيق ---
st.set_page_config(page_title="نظام أبو عمر للمحاسبة 2026", layout="wide", page_icon="🍏")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #27ae60; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .main-header { background-color: #2c3e50; color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 2rem; border-bottom: 5px solid #27ae60; }
    .card { background-color: #f8f9fa; border-right: 6px solid #27ae60; padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; background-color: #27ae60; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة البيانات ---
def safe_num(v):
    try: return float(str(v).replace(',', '.').replace('،', '.')) if v else 0.0
    except: return 0.0

def load_data(file, cols):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            for col in cols:
                if col not in df.columns: df[col] = 0
            return df
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

FILES = {
    'sales': ('sales_v4.csv', ['التاريخ', 'الصنف', 'المبلغ', 'الربح', 'الطريقة', 'الزبون', 'رقم_الفاتورة']),
    'exp': ('exp_v4.csv', ['التاريخ', 'البيان', 'المبلغ']),
    'inv': ('inv_v4.csv', ['صنف', 'قسم', 'شراء', 'بيع', 'كمية']),
    'adj': ('adj_v4.csv', ['التاريخ', 'الصنف', 'الفارق_الوزني', 'الفارق_المالي'])
}

if 'db' not in st.session_state:
    st.session_state.db = {k: load_data(v[0], v[1]) for k, v in FILES.items()}
    st.session_state.cats = pd.read_csv('cats.csv')['name'].tolist() if os.path.exists('cats.csv') else ["خضار وفواكه", "مكسرات"]

def save_db():
    for k, v in FILES.items():
        st.session_state.db[k].to_csv(v[0], index=False)
    pd.DataFrame(st.session_state.cats, columns=['name']).to_csv('cats.csv', index=False)

# --- 3. نظام الدخول ---
if 'auth' not in st.session_state:
    st.markdown("<div class='main-header'><h1>🔐 تسجيل دخول نظام أبو عمر</h1></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1,1])
    with col:
        pwd = st.text_input("كلمة المرور الإدارية", type="password")
        if st.button("دخول"):
            if pwd == "123": st.session_state.auth = True; st.rerun()
            else: st.error("خطأ في كلمة المرور")
else:
    # --- 4. القائمة الجانبية ---
    st.sidebar.markdown("<h2 style='text-align:center;'>أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("التنقل:", ["🛒 نقطة البيع", "📊 التقارير", "⚖️ تنفيذ جرد", "📦 المخزن", "💸 المصروفات", "⚙️ الإعدادات"])

    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 🛒 1. نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<div class='main-header'><h1>🛒 شاشة البيع المباشر</h1></div>", unsafe_allow_html=True)
        c_p1, c_p2 = st.columns([3, 1])
        with c_p2:
            method = st.radio("طريقة الدفع", ["نقداً", "تطبيق"], horizontal=True)
            cust = st.text_input("اسم الزبون", "زبون عام")
        with c_p1:
            search = st.text_input("🔍 ابحث عن صنف...")
            
        cart = []
        inv_df = st.session_state.db['inv']
        display_items = inv_df[inv_df['صنف'].str.contains(search, na=False)] if search else inv_df
        
        for idx, row in display_items.iterrows():
            with st.container():
                col_n, col_u, col_v = st.columns([2, 1, 1])
                col_n.markdown(f"<div class='card'><b>{row['صنف']}</b><br><small>المخزن: {row['كمية']} | السعر: {row['بيع']}</small></div>", unsafe_allow_html=True)
                unit = col_u.radio("بـ", ["شيكل", "وزن"], key=f"u_{idx}", horizontal=True)
                val = safe_num(col_v.text_input("المقدار", key=f"v_{idx}", label_visibility="collapsed"))
                if val > 0:
                    qty = val if unit == "وزن" else val / row['بيع']
                    cart.append({'idx': idx, 'صنف': row['صنف'], 'كمية': qty, 'مبلغ': val if unit == "شيكل" else val * row['بيع'], 'ربح': (row['بيع']-row['شراء'])*qty})

        if st.button("💾 إتمام العملية", type="primary"):
            if cart:
                bill_id = str(uuid.uuid4())[:8]
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                for item in cart:
                    st.session_state.db['inv'].at[item['idx'], 'كمية'] -= item['كمية']
                    new_s = {'التاريخ': now, 'الصنف': item['صنف'], 'المبلغ': item['مبلغ'], 'الربح': item['ربح'], 'الطريقة': method, 'الزبون': cust, 'رقم_الفاتورة': bill_id}
                    st.session_state.db['sales'] = pd.concat([st.session_state.db['sales'], pd.DataFrame([new_s])], ignore_index=True)
                save_db(); st.success("✅ تم الحفظ!"); st.rerun()

    # --- 📊 2. التقارير ---
    elif menu == "📊 التقارير":
        st.markdown("<div class='main-header'><h1>📊 كشف الأرباح والمبيعات</h1></div>", unsafe_allow_html=True)
        t_type = st.selectbox("فترة التقرير", ["اليوم", "آخر 7 أيام", "تاريخ مخصص"])
        start_d = datetime.now().date()
        end_d = datetime.now().date()
        if t_type == "آخر 7 أيام": start_d -= timedelta(days=7)
        elif t_type == "تاريخ مخصص":
            c1, c2 = st.columns(2)
            start_d = c1.date_input("من", start_d - timedelta(days=30))
            end_d = c2.date_input("إلى", datetime.now().date())

        def filter_date(df):
            if df.empty: return df
            df['date_dt'] = pd.to_datetime(df['التاريخ']).dt.date
            return df[(df['date_dt'] >= start_d) & (df['date_dt'] <= end_d)]

        s_f = filter_date(st.session_state.db['sales'])
        e_f = filter_date(st.session_state.db['exp'])
        a_f = filter_date(st.session_state.db['adj'])

        rev, prof, exps = s_f['المبلغ'].sum(), s_f['الربح'].sum(), e_f['المبلغ'].sum()
        adj_loss = a_f['الفارق_المالي'].sum()
        net = prof - exps - adj_loss

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("المبيعات", f"{rev:,.1f} ₪")
        m2.metric("المصروفات", f"{exps:,.1f} ₪")
        m3.metric("خسائر الجرد", f"{adj_loss:,.1f} ₪")
        m4.metric("صافي الربح", f"{net:,.1f} ₪")
        st.dataframe(s_f[['التاريخ', 'الصنف', 'المبلغ', 'الطريقة', 'الزبون']], use_container_width=True)

    # --- ⚖️ 3. تنفيذ جرد ---
    elif menu == "⚖️ تنفيذ جرد":
        st.markdown("<div class='main-header'><h1>⚖️ مطابقة الجرد الفعلي</h1></div>", unsafe_allow_html=True)
        j_data = []
        for idx, row in st.session_state.db['inv'].iterrows():
            cc1, cc2, cc3 = st.columns([2,1,2])
            cc1.write(f"**{row['صنف']}**")
            cc2.info(f"نظام: {row['كمية']}")
            real_v = cc3.text_input("أدخل الوزن الحقيقي", key=f"j_{idx}")
            if real_v:
                diff = row['كمية'] - safe_num(real_v)
                if diff != 0: j_data.append({'idx': idx, 'صنف': row['صنف'], 'فرق': diff, 'خسارة': diff * row['شراء'], 'new': safe_num(real_v)})
        
        if st.button("💾 اعتماد الجرد", type="primary"):
            now = datetime.now().strftime("%Y-%m-%d")
            for d in j_data:
                st.session_state.db['inv'].at[d['idx'], 'كمية'] = d['new']
                new_adj = {'التاريخ': now, 'الصنف': d['صنف'], 'الفارق_الوزني': d['فرق'], 'الفارق_المالي': d['خسارة']}
                st.session_state.db['adj'] = pd.concat([st.session_state.db['adj'], pd.DataFrame([new_adj])], ignore_index=True)
            save_db(); st.success("تم التحديث!"); st.rerun()

    # باقي الأقسام (المخزن، المصروفات، الإعدادات) تتبع نفس النمط المستقر...
    elif menu == "📦 المخزن":
        st.markdown("<div class='main-header'><h1>📦 رصيد المخزن</h1></div>", unsafe_allow_html=True)
        st.dataframe(st.session_state.db['inv'], use_container_width=True)
    
    elif menu == "💸 المصروفات":
        st.markdown("<div class='main-header'><h1>💸 تسجيل مصروف</h1></div>", unsafe_allow_html=True)
        with st.form("exp_f"):
            reason = st.text_input("البيان")
            amt = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                new_e = {'التاريخ': datetime.now().strftime("%Y-%m-%d"), 'البيان': reason, 'المبلغ': amt}
                st.session_state.db['exp'] = pd.concat([st.session_state.db['exp'], pd.DataFrame([new_e])], ignore_index=True)
                save_db(); st.rerun()

    elif menu == "⚙️ الإعدادات":
        st.markdown("<div class='main-header'><h1>⚙️ إدارة الأصناف</h1></div>", unsafe_allow_html=True)
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("add_i"):
                name = st.text_input("اسم الصنف")
                cat = st.selectbox("القسم", st.session_state.cats)
                c1, c2, c3 = st.columns(3)
                b = c1.text_input("شراء")
                s = c2.text_input("بيع")
                q = c3.text_input("كمية")
                if st.form_submit_button("حفظ"):
                    new_item = {'صنف': name, 'قسم': cat, 'شراء': safe_num(b), 'بيع': safe_num(s), 'كمية': safe_num(q)}
                    st.session_state.db['inv'] = pd.concat([st.session_state.db['inv'], pd.DataFrame([new_item])], ignore_index=True)
                    save_db(); st.rerun()
