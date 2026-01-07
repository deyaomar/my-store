import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام إدارة فروع أبو عمر 2026", layout="wide", page_icon="🏢")

def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

def clean_num(text):
    try:
        if text is None or text == "": return 0.0
        return float(str(text).replace(',', '.').replace('،', '.'))
    except: return 0.0

# 2. تعريف الفروع
BRANCHES = ["فرع 1", "فرع 2", "فرع 3"]

# 3. إدارة ملفات البيانات
def load_data():
    if 'sales_df' not in st.session_state:
        if os.path.exists('sales_all_branches.csv'):
            st.session_state.sales_df = pd.read_csv('sales_all_branches.csv')
        else:
            st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch'])

    if 'expenses_df' not in st.session_state:
        st.session_state.expenses_df = pd.read_csv('expenses_all.csv') if os.path.exists('expenses_all.csv') else pd.DataFrame(columns=['date', 'reason', 'amount', 'branch'])

    if 'inventory' not in st.session_state:
        if os.path.exists('inventory_all.csv'):
            df_inv = pd.read_csv('inventory_all.csv')
            st.session_state.inventory = df_inv.to_dict('records')
        else:
            st.session_state.inventory = []

load_data()

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_all.csv', index=False)
    st.session_state.sales_df.to_csv('sales_all_branches.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_all.csv', index=False)

