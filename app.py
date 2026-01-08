import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# 2. إدارة البيانات (نفس الهيكلية السابقة لضمان التوافق)
if 'branches_db' not in st.session_state:
    if os.path.exists('branches_config.csv'):
        st.session_state.branches_db = pd.read_csv('branches_config.csv')
    else:
        st.session_state.branches_db = pd.DataFrame([{'branch_name': 'المحل الأول', 'user_name': 'user1', 'password': '123'}])

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch', 'cat']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value', 'branch']),
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        st.session_state[state_key] = pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.read_csv('inventory_final.csv').to_dict('records') if os.path.exists('inventory_final.csv') else []

if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.branches_db.to_csv('branches_config.csv', index=False)

# 3. التنسيق (CSS) - النسخة الملكية للمدير
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    [data-testid="stSidebar"] { background-color: #0e1117 !important; color: white; }
    .main-title { color: #1e3a8a; text-align: center; font-weight: 900; font-size: 35px; border-bottom: 3px solid #10b981; padding-bottom: 15px; margin-bottom: 30px; }
    .admin-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border-right: 8px solid #10b981; }
    .stat-title { color: #64748b; font-size: 14px; font-weight: bold; }
    .stat-value { color: #0f172a; font-size: 26px; font-weight: 900; }
    .branch-tag { background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول (يدعم Enter)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول النظام</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        u_in = st.text_input("اسم المستخدم").strip()
        p_in = st.text_input("كلمة المرور", type="password").strip()
        if st.form_submit_button("دخول", use_container_width=True):
            if u_in == "أبو عمر" and p_in == "admin":
                st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                st.rerun()
            else:
                db = st.session_state.branches_db
                match = db[(db['user_name'] == u_in) & (db['password'] == p_in)]
                if not match.empty:
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.my_branch, st.session_state.active_user = True, "shop", match.iloc[0]['branch_name'], u_in
                    st.rerun()
                else: st.error("خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية للمدير
role = st.session_state.user_role
if role == "admin":
    st.sidebar.markdown(f"<div style='text-align:center; padding:20px; background:#10b981; border-radius:10px; margin-bottom:20px;'>👑 المدير العام<br><b>{st.session_state.active_user}</b></div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("التحكم الرئيسي", ["📊 المراقبة الحية", "🏪 إدارة الفروع", "📦 توريد بضاعة", "📑 التقارير الختامية", "⚙️ الإعدادات"])
    st.sidebar.markdown("---")
    active_branch = st.sidebar.selectbox("تصفية العرض حسب الفرع:", ["كافة الفروع"] + st.session_state.branches_db['branch_name'].tolist())
    if st.sidebar.button("🚨 خروج"): st.session_state.clear(); st.rerun()
else:
    # واجهة الموظف البسيطة
    st.sidebar.title(f"فرع: {st.session_state.my_branch}")
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    active_branch = st.session_state.my_branch
    if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()

# --- قسم المدير 1: المراقبة الحية ---
if menu == "📊 المراقبة الحية":
    st.markdown(f"<h1 class='main-title'>📊 مراقبة الأداء: {active_branch}</h1>", unsafe_allow_html=True)
    
    # تحضير البيانات
    sales = st.session_state.sales_df.copy()
    if active_branch != "كافة الفروع": sales = sales[sales['branch'] == active_branch]
    sales['date'] = pd.to_datetime(sales['date'])
    today_sales = sales[sales['date'].dt.date == datetime.now().date()]
    
    inv_df = pd.DataFrame(st.session_state.inventory)
    if active_branch != "كافة الفروع" and not inv_df.empty: inv_df = inv_df[inv_df['branch'] == active_branch]
    
    # صف الإحصائيات الرئيسي
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='admin-card'><div class='stat-title'>💰 مبيعات اليوم</div><div class='stat-value'>{format_num(today_sales['amount'].sum())} ₪</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='admin-card'><div class='stat-title'>📈 صافي ربح اليوم</div><div class='stat-value'>{format_num(today_sales['profit'].sum())} ₪</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='admin-card'><div class='stat-title'>📦 قيمة المخزون</div><div class='stat-value'>{format_num((inv_df['شراء']*inv_df['كمية']).sum() if not inv_df.empty else 0)} ₪</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='admin-card'><div class='stat-title'>🏪 الفروع النشطة</div><div class='stat-value'>{len(st.session_state.branches_db)}</div></div>", unsafe_allow_html=True)

    # تنبيهات النقص في المخزون
    st.markdown("### ⚠️ تنبيهات نقص البضاعة")
    if not inv_df.empty:
        low_stock = inv_df[inv_df['كمية'] < 5] # تنبيه إذا قل الصنف عن 5 كيلو/حبة
        if not low_stock.empty:
            for _, row in low_stock.iterrows():
                st.warning(f"الفرع: **{row['branch']}** | الصنف: **{row['item']}** | الكمية المتبقية: {row['كمية']} فقط!")
        else: st.success("جميع الأصناف متوفرة بكميات جيدة")

# --- قسم المدير 2: إدارة الفروع ---
elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إعداد الفروع والمستخدمين</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("new_branch"):
            st.subheader("إضافة فرع جديد")
            b_n = st.text_input("اسم المحل")
            u_n = st.text_input("اسم المستخدم")
            p_n = st.text_input("كلمة المرور")
            if st.form_submit_button("اعتماد الفرع"):
                st.session_state.branches_db = pd.concat([st.session_state.branches_db, pd.DataFrame([{'branch_name':b_n, 'user_name':u_n, 'password':p_n}])], ignore_index=True)
                auto_save(); st.rerun()
    with col2:
        st.subheader("قائمة الفروع الحالية")
        st.table(st.session_state.branches_db)

# --- قسم المدير 3: توريد البضاعة ---
elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد بضاعة للمخازن</h1>", unsafe_allow_html=True)
    with st.form("inventory_form"):
        c1, c2, c3 = st.columns(3)
        item = c1.text_input("اسم الصنف (مثلاً: موز)")
        branch = c2.selectbox("توجيه إلى فرع:", st.session_state.branches_db['branch_name'].tolist())
        cat = c3.selectbox("القسم:", st.session_state.categories)
        buy = c1.number_input("سعر التكلفة", min_value=0.0)
        sell = c2.number_input("سعر البيع", min_value=0.0)
        qty = c3.number_input("الكمية الموردة", min_value=0.0)
        if st.form_submit_button("تأكيد التوريد"):
            st.session_state.inventory.append({'item':item, 'branch':branch, 'قسم':cat, 'شراء':buy, 'بيع':sell, 'كمية':qty})
            auto_save(); st.success("تمت الإضافة للمخزن بنجاح")

# باقي القوائم يتم تفعيلها بنفس الطريقة الاحترافية...
else:
    st.info("أهلاً أبو عمر، هذا القسم جاهز لاستقبال بياناتك.")
