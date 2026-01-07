import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر للمحاسبة 2026", layout="wide", page_icon="🍏")

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

# 2. ملفات البيانات
الملفات = {
    'المبيعات': ('sales_v3.csv', ['التاريخ', 'الصنف', 'المبلغ', 'الربح', 'الطريقة', 'اسم_الزبون', 'هاتف_الزبون', 'رقم_الفاتورة']),
    'المصروفات': ('expenses_v3.csv', ['التاريخ', 'البيان', 'المبلغ']),
    'التالف': ('waste_v3.csv', ['التاريخ', 'الصنف', 'الكمية', 'قيمة_الخسارة']),
    'تسويات_الجرد': ('adjust_v3.csv', ['التاريخ', 'الصنف', 'الفارق_الوزني', 'الفارق_المالي'])
}

for مفتاح, (ملف, أعمدة) in الملفات.items():
    اسم_الحالة = f"بيانات_{مفتاح}"
    if اسم_الحالة not in st.session_state:
        if os.path.exists(ملف):
            df = pd.read_csv(ملف)
            df['التاريخ'] = pd.to_datetime(df['التاريخ']).dt.strftime('%Y-%m-%d %H:%M')
            st.session_state[اسم_الحالة] = df
        else:
            st.session_state[اسم_الحالة] = pd.DataFrame(columns=أعمدة)

if 'المخزن' not in st.session_state:
    st.session_state.المخزن = pd.read_csv('inventory_v3.csv', index_col=0).to_dict('index') if os.path.exists('inventory_v3.csv') else {}
if 'الأقسام' not in st.session_state:
    st.session_state.الأقسام = pd.read_csv('categories_v3.csv')['name'].tolist() if os.path.exists('categories_v3.csv') else ["خضار وفواكه", "مكسرات"]

def حفظ_تلقائي():
    pd.DataFrame(st.session_state.المخزن).T.to_csv('inventory_v3.csv')
    st.session_state.بيانات_المبيعات.to_csv('sales_v3.csv', index=False)
    st.session_state.بيانات_المصروفات.to_csv('expenses_v3.csv', index=False)
    st.session_state.بيانات_التالف.to_csv('waste_v3.csv', index=False)
    st.session_state.بيانات_تسويات_الجرد.to_csv('adjust_v3.csv', index=False)
    pd.DataFrame(st.session_state.الأقسام, columns=['name']).to_csv('categories_v3.csv', index=False)

