import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📊")

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

# 2. إدارة ملفات البيانات
FILES = {
    'sales': ('sales_final.csv', ['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'customer_phone', 'bill_id']),
    'expenses': ('expenses_final.csv', ['date', 'reason', 'amount']),
    'waste': ('waste_final.csv', ['date', 'item', 'qty', 'loss_value']),
    'adjust': ('inventory_adjustments.csv', ['date', 'item', 'diff_qty', 'loss_value'])
}

for key, (file, cols) in FILES.items():
    state_key = f"{key}_df"
    if state_key not in st.session_state:
        if os.path.exists(file):
            df = pd.read_csv(file)
            for c in cols: 
                if c not in df.columns: df[c] = 0.0 if 'amount' in c or 'profit' in c or 'loss' in c or 'qty' in c else ""
            st.session_state[state_key] = df
        else:
            st.session_state[state_key] = pd.DataFrame(columns=cols)

# --- إصلاح مشكلة قراءة المخزن والتكرار ---
if 'inventory' not in st.session_state:
    if os.path.exists('inventory_final.csv'):
        try:
            inv_df = pd.read_csv('inventory_final.csv')
            # إذا وجد تكرار في أول عمود (الأسماء)، نحذف المكرر ونبقي الأحدث
            inv_df = inv_df.drop_duplicates(subset=[inv_df.columns[0]], keep='last')
            st.session_state.inventory = inv_df.set_index(inv_df.columns[0]).to_dict('index')
        except Exception as e:
            st.error(f"خطأ في قراءة ملف المخزن: {e}")
            st.session_state.inventory = {}
    else:
        st.session_state.inventory = {}

if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

# حالات التشغيل
if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None

# --- إصلاح دالة الحفظ لضمان عدم التكرار ---
def auto_save():
    if st.session_state.inventory:
        inv_df_to_save = pd.DataFrame.from_dict(st.session_state.inventory, orient='index')
        inv_df_to_save.to_csv('inventory_final.csv', index=True)
    
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. واجهة المستخدم (CSS)
# --- 1. التنسيق الشامل والاحترافي (CSS) ---
st.markdown("""
    <style>
    /* استيراد خط تجوال بجميع الأوزان */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    /* إعدادات الخط والاتجاه العام */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* القائمة الجانبية - خلفية سوداء فخمة */
    [data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-left: 3px solid #27ae60;
        min-width: 320px !important;
    }

    /* منطقة الترحيب بأبو عمر */
    .welcome-box {
        background-color: #1a1a1a;
        padding: 30px 10px;
        border-radius: 15px;
        margin-bottom: 25px;
        border: 2px solid #27ae60;
        text-align: center;
    }
    .welcome-box h1 {
        color: #27ae60 !important;
        font-weight: 900 !important;
        font-size: 28px !important;
        margin: 0;
    }

    /* تنسيق أزرار القائمة الجانبية (الخط أبيض وعريض جداً) */
    [data-testid="stSidebar"] .stRadio div label {
        background-color: #1a1a1a !important;
        color: #ffffff !important; /* لون الخط أبيض */
        padding: 18px 25px !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
        border: 1px solid #333 !important;
        font-size: 20px !important; /* حجم خط كبير */
        font-weight: 900 !important; /* خط عريض جداً */
        transition: all 0.2s ease-in-out;
        display: flex;
        justify-content: flex-start;
    }

    /* تأثير عند اختيار القسم */
    [data-testid="stSidebar"] .stRadio div label[data-checked="true"] {
        background-color: #27ae60 !important; /* أخضر عند الاختيار */
        color: #ffffff !important;
        border: 1px solid #ffffff !important;
        box-shadow: 0 5px 15px rgba(39, 174, 96, 0.4);
    }

    /* عند تمرير الماوس فوق الأزرار */
    [data-testid="stSidebar"] .stRadio div label:hover {
        background-color: #333 !important;
        border-color: #27ae60 !important;
        cursor: pointer;
    }

    /* إخفاء دوائر الراديو الافتراضية */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > span:first-child {
        display: none !important;
    }

    /* العناوين الرئيسية في الصفحة */
    .main-title {
        color: #1a1a1a;
        font-weight: 900;
        font-size: 35px;
        border-bottom: 5px solid #27ae60;
        display: inline-block;
        padding-bottom: 10px;
        margin-bottom: 40px;
    }

    /* تنسيق زر تسجيل الخروج */
    .stButton>button {
        background-color: #e74c3c !important;
        color: white !important;
        font-weight: 900 !important;
        height: 50px;
        border-radius: 10px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تنفيذ القائمة الجانبية (Sidebar) ---
with st.sidebar:
    # المربع الترحيبي
    st.markdown("""
        <div class='welcome-box'>
            <h1>أهلاً أبو عمر 👋</h1>
            <p style='color: white; font-weight: 700; margin-top: 10px;'>نظام الإدارة المتكامل</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='color: #888; font-weight: 900; font-size: 16px; margin-right: 10px;'>إختر الوجهة:</p>", unsafe_allow_html=True)
    
    # القائمة الرئيسية
    menu = st.radio(
        "Navigation",
        ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"],
        label_visibility="collapsed"
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # زر الخروج
    if st.button("🚪 خروج من النظام", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 3. العناوين داخل الصفحات ---
if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 شاشة البيع المباشر</h1>", unsafe_allow_html=True)
    # باقي كود نقطة البيع هنا...

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 إدارة بضاعة المخزن</h1>", unsafe_allow_html=True)
    # باقي كود المخزن هنا...

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير والأرباح</h1>", unsafe_allow_html=True)
    # باقي كود التقارير هنا...
# 4. نظام تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    st.sidebar.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("التنقل السريع", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج آمن"):
        st.session_state.clear(); st.rerun()

    # --- 1. نقطة البيع ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
        if st.session_state.show_cust_fields:
            with st.status("✅ تم حفظ الفاتورة!"):
                c_n = st.text_input("اسم الزبون")
                c_p = st.text_input("رقم الهاتف")
                if st.button("💾 حفظ وربط"):
                    mask = st.session_state.sales_df['bill_id'] == st.session_state.current_bill_id
                    st.session_state.sales_df.loc[mask, ['customer_name', 'customer_phone']] = [c_n, c_p]
                    auto_save(); st.session_state.show_cust_fields = False; st.rerun()
                if st.button("⏩ تخطي"): st.session_state.show_cust_fields = False; st.rerun()
        else:
            st.session_state.p_method = st.radio("طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
            search_q = st.text_input("🔍 ابحث عن صنف...")
            bill_items = []
            for cat in st.session_state.categories:
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                if search_q: items = {k: v for k, v in items.items() if search_q in k}
                if items:
                    with st.expander(f"📂 {cat}", expanded=True):
                        for item, data in items.items():
                            c1, c2, c3 = st.columns([2, 1, 2])
                            c1.markdown(f"**{item}**\n<small>متوفر: {format_num(data['كمية'])}</small>", unsafe_allow_html=True)
                            mode = c2.radio("بـ", ["₪", "كجم"], key=f"m_{item}", horizontal=True)
                            val = clean_num(c3.text_input("المقدار", key=f"v_{item}"))
                            if val > 0:
                                qty = val if mode == "كجم" else val / data["بيع"]
                                bill_items.append({"item": item, "qty": qty, "amount": val if mode == "₪" else val * data["بيع"], "profit": (data["بيع"] - data["شراء"]) * qty})
            
            if st.button("🚀 إتمام البيع", type="primary"):
                if bill_items:
                    b_id = str(uuid.uuid4())[:8]
                    for e in bill_items:
                        st.session_state.inventory[e["item"]]["كمية"] -= e["qty"]
                        new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': e['item'], 'amount': e['amount'], 'profit': e['profit'], 'method': st.session_state.p_method, 'customer_name': 'زبون عام', 'customer_phone': '', 'bill_id': b_id}
                        st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                    st.session_state.current_bill_id = b_id
                    auto_save(); st.session_state.show_cust_fields = True; st.rerun()

    # --- 2. المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>", unsafe_allow_html=True)
        t_list, t_jard, t_waste = st.tabs(["📋 الرصيد", "⚖️ الجرد", "🗑️ التالف"])
        with t_list: 
            if st.session_state.inventory:
                df_inv = pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية": v['كمية']} for k, v in st.session_state.inventory.items()])
                st.dataframe(df_inv, use_container_width=True)
            else: st.write("المخزن فارغ")
            
        with t_jard:
            new_counts = {}
            for item, data in st.session_state.inventory.items():
                c1, c2, c3 = st.columns([2, 1, 2])
                c1.write(f"**{item}**")
                res = c3.text_input("الوزن الحقيقي", key=f"j_{item}")
                if res != "": new_counts[item] = clean_num(res)
            if st.button("✔️ اعتماد الجرد"):
                for it, rq in new_counts.items():
                    diff = st.session_state.inventory[it]['كمية'] - rq
                    st.session_state.adjust_df = pd.concat([st.session_state.adjust_df, pd.DataFrame([{'date': datetime.now().strftime("%Y-%m-%d"), 'item': it, 'diff_qty': diff, 'loss_value': diff * st.session_state.inventory[it]['شراء']}])], ignore_index=True)
                    st.session_state.inventory[it]['كمية'] = rq
                auto_save(); st.rerun()

    # --- 5. الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إدارة الأصناف</h1>", unsafe_allow_html=True)
        with st.form("add_i"):
            n = st.text_input("الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            b = st.text_input("سعر شراء (التكلفة)")
            s = st.text_input("سعر بيع")
            q = st.text_input("الكمية")
            if st.form_submit_button("إضافة / تحديث الصنف"):
                if n:
                    # إضافة الصنف للقاموس (إذا كان موجوداً سيتم تحديثه ولن يتكرر)
                    st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                    auto_save()
                    st.success(f"تم حفظ {n}")
                    st.rerun()
