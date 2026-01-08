import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime, timedelta

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

# --- نظام الإدارة المباشر للملفات ---
def get_db_path():
    return 'branches_config.csv'

def initialize_db():
    path = get_db_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])
        df.to_csv(path, index=False)
    return pd.read_csv(path)

# 2. تحميل البيانات الأساسية (Session State)
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = initialize_db()

# إدارة ملفات البيانات التفصيلية
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount', 'branch']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value', 'branch']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value', 'branch'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        if os.path.exists(file):
            st.session_state[state_key] = pd.read_csv(file)
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

if 'inventory' not in st.session_state:
    if os.path.exists('inventory_final.csv'):
        # تحويل ملف المخزن إلى ديكشنري مع الحفاظ على مفتاح (الصنف + الفرع)
        df_inv = pd.read_csv('inventory_final.csv')
        st.session_state.inventory = df_inv.to_dict('records')
    else:
        st.session_state.inventory = []

if 'categories' not in st.session_state:
    if os.path.exists('categories_final.csv'):
        st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist()
    else:
        st.session_state.categories = ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

# حالات التشغيل
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق (ستايل أبو عمر الفخم)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; text-align: right; }
    .stApp { background-color: #f0f2f5; }
    .main-title { 
        background: linear-gradient(90deg, #1e3a8a, #10b981);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; font-weight: 900; font-size: 40px; padding: 20px;
    }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-right: 10px solid #10b981; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    .stSidebar [data-testid="stMarkdownContainer"] { color: white; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; font-weight: bold; border: none; }
    .metric-box { background: white; border-right: 5px solid #10b981; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول (النظام المباشر)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_form"):
            u_input = st.text_input("👤 اسم المستخدم").strip()
            p_input = st.text_input("🔑 كلمة المرور", type="password").strip()
            if st.form_submit_button("دخول النظام"):
                current_data = pd.read_csv(get_db_path())
                current_data['user_name'] = current_data['user_name'].astype(str).str.strip()
                current_data['password'] = current_data['password'].astype(str).str.strip()
                
                if u_input == "أبو عمر" and p_input == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                
                match = current_data[(current_data['user_name'] == u_input) & (current_data['password'] == p_input)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "shop"
                    st.session_state.my_branch = match.iloc[0]['branch_name']
                    st.session_state.active_user = u_input
                    st.rerun()
                else:
                    st.error("❌ فشل الدخول. الحساب غير موجود.")
    st.stop()

# 5. القائمة الجانبية
if st.session_state.user_role == "admin":
    st.sidebar.markdown(f"👑 <b>المدير العام</b><br>{st.session_state.active_user}", unsafe_allow_html=True)
    menu = st.sidebar.radio("📋 المهام الرئيسية", ["📊 التقارير المالية", "🏪 إدارة الفروع", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    active_branch = st.sidebar.selectbox("🏠 عرض فرع محدد:", ["كافة الفروع"] + pd.read_csv(get_db_path())['branch_name'].tolist())
else:
    st.sidebar.markdown(f"🏪 <b>فرع: {st.session_state.my_branch}</b>", unsafe_allow_html=True)
    menu = st.sidebar.radio("📋 القائمة", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚨 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- التنفيذ الفعلي للأقسام ---

# 1. إدارة الفروع (للمدير فقط)
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة وتعديل الفروع</h1>", unsafe_allow_html=True)
    col_edit, col_list = st.columns([1, 1.5])
    with col_edit:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        with st.form("add_br_form"):
            n = st.text_input("اسم المحل").strip()
            u = st.text_input("اسم المستخدم").strip()
            p = st.text_input("كلمة المرور").strip()
            if st.form_submit_button("إضافة فرع جديد"):
                if n and u and p:
                    df = pd.read_csv(get_db_path())
                    pd.concat([df, pd.DataFrame([{'branch_name': n, 'user_name': u, 'password': p}])]).to_csv(get_db_path(), index=False)
                    st.success("✅ تم إضافة الفرع بنجاح")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_list:
        st.table(pd.read_csv(get_db_path()))

# 2. نقطة البيع (للمحلات)
elif menu == "🛒 نقطة البيع":
    st.markdown(f"<h1 class='main-title'>🛒 نقطة بيع: {st.session_state.my_branch}</h1>", unsafe_allow_html=True)
    
    # تصفية بضاعة الفرع الحالي
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    if st.session_state.show_cust_fields:
        with st.status("✅ تم البيع! أضف بيانات الزبون (اختياري)"):
            c_n = st.text_input("اسم الزبون")
            c_p = st.text_input("رقم الهاتف")
            if st.button("💾 حفظ البيانات"):
                mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                auto_save(); st.session_state.show_cust_fields = False; st.rerun()
            if st.button("⏩ تخطي"): st.session_state.show_cust_fields = False; st.rerun()
    else:
        st.session_state.p_method = st.radio("طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
        search_q = st.text_input("🔍 ابحث عن صنف...")
        bill_items = []
        
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i.get('قسم') == cat]
            if search_q: items = [i for i in items if search_q in i['item']]
            if items:
                with st.expander(f"📂 {cat}", expanded=True):
                    for it in items:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{it['item']}**\n<small>متوفر: {format_num(it['كمية'])}</small>", unsafe_allow_html=True)
                        mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{it['item']}", horizontal=True)
                        val = clean_num(c3.text_input("المقدار", key=f"v_{it['item']}"))
                        if val > 0:
                            qty = val if mode == "كجم" else val / it['بيع']
                            bill_items.append({"item": it['item'], "qty": qty, "amount": val if mode == "₪" else val * it['بيع'], "profit": (it['بيع'] - it['شراء']) * qty, "cat": cat})
        
        if st.button("🚀 إتمام البيع", type="primary") and bill_items:
            b_id = str(uuid.uuid4())[:8]
            for e in bill_items:
                # خصم من المخزن العام
                for i in st.session_state.inventory:
                    if i['item'] == e['item'] and i['branch'] == st.session_state.my_branch:
                        i['كمية'] -= e['qty']
                # تسجيل المبيعات
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id, 'branch': st.session_state.my_branch}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
            st.session_state.current_bill_id = b_id
            auto_save(); st.session_state.show_cust_fields = True; st.rerun()

# 3. المخزن والجرد (للمحلات)
elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة المخزن والجرد</h1>", unsafe_allow_html=True)
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    
    tab1, tab2 = st.tabs(["📋 قائمة الأصناف", "⚖️ جرد المخزن"])
    with tab1:
        st.table(pd.DataFrame(my_inv))
    with tab2:
        new_counts = {}
        for it in my_inv:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{it['item']}** (الحالي: {format_num(it['كمية'])})")
            res = c2.text_input("الكمية الفعلية", key=f"j_{it['item']}")
            if res != "": new_counts[it['item']] = clean_num(res)
        if st.button("✔️ اعتماد الجرد"):
            for name, q in new_counts.items():
                for i in st.session_state.inventory:
                    if i['item'] == name and i['branch'] == st.session_state.my_branch:
                        diff = i['كمية'] - q
                        st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': name, 'diff_qty': diff, 'loss_value': diff * i['شراء'], 'branch': st.session_state.my_branch}])], ignore_index=True)
                        i['كمية'] = q
            auto_save(); st.rerun()

# 4. المصروفات
elif menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 سجل المصروفات</h1>", unsafe_allow_html=True)
    with st.form("exp_form"):
        r = st.text_input("البيان (إيجار، كهرباء، الخ)")
        a = st.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ المصروف"):
            new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
            auto_save(); st.rerun()
    st.table(st.session_state.expenses_df[st.session_state.expenses_df['branch'] == st.session_state.my_branch])

# 5. الإعدادات (لإضافة الأصناف)
elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ إعدادات الأصناف</h1>", unsafe_allow_html=True)
    with st.form("add_item_form"):
        col1, col2 = st.columns(2)
        n = col1.text_input("اسم الصنف الجديد")
        cat = col2.selectbox("القسم", st.session_state.categories)
        b = col1.text_input("سعر التكلفة (شراء)")
        s = col2.text_input("سعر البيع")
        q = col1.text_input("الكمية المتوفرة حالياً")
        if st.form_submit_button("إضافة للمخزن"):
            if n:
                st.session_state.inventory.append({
                    "item": n, "قسم": cat, "شراء": clean_num(b), 
                    "بيع": clean_num(s), "كمية": clean_num(q), 
                    "branch": st.session_state.my_branch
                })
                auto_save(); st.success(f"تم إضافة {n} بنجاح!"); st.rerun()

# 6. التقارير المالية (مختصر)
elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية</h1>", unsafe_allow_html=True)
    # تصفية البيانات حسب الفرع المحدد
    if st.session_state.user_role == "admin" and active_branch == "كافة الفروع":
        s_data = st.session_state.sales_df
    else:
        s_data = st.session_state.sales_df[st.session_state.sales_df['branch'] == active_branch]
    
    st.metric("إجمالي المبيعات", f"{format_num(s_data['amount'].sum())} ₪")
    st.metric("إجمالي الأرباح", f"{format_num(s_data['profit'].sum())} ₪")
