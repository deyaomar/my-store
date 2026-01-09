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
                    st.session_state.my_branch = "المدير العام"
                    st.rerun()
                else: st.error("❌ خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية وتوزيع الصلاحيات
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً {st.session_state.active_user} 👋</div>", unsafe_allow_html=True)

if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التحكم المركزي", ["📊 التقارير العامة", "🏪 إدارة الفروع", "⚙️ إدارة أصناف الفروع", "📂 إدارة الأقسام", "👤 ملفي"])
    active_branch = st.sidebar.selectbox("🏠 عرض بيانات فرع:", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("قائمة المحل", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير", "⚙️ إدارة الأصناف", "👤 ملفي"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear(); st.rerun()

# ---------------------------------------------------------
# الجزء الأول: إدارة أصناف الفروع (خاص بالمدير العام)
# ---------------------------------------------------------
if menu == "⚙️ إدارة أصناف الفروع" and st.session_state.user_role == "admin":
    st.markdown("<h1 class='main-title'>🏬 التحكم المركزي بأصناف الفروع</h1>", unsafe_allow_html=True)
    
    # 1. فلترة واختيار الفرع
    branches_list = pd.read_csv(get_db_path())['branch_name'].tolist()
    target_br = st.selectbox("🏗️ اختر الفرع لإدارة أصنافه:", branches_list)
    
    # تصفية البضاعة
    branch_inv = [i for i in st.session_state.inventory if i.get('branch') == target_br]

    # 2. إضافة صنف للفرع المختار
    with st.expander(f"➕ إضافة صنف جديد لفرع: {target_br}"):
        with st.form("admin_add_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("اسم المنتج")
            cat = c2.selectbox("القسم", st.session_state.categories)
            c3, c4, c5 = st.columns(3)
            buy = c3.number_input("سعر الشراء", min_value=0.0, step=1.0)
            sell = c4.number_input("سعر البيع", min_value=0.0, step=1.0)
            qty = c5.number_input("الكمية", min_value=0.0, step=1.0)
            if st.form_submit_button("إضافة للمخزن المركز"):
                if name:
                    st.session_state.inventory.append({'item': name, 'قسم': cat, 'شراء': buy, 'بيع': sell, 'كمية': qty, 'branch': target_br})
                    auto_save(); st.success("تم الإضافة"); st.rerun()

    st.divider()

    # 3. عرض وتعديل بضاعة الفرع
    if branch_inv:
        for idx, item in enumerate(branch_inv):
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                col1.write(f"**{item['item']}**")
                col2.write(f"شراء: {item['شراء']}")
                col3.write(f"بيع: {item['بيع']}")
                col4.write(f"الكمية: {item['كمية']}")
                if col5.button("🗑️", key=f"global_del_{idx}"):
                    st.session_state.inventory = [i for i in st.session_state.inventory if not (i['item'] == item['item'] and i['branch'] == target_br)]
                    auto_save(); st.rerun()
    else:
        st.info("لا توجد أصناف حالياً لهذا الفرع.")

# ---------------------------------------------------------
# الجزء الثاني: إدارة الأصناف (خاص بمدير الفرع)
# ---------------------------------------------------------
# ---------------------------------------------------------
# القسم المطور: إدارة الأصناف (لضمان الظهور في نقطة البيع)
# ---------------------------------------------------------
# ---------------------------------------------------------
# قسم إدارة الأصناف - نسخة الحفظ المباشر
# ---------------------------------------------------------
elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>📦 إدارة أصناف المحل</h1>", unsafe_allow_html=True)
    
    my_branch = st.session_state.get('my_branch', 'الفرع الحالي')

    # نموذج إضافة بسيط بدون Form معقد لتجنب مشاكل التحديث
    with st.container(border=True):
        st.subheader("➕ إضافة صنف جديد")
        col1, col2 = st.columns(2)
        name = col1.text_input("اسم المنتج")
        cat = col2.selectbox("القسم", st.session_state.categories if st.session_state.categories else ["عام"])
        
        col3, col4, col5 = st.columns(3)
        buy = col3.number_input("سعر الشراء", min_value=0.0, step=0.1)
        sell = col4.number_input("سعر البيع", min_value=0.0, step=0.1)
        qty = col5.number_input("الكمية المتوفرة", min_value=0.0, step=1.0)
        
        if st.button("💾 حفظ الصنف الآن", use_container_width=True):
            if name:
                # التأكد من إنشاء قائمة المخزن إذا لم تكن موجودة
                if 'inventory' not in st.session_state:
                    st.session_state.inventory = []
                
                # إضافة الصنف
                new_data = {'item': name, 'قسم': cat, 'شراء': buy, 'بيع': sell, 'كمية': qty, 'branch': my_branch}
                st.session_state.inventory.append(new_data)
                
                # الحفظ الفوري
                auto_save()
                st.success(f"تم حفظ {name} بنجاح!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("يرجى إدخال اسم المنتج")

    st.divider()
    # عرض الأصناف للتأكد من وجودها
    st.subheader("📋 الأصناف الموجودة في مخزنك")
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == my_branch]
    if my_inv:
        st.table(pd.DataFrame(my_inv)[['item', 'قسم', 'شراء', 'بيع', 'كمية']])
    else:
        st.info("لا يوجد أصناف في المخزن حالياً.")

elif menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة الفروع</h1>", unsafe_allow_html=True)
    with st.form("br"):
        bn = st.text_input("المحل"); un = st.text_input("المستخدم"); pw = st.text_input("المرور")
        if st.form_submit_button("حفظ"):
            new_br = pd.DataFrame([{'branch_name':bn,'user_name':un,'password':pw, 'role': 'shop'}])
            st.session_state.branches_db = pd.concat([st.session_state.branches_db, new_br], ignore_index=True)
            st.session_state.branches_db.to_csv(get_db_path(), index=False)
            st.success("تم إضافة الفرع"); st.rerun()
    st.table(st.session_state.branches_db)

# ---------------------------------------------------------
# الجزء المحدث: التقارير المالية
# ---------------------------------------------------------
elif menu in ["📊 التقارير العامة", "📊 التقارير"]:
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
    
    # تجهيز البيانات
    s_df = st.session_state.sales_df.copy()
    e_df = st.session_state.expenses_df.copy()
    
    # تصفية حسب الفرع المختار
    if active_branch != "كافة الفروع":
        s_df = s_df[s_df['branch'] == active_branch]
        e_df = e_df[e_df['branch'] == active_branch]

    # حساب القيم الإجمالية
    total_sales = s_df['amount'].sum() if not s_df.empty else 0
    total_profit = s_df['profit'].sum() if not s_df.empty else 0
    total_exp = e_df['amount'].sum() if not e_df.empty else 0
    net_total = total_profit - total_exp

    # عرض البطاقات المالية
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("💰 المبيعات", f"{total_sales} ₪")
    with c2:
        st.metric("📈 الأرباح", f"{total_profit} ₪")
    with c3:
        st.metric("💸 المصاريف", f"{total_exp} ₪")
    with c4:
        st.metric("⚖️ الصافي", f"{net_total} ₪")

    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📄 تفاصيل المبيعات", "📉 تفاصيل المصاريف"])
    with t1:
        st.dataframe(s_df.sort_values(by='date', ascending=False) if not s_df.empty else s_df, use_container_width=True)
    with t2:
        st.dataframe(e_df.sort_values(by='date', ascending=False) if not e_df.empty else e_df, use_container_width=True)

# ---------------------------------------------------------
# الجزء المحدث: المخزن والجرد (نسخة آمنة من الأخطاء)
# ---------------------------------------------------------
# ---------------------------------------------------------
# الجزء المحدث: المخزن والجرد (التصميم الاحترافي + التالف + الجرد اليدوي)
# ---------------------------------------------------------
# ---------------------------------------------------------
# القسم الاحترافي للمخزن والجرد (نسخة أبو عمر المعتمدة)
# ---------------------------------------------------------
elif menu == "📦 المخزن والجرد":
    # 1. التحقق من اسم الفرع بشكل آمن
    branch_name = st.session_state.get('my_branch', 'الفرع الحالي')
    st.markdown(f"<h1 class='main-title'>📦 إدارة المخزون والجرد - {branch_name}</h1>", unsafe_allow_html=True)

    # 2. تصفية البيانات (بضاعة هذا الفرع فقط)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == branch_name]
    
    if my_inv:
        df_inv = pd.DataFrame(my_inv)
        
        # --- الإحصائيات الاحترافية (التنسيق الخرافي) ---
        total_items = len(df_inv)
        stock_value = (df_inv['شراء'] * df_inv['كمية']).sum()
        potential_profit = ((df_inv['بيع'] - df_inv['شراء']) * df_inv['كمية']).sum()

        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.markdown(f'<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-right: 5px solid #3498db; text-align: center;">'
                        f'<p style="color: #555; margin-bottom: 5px;">📦 عدد الأصناف</p>'
                        f'<h2 style="color: #3498db; margin: 0;">{total_items}</h2>'
                        f'</div>', unsafe_allow_html=True)
        with col_stat2:
            st.markdown(f'<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-right: 5px solid #f1c40f; text-align: center;">'
                        f'<p style="color: #555; margin-bottom: 5px;">💰 قيمة المخزون</p>'
                        f'<h2 style="color: #f1c40f; margin: 0;">{stock_value:,.1f} ₪</h2>'
                        f'</div>', unsafe_allow_html=True)
        with col_stat3:
            st.markdown(f'<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-right: 5px solid #2ecc71; text-align: center;">'
                        f'<p style="color: #555; margin-bottom: 5px;">📈 ربح متوقع</p>'
                        f'<h2 style="color: #2ecc71; margin: 0;">{potential_profit:,.1f} ₪</h2>'
                        f'</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- تبويبات العمليات (الجرد، التالف، العرض) ---
        tab_view, tab_manual, tab_damage = st.tabs(["🔍 عرض المخزن", "📝 جرد يدوي", "⚠️ تسجيل تالف"])

        with tab_view:
            st.markdown("### 📋 قائمة البضاعة الحالية")
            st.dataframe(df_inv[['item', 'قسم', 'شراء', 'بيع', 'كمية']], use_container_width=True)

        with tab_manual:
            st.info("💡 استخدم هذا القسم لتصحيح كمية صنف موجود فعلياً في المحل.")
            with st.form("manual_inventory"):
                item_to_update = st.selectbox("اختر الصنف المراد جرده", df_inv['item'].tolist())
                actual_qty = st.number_input("الكمية الموجودة على الرف حالياً", min_value=0.0)
                if st.form_submit_button("✅ اعتماد الجرد الجديد"):
                    for item in st.session_state.inventory:
                        if item['item'] == item_to_update and item['branch'] == branch_name:
                            item['كمية'] = actual_qty
                    auto_save(); st.success(f"تم تحديث مخزون {item_to_update} بنجاح"); st.rerun()

        with tab_damage:
            st.error("⚠️ تسجيل بضاعة تالفة سيخصم الكمية ويسجل خسارتها في المصاريف.")
            with st.form("damage_report"):
                dmg_item = st.selectbox("الصنف التالف/المفقود", df_inv['item'].tolist())
                dmg_qty = st.number_input("الكمية التالفة", min_value=0.1)
                reason = st.text_input("سبب التلف (كسر، ضياع، انتهاء صلاحية)")
                if st.form_submit_button("🚑 تسجيل خسارة التالف"):
                    for it in st.session_state.inventory:
                        if it['item'] == dmg_item and it['branch'] == branch_name:
                            if it['كمية'] >= dmg_qty:
                                it['كمية'] -= dmg_qty
                                loss_amount = dmg_qty * it['شراء']
                                # تسجيل في المصاريف تلقائياً
                                new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 
                                          'reason': f"تالف: {dmg_item} ({reason})", 
                                          'amount': loss_amount, 
                                          'branch': branch_name}
                                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                                auto_save(); st.warning(f"تم خصم {dmg_qty} قطعة وتسجيل خسارة {loss_amount} ₪"); st.rerun()
                            else:
                                st.error("الكمية المطلوبة أكبر من المتوفر!")
    else:
        st.warning("⚠️ لا توجد بيانات في المخزن حالياً. قم بإضافة أصناف من صفحة 'إدارة الأصناف'.")

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 تسجيل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r = st.text_input("السبب"); a = st.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ"):
            new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
            auto_save(); st.success("تم التسجيل"); st.rerun()

elif menu == "👤 ملفي الشخصي" or menu == "👤 ملفي":
    st.markdown("<h1 class='main-title'>👤 بيانات الحساب</h1>", unsafe_allow_html=True)
    st.write(f"**المستخدم:** {st.session_state.active_user}")
    st.write(f"**الرتبة:** {st.session_state.user_role}")
    st.write(f"**الفرع:** {st.session_state.my_branch}")
