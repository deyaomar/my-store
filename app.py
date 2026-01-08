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

def force_init_db():
    path = get_db_path()
    default_data = [
        {'branch_name': 'المدير العام', 'user_name': 'أبو عمر', 'password': 'admin', 'role': 'admin'},
        {'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123', 'role': 'shop'}
    ]
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        pd.DataFrame(default_data).to_csv(path, index=False, encoding='utf-8-sig')
    return pd.read_csv(path, encoding='utf-8-sig')

# 2. تحميل البيانات
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = force_init_db()

FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        st.session_state[state_key] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية', 'سعر_القطعة'])
    st.session_state.inventory = inv_df.to_dict('records')

if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    st.session_state.categories = list(dict.fromkeys(["سجائر"] + (cat_df['name'].tolist() if not cat_df.empty else ["مواد غذائية"])))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق الجمالي (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; direction: rtl; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-left: 3px solid #10b981; }
    .sidebar-user { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white !important; font-weight: 900; font-size: 22px; text-align: center; padding: 20px; border-radius: 15px; margin: 10px; }
    
    /* Item Cards */
    .item-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-right: 6px solid #10b981;
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .item-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
    .item-name { font-size: 20px; font-weight: 900; color: #1e293b; margin-bottom: 5px; }
    .item-stock { font-size: 14px; color: #64748b; }
    .main-title { color: #1e293b; text-align: center; border-bottom: 4px solid #10b981; padding-bottom: 10px; font-weight: 900; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

# 4. تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>🔐 نظام أبو عمر للإدارة</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("👤 اسم المستخدم").strip()
        p = st.text_input("🔑 كلمة المرور", type="password").strip()
        if st.form_submit_button("دخول"):
            db = force_init_db()
            m = db[(db['user_name'] == u) & (db['password'] == p)]
            if not m.empty:
                st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, m.iloc[0]['role'], u
                st.session_state.my_branch = m.iloc[0]['branch_name']; st.rerun()
            else: st.error("❌ خطأ في البيانات")
    st.stop()

# 5. القائمة الجانبية
st.sidebar.markdown(f"<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
if st.session_state.user_role == "admin":
    menu = st.sidebar.radio("التنقل", ["📊 التقارير العامة", "🏪 إدارة الفروع", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.sidebar.selectbox("تصفية الفرع", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    menu = st.sidebar.radio("التنقل", ["🛒 شاشة البيع", "📦 المخزن", "💸 المصروفات", "📊 التقارير", "⚙️ إدارة الأصناف", "👤 ملفي الشخصي"])
    active_branch = st.session_state.my_branch

# --- شاشة البيع الاحترافية ---
if menu == "🛒 شاشة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع الذكية</h1>", unsafe_allow_html=True)
    
    search = st.text_input("🔍 ابحث عن صنف بالاسم أو القسم...", placeholder="اكتب هنا للبحث...")
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    current_bill = []
    
    for it in my_inv:
        if not search or search.lower() in it['item'].lower() or search.lower() in it.get('قسم', '').lower():
            st.markdown(f"""
                <div class="item-card">
                    <div class="item-name">{it['item']}</div>
                    <div class="item-stock">المتوفر في المخزن: {format_num(it['كمية'])} | القسم: {it.get('قسم', 'عام')}</div>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1.5, 1, 1])
            opts = ["وحدة/علبة"]
            if it.get('سعر_القطعة', 0) > 0: opts.append("تجزئة/فرط")
            
            stype = c1.selectbox("طريقة البيع", opts, key=f"st_{it['item']}")
            val = clean_num(c2.text_input("المبلغ المطلوب ₪", key=f"v_{it['item']}"))
            
            if val > 0:
                p = it['بيع'] if stype == "وحدة/علبة" else it.get('سعر_القطعة', it['بيع'])
                qty = (val/p)/20 if (stype=="تجزئة/فرط" and it.get('قسم')=="سجائر") else (val/p)
                current_bill.append({
                    'item': it['item'], 'amount': val, 'profit': val - (it['شراء']*qty), 
                    'qty_sub': qty, 'branch': st.session_state.my_branch
                })
            st.write("---")

    if current_bill:
        st.markdown("### 📝 ملخص الفاتورة")
        total_amt = sum(item['amount'] for item in current_bill)
        st.info(f"إجمالي المبلغ الحالي: {format_num(total_amt)} ₪")
        
        if st.button("✅ اعتماد وإتمام الفاتورة", use_container_width=True):
            st.session_state.show_checkout = True

    # نافذة منبثقة (Modal) لبيانات الزبون تظهر بعد الاعتماد
    if 'show_checkout' in st.session_state and st.session_state.show_checkout:
        with st.expander("🏁 اللمسات الأخيرة للفاتورة", expanded=True):
            st.subheader("تسجيل بيانات العميل")
            c_name = st.text_input("اسم الزبون")
            c_phone = st.text_input("رقم الجوال")
            c_method = st.selectbox("طريقة الدفع", ["نقدي", "دين/آجل", "تحويل"])
            
            if st.button("🚀 حفظ وإصدار الفاتورة"):
                b_id = str(uuid.uuid4())[:8]
                dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for b_item in current_bill:
                    # تحديث المخزن
                    for i, inv in enumerate(st.session_state.inventory):
                        if inv['item'] == b_item['item'] and inv['branch'] == b_item['branch']:
                            st.session_state.inventory[i]['كمية'] -= b_item['qty_sub']
                    
                    # تسجيل في المبيعات
                    new_sale = {
                        'date': dt, 'item': b_item['item'], 'amount': b_item['amount'],
                        'profit': b_item['profit'], 'method': c_method, 'customer_name': c_name,
                        'customer_phone': c_phone, 'bill_id': b_id, 'branch': b_item['branch']
                    }
                    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_sale])], ignore_index=True)
                
                auto_save()
                st.session_state.show_checkout = False
                st.success("تم تسجيل الفاتورة بنجاح!")
                st.balloons()
                st.rerun()

# --- بقية الأقسام (كما هي بنفس التنسيق الفخم) ---
elif menu in ["📊 التقارير العامة", "📊 التقارير"]:
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية - {active_branch}</h1>", unsafe_allow_html=True)
    # ... كود التقارير المختصر ...
    s_df = st.session_state.sales_df.copy()
    if active_branch != "كافة الفروع": s_df = s_df[s_df['branch'] == active_branch]
    st.dataframe(s_df.sort_values(by='date', ascending=False), use_container_width=True)

elif menu == "⚙️ إدارة الأصناف":
    st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
    with st.form("add_item"):
        n = st.text_input("اسم الصنف")
        q = st.selectbox("القسم", st.session_state.categories)
        b, s, p = st.text_input("شراء"), st.text_input("بيع"), st.text_input("بيع فرط (للسجائر)")
        qty = st.text_input("الكمية")
        if st.form_submit_button("حفظ"):
            st.session_state.inventory.append({
                "item": n, "قسم": q, "شراء": clean_num(b), "بيع": clean_num(s), 
                "كمية": clean_num(qty), "branch": st.session_state.my_branch, "سعر_القطعة": clean_num(p)
            })
            auto_save(); st.success("تم الحفظ"); st.rerun()

elif menu == "📦 المخزن":
    st.markdown("<h1 class='main-title'>📦 جرد المخزن</h1>", unsafe_allow_html=True)
    st.table(pd.DataFrame([i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]))

elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp"):
        r, a = st.text_input("البيان"), st.number_input("المبلغ")
        if st.form_submit_button("تسجيل"):
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}])], ignore_index=True)
            auto_save(); st.rerun()
