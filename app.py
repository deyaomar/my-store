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

if menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة التحكم الشامل بالأصناف</h1>", unsafe_allow_html=True)
    
    # تحديد الفرع المستهدف للإدارة (للمدير العام)
    if st.session_state.user_role == "admin":
        branch_list = pd.read_csv(get_db_path())['branch_name'].tolist()
        target_branch = st.selectbox("🏬 اختر الفرع للتحكم ببياناته:", branch_list)
    else:
        target_branch = st.session_state.my_branch

    t_add, t_manage, t_cats = st.tabs(["➕ إضافة أصناف للفرع", "🛠️ جرد وتعديل مخزن الفرع", "📂 إدارة الأقسام"])

    with t_add:
        with st.form("admin_add_i", clear_on_submit=True):
            st.info(f"إضافة صنف جديد إلى: {target_branch}")
            n = st.text_input("اسم الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            b = st.text_input("سعر التكلفة (شراء)")
            s = st.text_input("سعر البيع")
            q = st.text_input("الكمية")
            if st.form_submit_button("➕ تنفيذ الإضافة"):
                if n:
                    st.session_state.inventory.append({
                        "item": n, "قسم": cat, "شراء": clean_num(b), 
                        "بيع": clean_num(s), "كمية": clean_num(q), "branch": target_branch
                    })
                    auto_save()
                    st.success(f"✅ تم إضافة {n} لفرع {target_branch}")
                    st.rerun()

    with t_manage:
        st.subheader(f"قائمة بضائع فرع: {target_branch}")
        # تصفية البضاعة للفرع المختار
        branch_data = [i for i in st.session_state.inventory if i.get('branch') == target_branch]
        if branch_data:
            df_branch = pd.DataFrame(branch_data)
            # عرض جدول قابل للتعديل (Data Editor) للمدير
            edited_df = st.data_editor(
                df_branch[['item', 'قسم', 'شراء', 'بيع', 'كمية']],
                column_config={
                    "item": "اسم الصنف",
                    "قسم": st.column_config.SelectboxColumn("القسم", options=st.session_state.categories),
                    "شراء": "سعر الشراء",
                    "بيع": "سعر البيع",
                    "كمية": "الكمية المتوفرة"
                },
                num_rows="dynamic",
                use_container_width=True,
                key="editor"
            )
            
            if st.button("💾 حفظ كافة التغييرات للفرع"):
                # تحديث المصفوفة الرئيسية بالبيانات المعدلة
                new_inventory = [i for i in st.session_state.inventory if i.get('branch') != target_branch]
                for _, row in edited_df.iterrows():
                    new_inventory.append({
                        "item": row['item'], "قسم": row['قسم'], 
                        "شراء": clean_num(row['شراء']), "بيع": clean_num(row['بيع']), 
                        "كمية": clean_num(row['كمية']), "branch": target_branch
                    })
                st.session_state.inventory = new_inventory
                auto_save()
                st.success("✅ تم تحديث بيانات الفرع بنجاح!")
                st.rerun()
        else:
            st.warning("هذا الفرع لا يحتوي على أصناف حالياً.")

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
    st.markdown("<h1 class='main-title'>🛒 نظام المبيعات المتطور</h1>", unsafe_allow_html=True)
    
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    # حالة إتمام الفاتورة (تظهر فقط للتطبيق)
    if st.session_state.get('show_cust_fields', False):
        st.markdown("""<div style='background-color: #e0f2fe; padding: 20px; border-radius: 15px; border-right: 5px solid #0369a1; margin-bottom: 20px;'>
            <h3 style='color: #0369a1; margin: 0;'>📱 اعتماد دفع التطبيق</h3>
            <p style='color: #1e293b;'>يرجى تسجيل بيانات الزبون لإتمام عملية التطبيق.</p>
        </div>""", unsafe_allow_html=True)
        
        with st.container(border=True):
            c_n = st.text_input("👤 اسم الزبون المستفيد")
            c_p = st.text_input("📞 رقم هاتف الزبون")
            if st.button("✅ تأكيد وحفظ بيانات التطبيق", use_container_width=True, type="primary"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                auto_save()
                st.session_state.show_cust_fields = False
                st.success("تم الحفظ بنجاح!"); st.rerun()
    else:
        # --- اختيار طريقة الدفع (الأولوية للتطبيق) ---
        if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
        
        st.write("💳 **طريقة الدفع الحالية:**")
        p_cols = st.columns([1, 1, 1])
        
        # ترتيب الأزرار (تطبيق أولاً)
        if p_cols[0].button("📱 تطبيق / بنكي", use_container_width=True, type="primary" if st.session_state.p_method == "تطبيق" else "secondary"):
            st.session_state.p_method = "تطبيق"
        if p_cols[1].button("💵 نقداً", use_container_width=True, type="primary" if st.session_state.p_method == "نقداً" else "secondary"):
            st.session_state.p_method = "نقداً"
        if p_cols[2].button("📝 دين", use_container_width=True, type="primary" if st.session_state.p_method == "دين / آجل" else "secondary"):
            st.session_state.p_method = "دين / آجل"

        st.markdown(f"<div style='text-align: center; background: #f8fafc; padding: 10px; border-radius: 10px; border: 1px dashed #cbd5e1;'>النمط المختار: <b>{st.session_state.p_method}</b></div>", unsafe_allow_html=True)
        
        search_q = st.text_input("🔍 ابحث عن صنف...", placeholder="اكتب هنا للبحث السريع...")

        bill_items = []
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i.get('قسم') == cat]
            if search_q: items = [i for i in items if search_q.lower() in i['item'].lower()]
            
            if items:
                with st.expander(f"📂 {cat}", expanded=True):
                    grid = st.columns(3)
                    for idx, it in enumerate(items):
                        with grid[idx % 3]:
                            with st.container(border=True):
                                st.markdown(f"<div style='text-align:center;'><b>{it['item']}</b><br><b style='color:#16a34a;'>{it['بيع']} ₪</b></div>", unsafe_allow_html=True)
                                val = st.number_input("المبلغ", min_value=0.0, step=1.0, key=f"sale_{it['item']}_{idx}", label_visibility="collapsed")
                                if val > 0:
                                    qty = val / it['بيع']
                                    if qty <= it['كمية']:
                                        bill_items.append({"item": it['item'], "qty": qty, "amount": val, "profit": (it['بيع'] - it['شراء']) * qty})
                                    else: st.error("الكمية نافذة!")
                                st.markdown(f"<center><small style='color:#94a3b8;'>متوفر: {format_num(it['كمية'])}</small></center>", unsafe_allow_html=True)

        # --- منطقة التنفيذ ---
        if bill_items:
            total_sum = sum(item['amount'] for item in bill_items)
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container():
                st.markdown(f"""<div style='background: #1e293b; color: white; padding: 20px; border-radius: 15px; text-align: center;'>
                    <div style='font-size: 1.2em;'>إجمالي المطلوب</div>
                    <div style='font-size: 2.2em; font-weight: 900; color: #4ade80;'>{format_num(total_sum)} ₪</div>
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
                    
                    # المنطق المطلوب: إذا كان تطبيق تظهر شاشة البيانات، إذا نقدي يصفر ويخلص
                    if st.session_state.p_method == "تطبيق":
                        st.session_state.show_cust_fields = True
                    else:
                        st.success("تمت عملية البيع النقدي بنجاح!")
                        st.session_state.show_cust_fields = False
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
    st.markdown("<h1 class='main-title'>📦 المخزن</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    st.table(pd.DataFrame(my_inv))

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r = st.text_input("البيان"); a = st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()
    st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch], use_container_width=True)

elif menu == "👤 ملفي الشخصي":
    st.markdown("<h1 class='main-title'>👤 ملفي الشخصي</h1>", unsafe_allow_html=True)
    st.write(f"المستخدم الحالي: {st.session_state.active_user}")
