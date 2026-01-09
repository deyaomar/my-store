import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

# دالات التنسيق والتنظيف
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

# دالة القراءة الآمنة
def safe_read_csv(file_path, default_cols):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try: return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# --- إدارة الفروع والقاعدة ---
def get_db_path(): return 'branches_config.csv'

def initialize_db():
    path = get_db_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame([
            {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
            {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
        ])
        df.to_csv(path, index=False)
    return pd.read_csv(path)

# 2. تحميل البيانات الأساسية (Session State)
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value', 'branch']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value', 'branch'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        st.session_state[state_key] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = cat_df['name'].tolist() if not cat_df.empty else ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التصميم (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-left: 2px solid #27ae60; }
    [data-testid="stSidebar"] .stRadio div label { background-color: #334155; border-radius: 10px; padding: 12px 20px !important; margin-bottom: 10px; border-right: 5px solid transparent; transition: 0.3s; }
    [data-testid="stSidebar"] .stRadio div label[data-selected="true"] { background-color: #27ae60 !important; border-right: 5px solid #14532d; }
    [data-testid="stSidebar"] .stRadio div label p { color: white !important; font-weight: 700 !important; font-size: 18px !important; }
    .sidebar-user { color: #27ae60 !important; font-weight: 900; font-size: 24px; text-align: center; margin-bottom: 25px; border-bottom: 2px solid #334155; padding-bottom: 15px; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 5px solid #27ae60; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; border-radius: 10px; }
    .rep-card { background: white; border-radius: 15px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #27ae60; }
    .rep-label { color: #7f8c8d; font-size: 1rem; font-weight: bold; margin-bottom: 10px; }
    .rep-value { color: #2c3e50; font-size: 1.8rem; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("👤 اسم المستخدم").strip()
            p = st.text_input("🔑 كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول"):
                db = pd.read_csv(get_db_path())
                m = db[(db['user_name'] == u) & (db['password'] == p)]
                if not m.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = m.iloc[0]['role'] if 'role' in m.columns else "shop"
                    st.session_state.active_user = u
                    st.session_state.my_branch = m.iloc[0]['branch_name']
                    st.rerun()
                elif u == "أبو عمر" and p == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.session_state.my_branch = "الإدارة"
                    st.rerun()
                else: st.error("❌ خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)
if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل السريع", ["📊 التقارير المالية العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.sidebar.selectbox("🏠 اختيار الفرع للعرض:", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# --- محتوى الأقسام (تم اختصار الأقسام الأخرى لبيان تعديل إدارة الأصناف) ---

elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ الإدارة المركزية للأصناف</h1>", unsafe_allow_html=True)
    
    # 1. الربط الحقيقي مع قسم إدارة الفروع
    # بنحاول نجيب الفروع من ملف branches.csv اللي أنت بتديره
    try:
        df_branches = pd.read_csv('branches.csv')
        real_branches = df_branches['branch_name'].unique().tolist()
    except:
        # لو الملف مش موجود، بنشوف شو في فروع مسجلة أصلاً في المخزن
        real_branches = list(set([i.get('branch') for i in st.session_state.inventory if i.get('branch')]))

    if not real_branches:
        st.error("⚠️ لا توجد فروع مسجلة! اذهب أولاً لقسم 'إدارة الفروع' وأضف محلاتك هناك.")
    else:
        # 2. اختيار الفرع (مرتبط حقيقياً بصفحات المحلات)
        selected_branch = st.selectbox("🏗️ اختر الفرع المطلوب إدارته:", real_branches)
        
        # تصفية بضاعة الفرع المختار فقط
        branch_inv = [i for i in st.session_state.inventory if i.get('branch') == selected_branch]

        st.info(f"📍 إدارة مخزن: **{selected_branch}**")

        # 3. إضافة صنف جديد (تصميم مباشر وبدون أي متغيرات قديمة)
        with st.container(border=True):
            st.markdown(f"#### ➕ إضافة صنف لـ {selected_branch}")
            with st.form("new_admin_form"):
                c1, c2 = st.columns(2)
                i_name = c1.text_input("اسم المنتج")
                # التأكد من وجود أقسام، وإلا نضع قسم "عام"
                cats = st.session_state.get('categories', ["عام"])
                i_cat = c2.selectbox("القسم", cats)
                
                c3, c4, c5 = st.columns(3)
                i_buy = c3.number_input("سعر الشراء", min_value=0.0, step=1.0, value=0.0)
                i_sell = c4.number_input("سعر البيع", min_value=0.0, step=1.0, value=0.0)
                i_qty = c5.number_input("الكمية", min_value=0.0, step=1.0, value=0.0)
                
                if st.form_submit_button("🚀 حفظ الصنف"):
                    if i_name:
                        new_item = {
                            'item': i_name, 'قسم': i_cat, 'شراء': i_buy, 
                            'بيع': i_sell, 'كمية': i_qty, 'branch': selected_branch
                        }
                        st.session_state.inventory.append(new_item)
                        auto_save()
                        st.success(f"✅ تم إضافة {i_name} بنجاح!"); st.rerun()
                    else:
                        st.error("اسم الصنف مطلوب!")

        st.divider()

        # 4. إدارة بضاعة الفرع (عرض، تعديل، حذف)
        if branch_inv:
            st.markdown(f"### 📦 بضاعة {selected_branch}")
            for idx, item in enumerate(branch_inv):
                with st.container(border=True):
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                    col1.markdown(f"**{item['item']}**\n<small>{item['قسم']}</small>", unsafe_allow_html=True)
                    col2.write(f"شراء: {item['شراء']}")
                    col3.write(f"بيع: {item['بيع']}")
                    col4.write(f"الكمية: {item['كمية']}")
                    
                    if col5.button("🗑️ حذف", key=f"btn_del_{selected_branch}_{idx}"):
                        # حذف الصنف من القائمة الرئيسية (inventory)
                        st.session_state.inventory = [i for i in st.session_state.inventory if not (i['item'] == item['item'] and i['branch'] == selected_branch)]
                        auto_save()
                        st.warning(f"تم حذف {item['item']}"); st.rerun()
        else:
            st.warning("هذا الفرع لا يحتوي على بضاعة حالياً.")

    with t_cats:
        st.subheader("التحكم في أقسام النظام")
        with st.form("c_form", clear_on_submit=True):
            nc = st.text_input("اسم القسم الجديد")
            if st.form_submit_button("حفظ القسم"):
                if nc and nc not in st.session_state.categories:
                    st.session_state.categories.append(nc); auto_save(); st.rerun()
        for c in st.session_state.categories:
            c1, c2 = st.columns([4,1])
            c1.write(f"📂 {c}")
            if c2.button("❌", key=f"del_{c}"):
                st.session_state.categories.remove(c); auto_save(); st.rerun()

# --- بقية الأقسام (نفس الكود السابق للحفاظ على الوظائف) 
elif menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع الاحترافية</h1>", unsafe_allow_html=True)
    
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    # --- شاشة بيانات الزبون (تظهر بعد الاعتماد في حالة التطبيق فقط) ---
    if st.session_state.get('show_cust_fields', False):
        st.markdown("""<div style='background: #f0f9ff; padding: 25px; border-radius: 15px; border: 1px solid #7dd3fc; text-align: center;'>
            <h2 style='color: #0369a1;'>📱 بيانات دفع التطبيق</h2>
            <p style='color: #0c4a6e;'>يرجى إدخال بيانات الزبون لتوثيق التحويل</p>
        </div>""", unsafe_allow_html=True)
        
        with st.container(border=True):
            c_n = st.text_input("👤 اسم الزبون المستفيد")
            c_p = st.text_input("📞 رقم الهاتف")
            if st.button("✅ حفظ وإتمام العملية", use_container_width=True, type="primary"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                auto_save()
                st.session_state.show_cust_fields = False
                st.success("تم التوثيق بنجاح!"); st.rerun()
    else:
        # --- اختيار طريقة الدفع (الأولوية للتطبيق أولاً) ---
        if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
        
        st.write("💳 **اختر وسيلة الدفع:**")
        p_cols = st.columns(3)
        
        # التطبيق هو الأول والافتراضي
        if p_cols[0].button("📱 تطبيق", use_container_width=True, type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
            st.session_state.p_method = "تطبيق"
        if p_cols[1].button("💵 نقداً", use_container_width=True, type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
            st.session_state.p_method = "نقداً"
        if p_cols[2].button("📝 دين", use_container_width=True, type="primary" if st.session_state.p_method == "دين / آجل" else "secondary"):
            st.session_state.p_method = "دين / آجل"

        st.divider()

        bill_items = []
        # --- عرض المنتجات بتصميم عصري وخانات فارغة ---
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i.get('قسم') == cat]
            if items:
                st.markdown(f"#### 📂 {cat}")
                grid = st.columns(3)
                for idx, it in enumerate(items):
                    with grid[idx % 3]:
                        with st.container(border=True):
                            # اسم المنتج وسعره المرجعي
                            st.markdown(f"<div style='text-align:center; margin-bottom:10px;'><b style='font-size:1.1em;'>{it['item']}</b><br><span style='color:#64748b;'>السعر: {it['بيع']} ₪</span></div>", unsafe_allow_html=True)
                            
                            # خانة السعر فارغة (None افتراضياً) لتدخل الرقم يدوياً
                            val = st.number_input(f"المبلغ - {it['item']}", min_value=0.0, value=0.0, step=1.0, key=f"inp_{it['item']}_{idx}", label_visibility="collapsed")
                            
                            if val > 0:
                                qty = val / it['بيع']
                                if qty <= it['كمية']:
                                    bill_items.append({"item": it['item'], "qty": qty, "amount": val, "profit": (it['بيع'] - it['شراء']) * qty})
                                else: st.error("المخزن لا يكفي")
                            
                            st.markdown(f"<center><small style='color:#94a3b8;'>المتوفر: {format_num(it['كمية'])}</small></center>", unsafe_allow_html=True)

        # --- ملخص الفاتورة السفلي ---
        if bill_items:
            total_sum = sum(item['amount'] for item in bill_items)
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container():
                st.markdown(f"""<div style='background: #0f172a; color: white; padding: 20px; border-radius: 15px; text-align: center;'>
                    <div style='font-size: 1.1em; opacity: 0.8;'>إجمالي الفاتورة ({st.session_state.p_method})</div>
                    <div style='font-size: 2.2em; font-weight: 900; color: #10b981;'>{format_num(total_sum)} ₪</div>
                </div>""", unsafe_allow_html=True)
                
                if st.button("🚀 إتمام العملية الآن", use_container_width=True, type="primary"):
                    b_id = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        for idx, inv_item in enumerate(st.session_state.inventory):
                            if inv_item['item'] == e['item'] and inv_item['branch'] == st.session_state.my_branch:
                                st.session_state.inventory[idx]['كمية'] -= e['qty']
                        
                        new_sale = {
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 
                            'method': st.session_state.p_method, 
                            'customer_name': 'زبون عام', 'customer_phone': '', 
                            'bill_id': b_id, 'branch': st.session_state.my_branch
                        }
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
                    
                    st.session_state.current_bill_id = b_id
                    auto_save()
                    
                    if st.session_state.p_method == "تطبيق":
                        st.session_state.show_cust_fields = True
                    else:
                        st.success("تم البيع النقدي بنجاح!")
                    st.rerun()
elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
    with st.form("br"):
        bn = st.text_input("المحل"); un = st.text_input("المستخدم"); pw = st.text_input("المرور")
        if st.form_submit_button("حفظ"):
            pd.concat([pd.read_csv(get_db_path()), pd.DataFrame([{'branch_name':bn,'user_name':un,'password':pw, 'role': 'shop'}])]).to_csv(get_db_path(), index=False)
            st.rerun()
    st.table(pd.read_csv(get_db_path()))

elif menu in ["📊 التقارير المالية العامة", "📊 التقارير المالية"]:
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
    
    # تجهيز البيانات
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    
    # تصفية حسب الفرع المختار (إذا كان المدير اختار فرع معين أو كان مستخدم فرع)
    if active_branch != "كافة الفروع":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]

    # حساب القيم الإجمالية
    total_sales = s_df['amount'].sum()
    total_profit = s_df['profit'].sum()
    total_exp = e_df['amount'].sum()
    net_total = total_profit - total_exp

    # --- التصميم الاحترافي للبطاقات ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
            <div class="rep-card" style="border-top-color: #3498db;">
                <div class="rep-label">💰 إجمالي المبيعات</div>
                <div class="rep-value">{format_num(total_sales)} ₪</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
            <div class="rep-card" style="border-top-color: #27ae60;">
                <div class="rep-label">📈 صافي الأرباح</div>
                <div class="rep-value">{format_num(total_profit)} ₪</div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div class="rep-card" style="border-top-color: #e74c3c;">
                <div class="rep-label">💸 إجمالي المصاريف</div>
                <div class="rep-value">{format_num(total_exp)} ₪</div>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        color = "#27ae60" if net_total >= 0 else "#e74c3c"
        st.markdown(f"""
            <div class="rep-card" style="border-top-color: {color};">
                <div class="rep-label">⚖️ المتبقي النهائي</div>
                <div class="rep-value" style="color: {color};">{format_num(net_total)} ₪</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # عرض الجداول تحت البطاقات
    t1, t2 = st.tabs(["📄 تفاصيل المبيعات", "📉 تفاصيل المصاريف"])
    with t1:
        st.dataframe(s_df.sort_values(by='date', ascending=False), use_container_width=True)
    with t2:
        st.dataframe(e_df.sort_values(by='date', ascending=False), use_container_width=True)

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 جرد المخزن التفصيلي</h1>", unsafe_allow_html=True)
    
    # تصفية بضاعة الفرع الحالي
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    if not my_inv:
        st.warning("⚠️ لا توجد أصناف في المخزن حالياً.")
    else:
        # 1. لوحة المعلومات المالية للمخزن (نظرة عامة)
        df_inv = pd.DataFrame(my_inv)
        total_items = len(df_inv)
        total_qty = df_inv['كمية'].sum()
        total_buy_value = (df_inv['كمية'] * df_inv['شراء']).sum()
        total_sell_value = (df_inv['كمية'] * df_inv['بيع']).sum()
        expected_profit = total_sell_value - total_buy_value

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("عدد الأصناف", f"{total_items}")
            c2.metric("رأس المال (شراء)", f"{format_num(total_buy_value)} ₪")
            c3.metric("قيمة البيع", f"{format_num(total_sell_value)} ₪")
            c4.metric("الربح المتوقع", f"{format_num(expected_profit)} ₪")

        st.markdown("---")
        
        # 2. جدول الجرد والعرض التفصيلي
        st.markdown("### 📋 تفاصيل الأصناف وعملية الجرد")
        
        jard_updates = []

        # العناوين (Header) للتوضيح
        h1, h2, h3, h4, h5 = st.columns([2.5, 1, 1, 1.5, 1.5])
        h1.write("**الصنف والقسم**")
        h2.write("**شراء / بيع**")
        h3.write("**النظام**")
        h4.write("**الجرد الفعلي**")
        h5.write("**الحالة / الفرق**")

        for idx, it in enumerate(my_inv):
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([2.5, 1, 1, 1.5, 1.5])
                
                # العمود 1: تفاصيل الصنف
                col1.markdown(f"**{it['item']}** \n<small>📂 {it['قسم']}</small>", unsafe_allow_html=True)
                
                # العمود 2: الأسعار
                col2.markdown(f"💰 {it['شراء']}  \n🏷️ {it['بيع']}")
                
                # العمود 3: كمية النظام
                col3.markdown(f"📦  \n**{format_num(it['كمية'])}**")
                
                # العمود 4: مدخل الجرد اليدوي
                # القيمة الافتراضية هي كمية النظام لسهولة التعديل
                actual = col4.number_input("الفعلي", min_value=0.0, value=float(it['كمية']), step=1.0, key=f"j_{idx}_{it['item']}")
                
                # العمود 5: الحالة والفرق
                diff = actual - it['كمية']
                if diff == 0:
                    status_color = "#16a34a" # أخضر
                    status_text = "✅ مطابق"
                elif diff < 0:
                    status_color = "#dc2626" # أحمر
                    status_text = f"⚠️ عجز ({format_num(diff)})"
                else:
                    status_color = "#2563eb" # أزرق
                    status_text = f"➕ زيادة (+{format_num(diff)})"
                
                col5.markdown(f"""
                    <div style='background:{status_color}; color:white; padding:8px; border-radius:10px; text-align:center; font-size:0.9em; font-weight:bold;'>
                        {status_text}
                    </div>
                    <div style='text-align:center; font-size:0.8em; margin-top:5px; color:gray;'>
                        قيمة الفرق: {format_num(abs(diff) * it['شراء'])} ₪
                    </div>
                """, unsafe_allow_html=True)

                # إذا وجد فرق، نجهز البيانات للتحديث
                if diff != 0:
                    jard_updates.append({
                        'item': it['item'],
                        'new_qty': actual,
                        'diff': diff,
                        'loss': abs(diff) * it['شراء'] if diff < 0 else 0
                    })

        # 3. اعتماد الجرد
        if jard_updates:
            st.divider()
            st.warning(f"⚠️ لقد قمت بتغيير كميات لـ ({len(jard_updates)}) صنف. هل تريد اعتماد الكميات الفعلية الجديدة؟")
            if st.button("💾 اعتماد نتائج الجرد وتحديث المخزن", use_container_width=True, type="primary"):
                for up in jard_updates:
                    for i, inv_item in enumerate(st.session_state.inventory):
                        if inv_item['item'] == up['item'] and inv_item['branch'] == st.session_state.my_branch:
                            st.session_state.inventory[i]['كمية'] = up['new_qty']
                            
                            # تسجيل في سجل التعديلات
                            adj_log = {
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'item': up['item'],
                                'diff': up['diff'],
                                'branch': st.session_state.my_branch
                            }
                            st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame([adj_log])], ignore_index=True)
                
                auto_save()
                st.success("✅ تم تحديث بيانات المخزن بناءً على الجرد الفعلي!")
                st.rerun()
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r = st.text_input("البيان"); a = st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()
    st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "👤 ملفي الشخصي":
    st.markdown("<h1 class='main-title'>👤 إدارة الملف الشخصي</h1>", unsafe_allow_html=True)
    
    # 1. عرض بيانات الحساب في بطاقة أنيقة
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"<div style='font-size: 80px; text-align: center;'>👤</div>", unsafe_allow_html=True)
        with col2:
            st.subheader(f"مرحباً بك يا {st.session_state.get('user_role', 'المستخدم')}")
            st.info(f"📍 **الفرع الحالي:** {st.session_state.my_branch} | 🔑 **نوع الحساب:** {st.session_state.user_role}")

    # 2. نظام التبويبات للتعديل والاسترجاع
    tab1, tab2 = st.tabs(["🔐 تغيير كلمة المرور", "📧 استعادة الحساب"])
    
    with tab1:
        st.write("### تحديث كلمة المرور")
        st.warning("ملاحظة: لتغيير كلمة المرور بشكل دائم، يرجى مراجعة المسؤول لتحديثها في قائمة المستخدمين الرئيسية.")
        
        with st.container(border=True):
            old_pass = st.text_input("كلمة المرور الحالية", type="password")
            new_pass = st.text_input("كلمة المرور الجديدة", type="password")
            confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
            
            if st.button("💾 تحديث الآن"):
                if new_pass == confirm_pass and len(new_pass) >= 4:
                    st.success("✅ تم استلام طلب التغيير (هذه الميزة تحتاج لربط قاعدة البيانات)")
                else:
                    st.error("⚠️ يرجى التأكد من تطابق كلمة المرور وقوتها")

    with tab2:
        st.write("### استرجاع الحساب")
        st.write("في حال فقدان الوصول، أدخل بريدك الإلكتروني لتلقي تعليمات الاسترداد.")
        
        with st.container(border=True):
            user_email = st.text_input("البريد الإلكتروني المسجل")
            if st.button("📩 إرسال رابط الاسترداد"):
                if "@" in user_email:
                    st.success(f"تم إرسال تعليمات الاسترداد إلى: {user_email}")
                else:
                    st.error("يرجى إدخال بريد إلكتروني صحيح")

    # زر تسجيل الخروج
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج من النظام", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