# 3. الواجهة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .main-title { color: #2c3e50; text-align: center; border-bottom: 4px solid #27ae60; padding-bottom: 10px; font-weight: 900; }
    .report-card { background-color: #f1f3f4; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 دخول نظام أبو عمر</h1>", unsafe_allow_html=True)
    with st.container():
        _, col_login, _ = st.columns([1,1,1])
        with col_login:
            pwd = st.text_input("كلمة المرور", type="password")
            if st.button("دخول"):
                if pwd == "123": st.session_state.logged_in = True; st.rerun()
                else: st.error("خطأ!")
else:
    st.sidebar.markdown("<h2 style='color:#27ae60; text-align:center;'>أهلاً أبو عمر</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المتقدمة", "⚙️ الإعدادات"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear(); st.rerun()

    # --- 1. شاشة البيع (نفس الكود السابق مع التأكد من حفظ الطريقة) ---
    if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع</h1>", unsafe_allow_html=True)
        # (كود البيع يبقى كما هو في النسخة السابقة لضمان الاستقرار)
        # ملاحظة: تم التأكد من حفظ "الطريقة" (نقداً/تطبيق) في الفاتورة.
        if 'p_method' not in st.session_state: st.session_state.p_method = "نقداً"
        col_pay1, col_pay2 = st.columns([3,1])
        with col_pay2:
            st.session_state.p_method = st.radio("الدفع:", ["نقداً", "تطبيق"], horizontal=True)
        
        # ... تكملة كود البيع المختصر للحفظ ...
        بحث = st.text_input("🔍 ابحث عن صنف...")
        سلة = []
        for اسم, داتا in st.session_state.المخزن.items():
            if بحث in اسم:
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{اسم}**")
                نوع = c2.radio("بـ", ["₪", "كجم"], key=f"t_{اسم}", horizontal=True)
                قيمة = تنظيف_رقم(c3.text_input("المقدار", key=f"v_{اسم}"))
                if قيمة > 0:
                    كمية = قيمة if نوع == "كجم" else قيمة / داتا["بيع"]
                    سلة.append({"ص": اسم, "ك": كمية, "م": قيمة if نوع == "₪" else قيمة * داتا["بيع"], "ر": (داتا["بيع"]-داتا["شراء"])*كمية})
        
        if st.button("✅ تأكيد البيع"):
            if سلة:
                رقم_ف = str(uuid.uuid4())
                لآن = datetime.now().strftime("%Y-%m-%d %H:%M")
                for غ في سلة:
                    st.session_state.المخزن[غ["ص"]]["كمية"] -= غ["ك"]
                    جديد = {'التاريخ': لآن, 'الصنف': غ['ص'], 'المبلغ': غ['م'], 'الربح': غ['ر'], 'الطريقة': st.session_state.p_method, 'اسم_الزبون': 'زبون عام', 'رقم_الفاتورة': رقم_ف}
                    st.session_state.بيانات_المبيعات = pd.concat([st.session_state.بيانات_المبيعات, pd.DataFrame([جديد])], ignore_index=True)
                حفظ_تلقائي(); st.success("تم الحفظ!"); st.rerun()

    # --- 4. التقارير المتقدمة (التحديث المطلوب) ---
    elif menu == "📊 التقارير المتقدمة":
        st.markdown("<h1 class='main-title'>📊 التقارير المالية والتحليلية</h1>", unsafe_allow_html=True)
        
        # خيارات الفلترة الزمنية
        col_f1, col_f2 = st.columns([1, 2])
        فترة = col_f1.selectbox("اختر الفترة الزمنية:", ["اليوم", "آخر 7 أيام (أسبوعي)", "تاريخ مخصص (من - إلى)"])
        
        تاريخ_بداية = datetime.now().date()
        تاريخ_نهاية = datetime.now().date()
        
        if فترة == "اليوم":
            تاريخ_بداية = datetime.now().date()
        elif فترة == "آخر 7 أيام (أسبوعي)":
            تاريخ_بداية = datetime.now().date() - timedelta(days=7)
        else:
            c_date1, c_date2 = col_f2.columns(2)
            تاريخ_بداية = c_date1.date_input("من تاريخ:", datetime.now().date() - timedelta(days=30))
            تاريخ_نهاية = c_date2.date_input("إلى تاريخ:", datetime.now().date())

        # تصفية البيانات بناءً على التاريخ
        def فلترة_بالتاريخ(df):
            if df.empty: return df
            df['التاريخ_مؤقت'] = pd.to_datetime(df['التاريخ']).dt.date
            filtered = df[(df['التاريخ_مؤقت'] >= تاريخ_بداية) & (df['التاريخ_مؤقت'] <= تاريخ_نهاية)]
            return filtered

        مبيعات_مفلترة = فلترة_بالتاريخ(st.session_state.بيانات_المبيعات)
        مصروفات_مفلترة = فلترة_بالتاريخ(st.session_state.بيانات_المصروفات)
        تالف_مفلتر = فلترة_بالتاريخ(st.session_state.بيانات_التالف)
        جرد_مفلتر = فلترة_بالتاريخ(st.session_state.بيانات_تسويات_الجرد)

        # الحسابات المالية
        أرباح_صافية = مبيعات_مفلترة['الربح'].sum()
        إجمالي_مبيعات = مبيعات_مفلترة['المبلغ'].sum()
        إجمالي_مصاريف = مصروفات_مفلترة['المبلغ'].sum()
        إجمالي_خسائر = تالف_مفلتر['قيمة_الخسارة'].sum() + جرد_مفلتر['الفارق_المالي'].sum()
        الربح_النهائي = أرباح_صافية - إجمالي_مصاريف - إجمالي_خسائر

        # عرض البطاقات المالية
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='report-card'><h3>إجمالي المبيعات</h3><h2>{تنسيق_رقم(إجمالي_مبيعات)} ₪</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='report-card'><h3>المصروفات</h3><h2>{تنسيق_رقم(إجمالي_مصاريف)} ₪</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='report-card'><h3>العجز والتالف</h3><h2>{تنسيق_رقم(إجمالي_خسائر)} ₪</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div style='background-color:#27ae60; color:white;' class='report-card'><h3>الربح الصافي</h3><h2>{تنسيق_رقم(الربح_النهائي)} ₪</h2></div>", unsafe_allow_html=True)

        st.markdown("---")
        
        # جدول تفاصيل المبيعات مع (طريقة الدفع والزبون)
        st.subheader("📋 تفاصيل المبيعات خلال الفترة المختارة")
        if not مبيعات_مفلترة.empty:
            # تجميع حسب رقم الفاتورة لإظهار كل فاتورة كسطر واحد
            جدول_الفواتير = مبيعات_مفلترة.groupby('رقم_الفاتورة').agg({
                'التاريخ': 'first',
                'اسم_الزبون': 'first',
                'الطريقة': 'first',
                'المبلغ': 'sum',
                'الربح': 'sum'
            }).sort_values('التاريخ', ascending=False)
            
            st.table(جدول_الفواتير.rename(columns={
                'التاريخ': 'التاريخ والوقت',
                'اسم_الزبون': 'اسم الزبون',
                'الطريقة': 'طريقة الدفع (نقداً/تطبيق)',
                'المبلغ': 'قيمة الفاتورة',
                'الربح': 'ربح الفاتورة'
            }))
        else:
            st.info("لا توجد مبيعات في هذه الفترة.")

    # --- باقي الأقسام (المخزن والمصروفات والإعدادات) تبقى كما هي ---
    elif menu == "📦 المخزن والجرد":
        st.markdown("<h1 class='main-title'>📦 إدارة المخزن</h1>")
        st.table(pd.DataFrame([{"الصنف": k, "الكمية": v['كمية']} for k, v in st.session_state.المخزن.items()]))