# 4. واجهة المستخدم والتنسيق
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 15px; margin-bottom: 20px;}
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .metric-box { background-color: #ffffff; border-right: 8px solid #27ae60; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px; }
    .metric-value { font-size: 22px; font-weight: 900; color: #2c3e50; }
    .section-header { background: #f1f4f6; padding: 10px; border-radius: 10px; font-weight: 900; border-right: 5px solid #27ae60; margin: 15px 0; }
    </style>
    """, unsafe_allow_html=True)

# 5. نظام تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🏢 بوابة إدارة فروع أبو عمر</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    user_type = col1.selectbox("نوع الحساب", ["مسؤول فرع", "أبو عمر (المدير العام)"])
    branch_choice = "الكل"
    if user_type == "مسؤول فرع":
        branch_choice = col2.selectbox("اختر الفرع المسجل به", BRANCHES)
    
    pwd = st.text_input("كلمة المرور", type="password")
    
    if st.button("دخول النظام"):
        if (user_type == "أبو عمر (المدير العام)" and pwd == "admin") or (user_type == "مسؤول فرع" and pwd == "123"):
            st.session_state.logged_in = True
            st.session_state.user_role = user_type
            st.session_state.my_branch = branch_choice
            st.rerun()
        else:
            st.error("كلمة المرور غير صحيحة")
else:
    # تم حل المشكلة هنا بإضافة التحقق
    user_role = st.session_state.get('user_role', 'بائع')
    my_branch = st.session_state.get('my_branch', 'غير محدد')

    st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {user_role}</div>", unsafe_allow_html=True)
    
    if user_role == "أبو عمر (المدير العام)":
        active_branch = st.sidebar.selectbox("🏠 استعراض فرع:", ["الكل"] + BRANCHES)
    else:
        active_branch = my_branch
        st.sidebar.info(f"📍 فرعك: {active_branch}")

    menu = st.sidebar.radio("التنقل", ["🛒 نقطة البيع", "📦 المخزن", "📊 التقارير", "💸 المصروفات", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        if active_branch == "الكل":
            st.warning("⚠️ يرجى اختيار فرع محدد من القائمة الجانبية للبيع")
        else:
            st.markdown(f"<h1 class='main-title'>🛒 بيع - {active_branch}</h1>", unsafe_allow_html=True)
            branch_inv = [i for i in st.session_state.inventory if i['branch'] == active_branch]
            if not branch_inv:
                st.info("لا توجد بضاعة في هذا الفرع حالياً.")
            else:
                search = st.text_input("🔍 بحث عن صنف...")
                bill_items = []
                for item in branch_inv:
                    if search.lower() in item['item'].lower():
                        c1, c2, c3 = st.columns([2,1,2])
                        c1.markdown(f"**{item['item']}**\n<small>متوفر: {format_num(item['qty'])}</small>", unsafe_allow_html=True)
                        mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item['item']}_{active_branch}", horizontal=True)
                        val = clean_num(c3.text_input("المقدار", key=f"v_{item['item']}_{active_branch}"))
                        if val > 0:
                            qty = val if mode == "كجم" else val / item['sell']
                            bill_items.append({"item": item['item'], "qty": qty, "amount": val if mode == "₪" else val * item['sell'], "profit": (item['sell'] - item['buy']) * qty})
                
                if st.button("🚀 إتمام البيع") and bill_items:
                    b_id = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        for inv_item in st.session_state.inventory:
                            if inv_item['item'] == e['item'] and inv_item['branch'] == active_branch:
                                inv_item['qty'] -= e['qty']
                        new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': 'نقدي', 'branch': active_branch, 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                    auto_save(); st.success("✅ تم البيع بنجاح"); st.rerun()

    # --- 2. المخزن ---
    elif menu == "📦 المخزن":
        st.markdown(f"<h1 class='main-title'>📦 بضاعة {active_branch}</h1>", unsafe_allow_html=True)
        if st.session_state.inventory:
            df_inv = pd.DataFrame(st.session_state.inventory)
            if active_branch != "الكل":
                df_inv = df_inv[df_inv['branch'] == active_branch]
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
        else:
            st.info("المخزن فارغ.")

    # --- 3. التقارير المالية ---
    elif menu == "📊 التقارير":
        st.markdown(f"<h1 class='main-title'>📊 تقارير مبيعات: {active_branch}</h1>", unsafe_allow_html=True)
        sales = st.session_state.sales_df.copy()
        if active_branch != "الكل":
            sales = sales[sales['branch'] == active_branch]
        
        if not sales.empty:
            sales['date_dt'] = pd.to_datetime(sales['date'])
            today = datetime.now().date()
            d_sales = sales[sales['date_dt'].dt.date == today]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-box'><div>مبيعات اليوم</div><div class='metric-value'>{format_num(d_sales['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-box'><div>أرباح اليوم</div><div class='metric-value'>{format_num(d_sales['profit'].sum())} ₪</div></div>", unsafe_allow_html=True)
            
            inv_df = pd.DataFrame(st.session_state.inventory)
            if active_branch != "الكل" and not inv_df.empty:
                inv_df = inv_df[inv_df['branch'] == active_branch]
            
            cap_val = (inv_df['buy'] * inv_df['qty']).sum() if not inv_df.empty else 0
            with c3: st.markdown(f"<div class='metric-box' style='border-color:#e67e22'><div>رأس مال البضاعة</div><div class='metric-value'>{format_num(cap_val)} ₪</div></div>", unsafe_allow_html=True)
            
            st.markdown("<div class='section-header'>تفاصيل مبيعات اليوم</div>", unsafe_allow_html=True)
            st.table(d_sales.groupby('item').agg({'amount':'sum', 'profit':'sum'}).reset_index())
        else:
            st.info("لا توجد مبيعات مسجلة لهذا النطاق.")

    # --- 4. المصروفات ---
    elif menu == "💸 المصروفات":
        st.markdown(f"<h1 class='main-title'>💸 مصروفات {active_branch}</h1>", unsafe_allow_html=True)
        with st.form("exp"):
            r = st.text_input("السبب"); a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ المصروف"):
                new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': active_branch if active_branch != "الكل" else "عام"}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
                auto_save(); st.rerun()
        st.dataframe(st.session_state.expenses_df, use_container_width=True)

    # --- 5. الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        if user_role != "أبو عمر (المدير العام)":
            st.error("⚠️ عذراً، هذه الصلاحية للمدير العام فقط.")
        else:
            st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف والفروع</h1>", unsafe_allow_html=True)
            with st.form("add_item"):
                c1, c2, c3 = st.columns(3)
                name = c1.text_input("اسم الصنف")
                br = c2.selectbox("الفرع", BRANCHES)
                q = c3.number_input("الكمية", min_value=0.0)
                b = c1.number_input("سعر الشراء", min_value=0.0)
                s = c2.number_input("سعر البيع", min_value=0.0)
                if st.form_submit_button("إضافة للمخزن"):
                    st.session_state.inventory.append({'item': name, 'branch': br, 'qty': q, 'buy': b, 'sell': s})
                    auto_save(); st.success(f"تمت إضافة {name} لـ {br}"); st.rerun()
