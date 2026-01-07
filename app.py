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

# 3. إدارة ملفات البيانات (لكل فرع ملفاته الخاصة)
def load_data():
    # ملف المبيعات الإجمالي (يحتوي على خانة الفرع)
    if 'sales_df' not in st.session_state:
        if os.path.exists('sales_all_branches.csv'):
            st.session_state.sales_df = pd.read_csv('sales_all_branches.csv')
        else:
            st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch'])

    # ملف المصاريف الإجمالي
    if 'expenses_df' not in st.session_state:
        st.session_state.expenses_df = pd.read_csv('expenses_all.csv') if os.path.exists('expenses_all.csv') else pd.DataFrame(columns=['date', 'reason', 'amount', 'branch'])

    # ملف المخازن (مقسم حسب الفرع)
    if 'inventory' not in st.session_state:
        if os.path.exists('inventory_all.csv'):
            df_inv = pd.read_csv('inventory_all.csv')
            st.session_state.inventory = df_inv.to_dict('records')
        else:
            st.session_state.inventory = [] # قائمة تحتوي على قواميس {item, branch, qty, buy, sell, cat}

load_data()

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_all.csv', index=False)
    st.session_state.sales_df.to_csv('sales_all_branches.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_all.csv', index=False)

# 4. واجهة المستخدم والتنسيق
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .metric-box { background-color: #ffffff; border-right: 8px solid #27ae60; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px; }
    .branch-tag { background: #27ae60; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 5. نظام تسجيل الدخول واختيار الفرع
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🏢 بوابة إدارة فروع أبو عمر</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    user_type = col1.selectbox("نوع الحساب", ["مسؤول فرع", "أبو عمر (المدير العام)"])
    if user_type == "مسؤول فرع":
        branch_choice = col2.selectbox("اختر الفرع المسجل به", BRANCHES)
    pwd = st.text_input("كلمة المرور", type="password")
    
    if st.button("دخول النظام"):
        if (user_type == "أبو عمر (المدير العام)" and pwd == "admin") or (user_type == "مسؤول فرع" and pwd == "123"):
            st.session_state.logged_in = True
            st.session_state.user_role = user_type
            st.session_state.my_branch = branch_choice if user_type == "مسؤول فرع" else "الكل"
            st.rerun()
else:
    # شريط جانبي مخصص
    st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.user_role}</div>", unsafe_allow_html=True)
    if st.session_state.user_role == "أبو عمر (المدير العام)":
        active_branch = st.sidebar.selectbox("🏠 استعراض فرع:", ["الكل"] + BRANCHES)
    else:
        active_branch = st.session_state.my_branch
        st.sidebar.info(f"📍 أنت تعمل في: {active_branch}")

    menu = st.sidebar.radio("التنقل", ["🛒 نقطة البيع", "📦 المخزن", "💸 المصروفات", "📊 التقارير", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        if active_branch == "الكل":
            st.warning("يرجى اختيار فرع محدد من القائمة الجانبية للبيع")
        else:
            st.markdown(f"<h1 class='main-title'>🛒 بيع - {active_branch}</h1>", unsafe_allow_html=True)
            # عرض أصناف الفرع المختار فقط
            branch_inv = [i for i in st.session_state.inventory if i['branch'] == active_branch]
            if not branch_inv:
                st.info("لا توجد أصناف في هذا الفرع. أضف أصناف من الإعدادات.")
            else:
                search = st.text_input("🔍 بحث في الفرع...")
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
                
                if st.button("🚀 إتمام البيع"):
                    b_id = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        # تحديث الكمية في المخزن العام
                        for inv_item in st.session_state.inventory:
                            if inv_item['item'] == e['item'] and inv_item['branch'] == active_branch:
                                inv_item['qty'] -= e['qty']
                        
                        new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': 'نقدي', 'branch': active_branch, 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                    auto_save(); st.success("تمت عملية البيع"); st.rerun()

    # --- 2. المخزن ---
    elif menu == "📦 المخزن":
        st.markdown(f"<h1 class='main-title'>📦 مخزن {active_branch}</h1>", unsafe_allow_html=True)
        df_inv = pd.DataFrame(st.session_state.inventory)
        if active_branch != "الكل":
            df_inv = df_inv[df_inv['branch'] == active_branch]
        st.dataframe(df_inv, use_container_width=True)

    # --- 3. التقارير (التعديل الجوهري) ---
    elif menu == "📊 التقارير":
        st.markdown(f"<h1 class='main-title'>📊 تقارير: {active_branch}</h1>", unsafe_allow_html=True)
        
        # تصفية البيانات حسب الفرع المختار
        sales = st.session_state.sales_df.copy()
        exps = st.session_state.expenses_df.copy()
        if active_branch != "الكل":
            sales = sales[sales['branch'] == active_branch]
            exps = exps[exps['branch'] == active_branch]
        
        sales['date_dt'] = pd.to_datetime(sales['date'])
        today = datetime.now().date()

        # أرقام سريعة
        d_sales = sales[sales['date_dt'].dt.date == today]
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-box'><div>مبيعات اليوم</div><div class='metric-value'>{format_num(d_sales['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'><div>أرباح اليوم</div><div class='metric-value'>{format_num(d_sales['profit'].sum())} ₪</div></div>", unsafe_allow_html=True)
        
        # حساب رأس المال للفرع/الفروع
        inv_df = pd.DataFrame(st.session_state.inventory)
        if active_branch != "الكل":
            inv_df = inv_df[inv_df['branch'] == active_branch]
        capital = (inv_df['buy'] * inv_df['qty']).sum()
        c3.markdown(f"<div class='metric-box' style='border-color:#e67e22'><div>رأس مال البضاعة</div><div class='metric-value'>{format_num(capital)} ₪</div></div>", unsafe_allow_html=True)

        if active_branch == "الكل":
            st.markdown("### 🏢 مقارنة أداء الفروع (مبيعات اليوم)")
            branch_comp = sales[sales['date_dt'].dt.date == today].groupby('branch')['amount'].sum().reset_index()
            st.bar_chart(branch_comp.set_index('branch'))

    # --- 4. الإعدادات (توزيع البضاعة) ---
    elif menu == "⚙️ الإعدادات":
        if st.session_state.user_role != "أبو عمر (المدير العام)":
            st.error("هذه الصفحة للمدير العام فقط")
        else:
            st.markdown("<h1 class='main-title'>⚙️ إدارة بضاعة الفروع</h1>", unsafe_allow_html=True)
            with st.form("add_item_branch"):
                col1, col2, col3 = st.columns(3)
                name = col1.text_input("اسم الصنف")
                br = col2.selectbox("يُضاف لفرع:", BRANCHES)
                qty = col3.number_input("الكمية المضافة", min_value=0.0)
                buy = col1.number_input("سعر الشراء", min_value=0.0)
                sell = col2.number_input("سعر البيع", min_value=0.0)
                if st.form_submit_button("إضافة الصنف للفرع"):
                    new_item = {'item': name, 'branch': br, 'qty': qty, 'buy': buy, 'sell': sell}
                    st.session_state.inventory.append(new_item)
                    auto_save(); st.success(f"تمت إضافة {name} إلى {br}"); st.rerun()
                
