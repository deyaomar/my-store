import streamlit as st
import pandas as pd
import os

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="👑")

# دالة برمجية للتأكد من جودة الأرقام
def format_num(val):
    try:
        if val == int(val): return str(int(val))
        return str(round(val, 2))
    except: return str(val)

# --- نظام إدارة الملفات الصارم ---
def force_read_branches():
    """قراءة مباشرة وحيّة للملف لضمان رؤية المستخدمين الجدد فوراً"""
    path = 'branches_config.csv'
    cols = ['branch_name', 'user_name', 'password']
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            df = pd.read_csv(path)
            # تنظيف الفراغات من النصوص لضمان مطابقة كلمة السر
            for c in df.columns:
                if df[c].dtype == 'object':
                    df[c] = df[c].astype(str).str.strip()
            return df
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame([{'branch_name': 'المحل الرئيسي', 'user_name': 'admin', 'password': '123'}])

def force_save_branches(df):
    """حفظ فعلي في الملف مع التأكد من الكتابة على القرص"""
    df.to_csv('branches_config.csv', index=False)
    # تحديث الذاكرة فوراً بعد الحفظ
    st.session_state.branches_db = df

# 2. تحميل البيانات الأولية
if 'branches_db' not in st.session_state:
    st.session_state.branches_db = force_read_branches()

# تحميل بقية الجداول (مبيعات، مصاريف، مخزن)
def load_data():
    if 'sales_df' not in st.session_state:
        if os.path.exists('sales_final.csv'): st.session_state.sales_df = pd.read_csv('sales_final.csv')
        else: st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id', 'branch', 'cat'])
    
    if 'expenses_df' not in st.session_state:
        if os.path.exists('expenses_final.csv'): st.session_state.expenses_df = pd.read_csv('expenses_final.csv')
        else: st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount', 'branch'])

    if 'inventory' not in st.session_state:
        if os.path.exists('inventory_final.csv'): st.session_state.inventory = pd.read_csv('inventory_final.csv').to_dict('records')
        else: st.session_state.inventory = []

    if 'categories' not in st.session_state:
        st.session_state.categories = ["خضار وفواكه", "مكسرات", "ألبان", "منظفات"]

load_data()

# 3. التصميم الفخم (ستايل أبو عمر)
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
    </style>
    """, unsafe_allow_html=True)

# 4. بوابة الدخول (مُحدثة بالكامل لتقرأ الملف فوراً)
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔐 نظام الإدارة الذكي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_form"):
            u_input = st.text_input("👤 اسم المستخدم").strip()
            p_input = st.text_input("🔑 كلمة المرور", type="password").strip()
            submit = st.form_submit_button("دخول النظام")
            
            if submit:
                # 1. فحص المدير العام
                if u_input == "أبو عمر" and p_input == "admin":
                    st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, "admin", "أبو عمر"
                    st.rerun()
                
                # 2. فحص الفروع من الملف مباشرة (Live Check)
                current_db = force_read_branches()
                match = current_db[(current_db['user_name'] == u_input) & (current_db['password'] == p_input)]
                
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "shop"
                    st.session_state.my_branch = match.iloc[0]['branch_name']
                    st.session_state.active_user = u_input
                    st.rerun()
                else:
                    st.error("❌ البيانات غير موجودة. تأكد من الحفظ في لوحة الإدارة أولاً.")
    st.stop()

# 5. القائمة الجانبية
if st.session_state.user_role == "admin":
    st.sidebar.markdown(f"<div style='background:#10b981; padding:20px; border-radius:15px; text-align:center; margin-bottom:20px;'>👑 <b>المدير العام</b><br>{st.session_state.active_user}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("📋 المهام الرئيسية", ["📊 التقارير المالية", "🏪 إدارة الفروع", "📦 توريد بضاعة", "⚙️ الإعدادات"])
    active_branch = st.sidebar.selectbox("🏠 عرض فرع محدد:", ["كافة الفروع"] + st.session_state.branches_db['branch_name'].tolist())
else:
    st.sidebar.markdown(f"<div style='background:#3b82f6; padding:20px; border-radius:15px; text-align:center; margin-bottom:20px;'>🏪 <b>فرع: {st.session_state.my_branch}</b></div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("📋 القائمة", ["🛒 نقطة البيع", "📦 المخزن"])
    active_branch = st.session_state.my_branch

if st.sidebar.button("🚨 تسجيل الخروج"):
    st.session_state.clear(); st.rerun()

# --- قسم 2: إدارة الفروع (تم تقوية نظام الحفظ هنا) ---
if menu == "🏪 إدارة الفروع":
    st.markdown("<h1 class='main-title'>🏪 إدارة وتعديل الفروع</h1>", unsafe_allow_html=True)
    col_edit, col_list = st.columns([1, 1.5])
    
    with col_edit:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        t_add, t_edit, t_del = st.tabs(["➕ إضافة", "📝 تعديل", "❌ حذف"])
        
        with t_add:
            with st.form("add_branch_form", clear_on_submit=True):
                new_n = st.text_input("اسم المحل").strip()
                new_u = st.text_input("اسم المستخدم").strip()
                new_p = st.text_input("كلمة المرور").strip()
                if st.form_submit_button("حفظ الفرع الآن"):
                    if new_n and new_u and new_p:
                        # قراءة الملف، إضافة السطر، ثم الحفظ الفعلي
                        temp_db = force_read_branches()
                        new_data = pd.DataFrame([{'branch_name': new_n, 'user_name': new_u, 'password': new_p}])
                        updated_db = pd.concat([temp_db, new_data], ignore_index=True)
                        force_save_branches(updated_db)
                        st.success(f"✅ تم الحفظ! جرب الدخول الآن بـ {new_u}")
                        st.rerun()
        
        with t_edit:
            if not st.session_state.branches_db.empty:
                target = st.selectbox("اختر للتعديل", st.session_state.branches_db['branch_name'].tolist())
                curr = st.session_state.branches_db[st.session_state.branches_db['branch_name'] == target].iloc[0]
                with st.form("edit_f"):
                    en = st.text_input("الاسم", value=curr['branch_name'])
                    eu = st.text_input("المستخدم", value=curr['user_name'])
                    ep = st.text_input("الكلمة", value=curr['password'])
                    if st.form_submit_button("تحديث"):
                        db = force_read_branches()
                        db.loc[db['branch_name'] == target, ['branch_name', 'user_name', 'password']] = [en, eu, ep]
                        force_save_branches(db); st.rerun()
        
        with t_del:
            d_target = st.selectbox("حذف نهائي", st.session_state.branches_db['branch_name'].tolist())
            if st.button("تأكيد الحذف"):
                db = force_read_branches()
                db = db[db['branch_name'] != d_target]
                force_save_branches(db); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_list:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📋 الفروع المسجلة في النظام")
        # إعادة قراءة لضمان عرض الحقيقة
        st.table(force_read_branches().rename(columns={'branch_name':'المحل','user_name':'المستخدم','password':'الكلمة'}))
        st.markdown("</div>", unsafe_allow_html=True)

# --- بقية الأقسام (التقارير، التوريد، الإعدادات) ---
elif menu == "📊 التقارير المالية":
    st.markdown(f"<h1 class='main-title'>📊 التقارير المالية: {active_branch}</h1>", unsafe_allow_html=True)
    # كود التقارير المعرب...
    st.info("قسم التقارير المالية نشط.")

elif menu == "📦 توريد بضاعة":
    st.markdown("<h1 class='main-title'>📦 توريد بضاعة</h1>", unsafe_allow_html=True)
    # كود التوريد...
