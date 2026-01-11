import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

# تصفير الكاش لضمان تحديث البيانات فوراً
if 'needs_refresh' not in st.session_state:
    st.session_state.needs_refresh = False

# 2. تصميم الواجهة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-right: 8px solid #27ae60; padding-right: 15px; margin-bottom: 25px; }
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 3. الاتصال والمزامنة
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_to_google():
    try:
        # تحويل القاموس إلى DataFrame للمخزن
        inv_data = [{'item': k, **v} for k, v in st.session_state.inventory.items()]
        
        # تحديث كل الجداول في جوجل شيت
        conn.update(worksheet="Inventory", data=pd.DataFrame(inv_data))
        conn.update(worksheet="Sales", data=st.session_state.sales_df)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        
        # أهم خطوة: تنظيف الذاكرة المؤقتة تماماً
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"خطأ في المزامنة: {e}")
        return False

# 4. تحميل البيانات (مع ضمان عدم استخدام كاش قديم)
def load_data():
    try:
        inv_df = conn.read(worksheet="Inventory", ttl=0)
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        st.session_state.sales_df = conn.read(worksheet="Sales", ttl=0)
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        pass

if 'inventory' not in st.session_state:
    load_data()

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# 5. القائمة الجانبية
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>أهلاً أبو عمر 👋</h2>", unsafe_allow_html=True)
    menu = st.radio("انتقل إلى:", ["🛒 نقطة البيع", "📊 التقارير المالية", "💸 المصروفات", "📦 المخزن والجرد", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث شامل للبيانات"): 
        st.cache_data.clear()
        load_data()
        st.rerun()

# --- المنطق الرئيسي ---

if menu == "💸 المصروفات":
    st.markdown("<h1 class='main-title'>💸 إدارة المصروفات</h1>", unsafe_allow_html=True)
    
    # نموذج الإضافة
    with st.form("exp_form"):
        col1, col2 = st.columns(2)
        r = col1.text_input("البيان")
        a = col2.number_input("المبلغ", min_value=0.0)
        if st.form_submit_button("حفظ"):
            if r and a > 0:
                new_exp = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a}
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_exp])], ignore_index=True)
                sync_to_google()
                st.rerun()

    st.markdown("### سجل المصروفات")
    if not st.session_state.expenses_df.empty:
        # عرض المصروفات مع زر حذف حقيقي
        for index, row in st.session_state.expenses_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
            c1.write(row['date'])
            c2.write(row['reason'])
            c3.write(f"{row['amount']} ₪")
            if c4.button("🗑️", key=f"del_{index}"):
                # حذف من الذاكرة
                st.session_state.expenses_df = st.session_state.expenses_df.drop(index).reset_index(drop=True)
                # مزامنة فورية ومسح الكاش
                sync_to_google()
                st.success("تم الحذف وتحديث التقارير")
                st.rerun()
    else:
        st.info("لا توجد مصروفات.")

elif menu == "📊 التقارير المالية":
    st.markdown("<h1 class='main-title'>📊 التقارير المالية المحدثة</h1>", unsafe_allow_html=True)
    
    # قراءة البيانات مباشرة من session_state لضمان أنها النسخة الأخيرة بعد الحذف
    df_sales = st.session_state.sales_df.copy()
    df_exp = st.session_state.expenses_df.copy()
    
    # تحويل التواريخ والأرقام
    df_sales['date'] = pd.to_datetime(df_sales['date']).dt.date
    df_sales['profit'] = pd.to_numeric(df_sales['profit'], errors='coerce').fillna(0)
    
    if not df_exp.empty:
        df_exp['date'] = pd.to_datetime(df_exp['date']).dt.date
        df_exp['amount'] = pd.to_numeric(df_exp['amount'], errors='coerce').fillna(0)
    
    today = datetime.now().date()
    
    # الحسابات
    t_gross_profit = df_sales[df_sales['date'] == today]['profit'].sum()
    t_exp = df_exp[df_exp['date'] == today]['amount'].sum() if not df_exp.empty else 0
    t_net_profit = t_gross_profit - t_exp

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي ربح المبيعات (اليوم)", f"{t_gross_profit} ₪")
    col2.metric("إجمالي المصروفات (اليوم)", f"- {t_exp} ₪", delta_color="inverse")
    col3.metric("صافي الربح النهائي", f"{t_net_profit} ₪")

    st.divider()
    st.write("### فحص جدول المصروفات الحالي في التقارير:")
    st.table(df_exp[df_exp['date'] == today])

# (بقية الأقسام تظل كما هي في كودك الأصلي)
