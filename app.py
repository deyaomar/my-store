import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة الأصلية
st.set_page_config(page_title="نظام إدارة فروع أبو عمر", layout="wide", page_icon="🏢")

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

# 2. إدارة قواعد البيانات (المحلات، المستخدمين، البضاعة، المبيعات)
def load_data():
    # ملف الفروع والمستخدمين
    if 'branches_db' not in st.session_state:
        if os.path.exists('branches_config.csv'):
            st.session_state.branches_db = pd.read_csv('branches_config.csv')
        else:
            # افتراضياً عند أول تشغيل
            st.session_state.branches_db = pd.DataFrame([
                {'branch_name': 'المحل الأول', 'user_name': 'user1', 'password': '123'}
            ])
    
    if 'sales_df' not in st.session_state:
        st.session_state.sales_df = pd.read_csv('sales_vFinal.csv') if os.path.exists('sales_vFinal.csv') else pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'branch', 'cat'])
    
    if 'inventory' not in st.session_state:
        if os.path.exists('inventory_vFinal.csv'):
            st.session_state.inventory = pd.read_csv('inventory_vFinal.csv').to_dict('records')
        else:
            st.session_state.inventory = []

def save_all():
    st.session_state.branches_db.to_csv('branches_config.csv', index=False)
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_vFinal.csv', index=False)
    st.session_state.sales_df.to_csv('sales_vFinal.csv', index=False)

load_data()

# 3. التنسيق (الستايل الأصلي)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; border-left: 1px solid #27ae60; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 26px; text-align: center; border-bottom: 3px solid #27ae60; padding-bottom: 15px; margin-bottom: 25px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    .metric-box { background-color: #ffffff; border-right: 10px solid #27ae60; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .metric-value { font-size: 24px; color: #2c3e50; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام الدخول المتطور
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    user_input = st.text_input("اسم المستخدم")
    pass_input = st.text_input("كلمة المرور", type="password")
    
    if st.button("تسجيل الدخول"):
        # خيار دخول المدير العام (أبو عمر)
        if user_input == "أبو عمر" and pass_input == "admin":
            st.session_state.logged_in = True
            st.session_state.user_role = "admin"
            st.session_state.active_user = "أبو عمر"
            st.rerun()
        # فحص مستخدمي المحلات من قاعدة البيانات
        else:
            match = st.session_state.branches_db[
                (st.session_state.branches_db['user_name'] == user_input) & 
                (st.session_state.branches_db['password'] == pass_input)
            ]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = "shop_owner"
                st.session_state.my_branch = match.iloc[0]['branch_name']
                st.session_state.active_user = user_input
                st.rerun()
            else:
                st.error("خطأ في البيانات")
else:
    # القائمة الجانبية
    st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)
    
    # خيارات المدير العام للتبديل بين المحلات
    if st.session_state.user_role == "admin":
        branch_list = ["الكل"] + st.session_state.branches_db['branch_name'].tolist()
        active_branch = st.sidebar.selectbox("تبديل العرض:", branch_list)
        # ميزة إضافية للمدير فقط
        menu_options = ["📊 التقارير العامة", "🛒 نقطة البيع", "📦 المخزن", "💸 المصروفات", "🏗️ إدارة المحلات والمستخدمين", "⚙️ الإعدادات"]
    else:
        active_branch = st.session_state.my_branch
        menu_options = ["🛒 نقطة البيع", "📦 المخزن", "💸 المصروفات", "📊 التقارير المالية"]

    menu = st.sidebar.radio("التنقل", menu_options)

    # --- القسم الجديد: إدارة المحلات والمستخدمين (لأبو عمر فقط) ---
    if menu == "🏗️ إدارة المحلات والمستخدمين":
        st.markdown("<h1 class='main-title'>🏗️ إدارة المحلات والمستخدمين</h1>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("إضافة محل جديد")
            new_b_name = st.text_input("اسم المحل الجديد")
            new_u_name = st.text_input("اسم مستخدم صاحب المحل")
            new_u_pass = st.text_input("كلمة مرور صاحب المحل")
            if st.button("حفظ المحل الجديد"):
                new_row = {'branch_name': new_b_name, 'user_name': new_u_name, 'password': new_u_pass}
                st.session_state.branches_db = pd.concat([st.session_state.branches_db, pd.DataFrame([new_row])], ignore_index=True)
                save_all()
                st.success(f"تم إنشاء {new_b_name} بنجاح!")
                st.rerun()
        
        with col2:
            st.subheader("المحلات الحالية")
            st.dataframe(st.session_state.branches_db, use_container_width=True)
            if st.button("حذف المحدد (تجريبي)"):
                st.warning("هذه الميزة تحتاج لتحديد الصف أولاً")

    # --- نقطة البيع (التي تعودنا عليها) ---
    elif menu == "🛒 نقطة البيع":
        st.markdown(f"<h1 class='main-title'>🛒 نقطة بيع: {active_branch}</h1>", unsafe_allow_html=True)
        if active_branch == "الكل":
            st.warning("يرجى اختيار محل محدد للبيع منه")
        else:
            search_q = st.text_input("🔍 ابحث عن صنف...")
            # جلب بضاعة المحل النشط فقط
            branch_inv = [i for i in st.session_state.inventory if i['branch'] == active_branch]
            
            bill_items = []
            for item in branch_inv:
                if search_q.lower() in item['item'].lower():
                    c1, c2, c3 = st.columns([2, 1, 2])
                    c1.markdown(f"**{item['item']}**\n<small>متوفر: {format_num(item['qty'])}</small>", unsafe_allow_html=True)
                    mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item['item']}_{active_branch}")
                    val = clean_num(c3.text_input("المقدار", key=f"v_{item['item']}_{active_branch}"))
                    if val > 0:
                        qty = val if mode == "كجم" else val / item["sell"]
                        bill_items.append({"item": item["item"], "qty": qty, "amount": val if mode == "₪" else val * item["sell"], "profit": (item["sell"] - item["buy"]) * qty, "cat": item["cat"]})
            
            if st.button("🚀 تنفيذ البيع", type="primary") and bill_items:
                for e in bill_items:
                    for i in st.session_state.inventory:
                        if i['item'] == e['item'] and i['branch'] == active_branch: i['qty'] -= e['qty']
                    new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'branch': active_branch, 'cat': e['cat']}
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                save_all(); st.success("تم تسجيل البيع!"); st.rerun()

    # --- باقي الأقسام (التقارير والمخزن) بنفس المنطق السابق المفلتر ---
    elif menu == "📊 التقارير العامة" or menu == "📊 التقارير المالية":
        st.markdown(f"<h1 class='main-title'>📊 التقارير - {active_branch}</h1>", unsafe_allow_html=True)
        s_df = st.session_state.sales_df.copy()
        if active_branch != "الكل": s_df = s_df[s_df['branch'] == active_branch]
        
        # عرض المربعات الثلاثية (ربح، مبيعات، رأس مال)
        # ... (نفس كود التقارير السابق)
        st.write("إجمالي مبيعات الفترة:", format_num(s_df['amount'].sum()), "₪")

    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()
