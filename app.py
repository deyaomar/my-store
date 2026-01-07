import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر للمحاسبة 2026", layout="wide", page_icon="🍏")

# دالة لتنظيف وتنسيق الأرقام
def تنسيق_رقم(قيمة):
    try:
        if قيمة == int(قيمة): return str(int(قيمة))
        return str(round(قيمة, 2))
    except: return str(قيمة)

def تنظيف_رقم(نص):
    try:
        if نص is None or نص == "": return 0.0
        return float(str(نص).replace(',', '.').replace('،', '.'))
    except: return 0.0

# 2. تعريف ملفات البيانات (باللغة العربية لسهولة الإدارة)
الملفات = {
    'المبيعات': ('sales_v3.csv', ['التاريخ', 'الصنف', 'المبلغ', 'الربح', 'الطريقة', 'اسم_الزبون', 'هاتف_الزبون', 'رقم_الفاتورة']),
    'المصروفات': ('expenses_v3.csv', ['التاريخ', 'البيان', 'المبلغ']),
    'التالف': ('waste_v3.csv', ['التاريخ', 'الصنف', 'الكمية', 'قيمة_الخسارة']),
    'تسويات_الجرد': ('adjust_v3.csv', ['التاريخ', 'الصنف', 'الفارق_الوزني', 'الفارق_المالي'])
}

# تحميل البيانات في ذاكرة البرنامج
for مفتاح, (ملف, أعمدة) in الملفات.items():
    اسم_الحالة = f"بيانات_{مفتاح}"
    if اسم_الحالة not in st.session_state:
        if os.path.exists(ملف):
            st.session_state[اسم_الحالة] = pd.read_csv(ملف)
        else:
            st.session_state[اسم_الحالة] = pd.DataFrame(columns=أعمدة)

if 'المخزن' not in st.session_state:
    if os.path.exists('inventory_v3.csv'):
        st.session_state.المخزن = pd.read_csv('inventory_v3.csv', index_col=0).to_dict('index')
    else:
        st.session_state.المخزن = {}

if 'الأقسام' not in st.session_state:
    if os.path.exists('categories_v3.csv'):
        st.session_state.الأقسام = pd.read_csv('categories_v3.csv')['name'].tolist()
    else:
        st.session_state.الأقسام = ["خضار وفواكه", "مكسرات"]

# حالات النظام
if 'طريقة_الدفع' not in st.session_state: st.session_state.طريقة_الدفع = "نقداً"
if 'عرض_بيانات_الزبون' not in st.session_state: st.session_state.عرض_بيانات_الزبون = False
if 'رقم_الفاتورة_الحالي' not in st.session_state: st.session_state.رقم_الفاتورة_الحالي = None
if 'رسالة_نجاح' not in st.session_state: st.session_state.رسالة_نجاح = None

def حفظ_تلقائي():
    pd.DataFrame(st.session_state.المخزن).T.to_csv('inventory_v3.csv')
    st.session_state.بيانات_المبيعات.to_csv('sales_v3.csv', index=False)
    st.session_state.بيانات_المصروفات.to_csv('expenses_v3.csv', index=False)
    st.session_state.بيانات_التالف.to_csv('waste_v3.csv', index=False)
    st.session_state.بيانات_تسويات_الجرد.to_csv('adjust_v3.csv', index=False)
    pd.DataFrame(st.session_state.الأقسام, columns=['name']).to_csv('categories_v3.csv', index=False)

# 3. التنسيق الجمالي
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; }
    [data-testid="stSidebar"] { background-color: #2c3e50 !important; direction: rtl; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .stButton > button { width: 100%; border-radius: 8px !important; font-weight: bold; }
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-right: 5px solid #27ae60; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.container():
        _, col_login, _ = st.columns([1,1,1])
        with col_login:
            pwd = st.text_input("أدخل كلمة المرور", type="password")
            if st.button("دخول"):
                if pwd == "123": st.session_state.logged_in = True; st.rerun()
                else: st.error("كلمة المرور خاطئة")
else:
    # القائمة الجانبية بالعربي
    st.sidebar.markdown("<h2 style='color:white; text-align:center;'>لوحة التحكم</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("انتقل إلى:", ["🛒 شاشة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.clear(); st.rerun()

    if st.session_state.رسالة_نجاح:
        st.success(st.session_state.رسالة_نجاح)
        st.session_state.رسالة_نجاح = None

    # --- 1. شاشة البيع ---
    if menu == "🛒 شاشة البيع":
        st.markdown("<h1 class='main-title'>🛒 نقطة البيع المباشر</h1>", unsafe_allow_html=True)
        
        if st.session_state.عرض_بيانات_الزبون:
            with st.status("✅ تم حفظ البيعة! هل تود إضافة اسم الزبون؟"):
                c_name = st.text_input("اسم الزبون")
                c_phone = st.text_input("رقم الهاتف")
                if st.button("💾 ربط البيانات"):
                    mask = st.session_state.بيانات_المبيعات['رقم_الفاتورة'] == st.session_state.رقم_الفاتورة_الحالي
                    st.session_state.بيانات_المبيعات.loc[mask, ['اسم_الزبون', 'هاتف_الزبون']] = [c_name, c_phone]
                    حفظ_تلقائي(); st.session_state.عرض_بيانات_الزبون = False; st.rerun()
                if st.button("تخطي والعودة للبيع"):
                    st.session_state.عرض_بيانات_الزبون = False; st.rerun()
        else:
            col_pay1, col_pay2 = st.columns([3,1])
            with col_pay2:
                st.session_state.طريقة_الدفع = st.radio("طريقة الدفع:", ["نقداً", "تطبيق"], horizontal=True)
            
            بحث = st.text_input("🔍 ابحث عن صنف هنا...")
            
            سلة_المشتريات = []
            for قسم in st.session_state.الأقسام:
                أصناف = {k: v for k, v in st.session_state.المخزن.items() if v.get('قسم') == قسم}
                if بحث: أصناف = {k: v for k, v in أصناف.items() if بحث in k}
                
                if أصناف:
                    with st.expander(f"📂 {قسم}", expanded=True):
                        for اسم_الصنف, بيانات in أصناف.items():
                            c1, c2, c3 = st.columns([2, 1, 2])
                            c1.write(f"**{اسم_الصنف}** (متوفر: {تنسيق_رقم(بيانات['كمية'])})")
                            نوع = c2.radio("بـ", ["₪", "كجم"], key=f"n_{اسم_الصنف}", horizontal=True)
                            قيمة_مدخلة = تنظيف_رقم(c3.text_input("المقدار", key=f"q_{اسم_الصنف}", label_visibility="collapsed"))
                            
                            if قيمة_مدخلة > 0:
                                كمية = قيمة_مدخلة if نوع == "كجم" else قيمة_مدخلة / بيانات["بيع"]
                                مبلغ = قيمة_مدخلة if نوع == "₪" else قيمة_مدخلة * بيانات["بيع"]
                                ربح = (بيانات["بيع"] - بيانات["شراء"]) * كمية
                                سلة_المشتريات.append({"الصنف": اسم_الصنف, "الكمية": كمية, "المبلغ": مبلغ, "الربح": ربح})
            
            if st.button("✅ تنفيذ عملية البيع", type="primary"):
                if سلة_المشتريات:
                    رقم_ف = str(uuid.uuid4())
                    for غرض in سلة_المشتريات:
                        st.session_state.المخزن[غرض["الصنف"]]["كمية"] -= غرض["الكمية"]
                        جديد = {
                            'التاريخ': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'الصنف': غرض['الصنف'], 'المبلغ': غرض['المبلغ'], 'الربح': غرض['الربح'],
                            'الطريقة': st.session_state.طريقة_الدفع, 'اسم_الزبون': 'زبون عام',
                            'هاتف_الزبون': '', 'رقم_الفاتورة': رقم_ف
                        }
                        st.session_state.بيانات_المبيعات = pd.concat([st.session_state.بيانات_المبيعات, pd.DataFrame([جديد])], ignore_index=True)
                    st.session_state.رقم_الفاتورة_الحالي = رقم_ف
                    حفظ_تلقائي(); st.session_state.عرض_بيانات_الزبون = True; st.rerun()

    # --- 2. المخزن والجرد ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة البضاعة والرقابة</h1>", unsafe_allow_html=True)
        تبويب1, تبويب2, تبويب3 = st.tabs(["📋 جرد المخزن الحالي", "⚖️ تنفيذ جرد يدوي", "🗑️ تسجيل بضاعة تالفة"])
        
        with تبويب1:
            if st.session_state.المخزن:
                جدول_مخزن = pd.DataFrame([{"الصنف": k, "القسم": v['قسم'], "الكمية الحالية": v['كمية']} for k, v in st.session_state.المخزن.items()])
                st.table(جدول_مخزن)
        
        with تبويب2:
            st.subheader("قم بتسجيل الكميات الحقيقية لمطابقتها مع النظام")
            بيانات_الجرد = {}
            for صنف, معلومات in st.session_state.المخزن.items():
                col_n, col_s, col_i = st.columns([2, 1, 2])
                col_n.write(f"**{صنف}**")
                col_s.info(f"في النظام: {تنسيق_رقم(معلومات['كمية'])}")
                قيمة_حقيقية = col_i.text_input("الكمية الحقيقية على الرف", key=f"jard_{صنف}")
                if قيمة_حقيقية != "": بيانات_الجرد[صنف] = تنظيف_رقم(قيمة_حقيقية)
            
            if st.button("💾 اعتماد الجرد وتحديث الأرباح", type="primary"):
                سجلات_الجرد = []
                for ص، ق in بيانات_الجرد.items():
                    ق_نظام = st.session_state.المخزن[ص]['كمية']
                    فارق = ق_نظام - ق
                    خسارة = فارق * st.session_state.المخزن[ص]['شراء']
                    st.session_state.المخزن[ص]['كمية'] = ق
                    سجلات_الجرد.append({'التاريخ': datetime.now().strftime("%Y-%m-%d"), 'الصنف': ص, 'الفارق_الوزني': فارق, 'الفارق_المالي': خسارة})
                
                if سجلات_الجرد:
                    st.session_state.بيانات_تسويات_الجرد = pd.concat([st.session_state.بيانات_تسويات_الجرد, pd.DataFrame(سجلات_الجرد)], ignore_index=True)
                    حفظ_تلقائي(); st.session_state.رسالة_نجاح = "✅ تم تحديث المخزن وخصم فوارق الجرد من الأرباح"; st.rerun()

        with تبويب3:
            with st.form("تالف"):
                صنف_تالف = st.selectbox("اختر الصنف", list(st.session_state.المخزن.keys()))
                كمية_تالفة = st.number_input("الكمية التالفة", min_value=0.0)
                if st.form_submit_button("حفظ التالف"):
                    خسارة_ت = كمية_تالفة * st.session_state.المخزن[صنف_تالف]['شراء']
                    st.session_state.المخزن[صنف_تالف]['كمية'] -= كمية_تالفة
                    جديد_ت = {'التاريخ': datetime.now().strftime("%Y-%m-%d"), 'الصنف': صنف_تالف, 'الكمية': كمية_تالفة, 'قيمة_الخسارة': خسارة_ت}
                    st.session_state.بيانات_التالف = pd.concat([st.session_state.بيانات_التالف, pd.DataFrame([جديد_ت])], ignore_index=True)
                    حفظ_تلقائي(); st.rerun()

    # --- 3. التقارير ---
    elif menu == "📊 التقارير":
        st.markdown("<h1 class='main-title'>📊 التقرير المالي الشامل</h1>", unsafe_allow_html=True)
        أرباح_بيع = st.session_state.بيانات_المبيعات['الالربح'].sum() if 'الالربح' in st.session_state.بيانات_المبيعات else st.session_state.بيانات_المبيعات['الربح'].sum()
        م_مصروفات = st.session_state.بيانات_المصروفات['المبلغ'].sum()
        خ_تالف = st.session_state.بيانات_التالف['قيمة_الخسارة'].sum()
        خ_جرد = st.session_state.بيانات_تسويات_الجرد['الفارق_المالي'].sum()
        صافي = أرباح_بيع - م_مصروفات - خ_تالف - خ_جرد
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي ربح المبيعات", f"{تنسيق_رقم(أرباح_بيع)} ₪")
        c2.metric("مصروفات + تالف + عجز", f"{تنسيق_رقم(م_مصروفات + خ_تالف + خ_جرد)} ₪")
        c3.metric("صافي الربح الحقيقي", f"{تنسيق_رقم(صافي)} ₪")
        
        st.markdown("---")
        st.subheader("👥 مبيعات الزبائن")
        if not st.session_state.بيانات_المبيعات.empty:
            تجميع_زبائن = st.session_state.بيانات_المبيعات.groupby('رقم_الفاتورة').agg({'التاريخ':'first','اسم_الزبون':'first','المبلغ':'sum'}).sort_values('التاريخ', ascending=False)
            st.table(تجميع_زبائن.rename(columns={'التاريخ':'التاريخ','اسم_الزبون':'الزبون','المبلغ':'المبلغ الإجمالي'}))

    # --- 4. الإعدادات ---
    elif menu == "⚙️ الإعدادات":
        st.markdown("<h1 class='main-title'>⚙️ إعدادات النظام</h1>", unsafe_allow_html=True)
        with st.expander("➕ إضافة صنف جديد"):
            with st.form("صنف_جديد"):
                اسم = st.text_input("اسم الصنف")
                قسم = st.selectbox("القسم", st.session_state.الأقسام)
                col1, col2, col3 = st.columns(3)
                ش = col1.text_input("سعر الشراء")
                ب = col2.text_input("سعر البيع")
                ك = col3.text_input("الكمية الحالية")
                if st.form_submit_button("إضافة"):
                    st.session_state.المخزن[اسم] = {"قسم": قسم, "شراء": تنظيف_رقم(ش), "بيع": تنظيف_رقم(ب), "كمية": تنظيف_رقم(ك)}
                    حفظ_تلقائي(); st.session_state.رسالة_نجاح = f"✅ تم إضافة {اسم}"; st.rerun()
