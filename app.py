import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📦")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .main-title { color: #1a1a1a; font-weight: 900; font-size: 30px; border-right: 8px solid #27ae60; padding-right: 15px; margin-bottom: 25px; }
    .report-card { background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #27ae60; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .stock-card { background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. المزامنة والبيانات
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_to_google():
    try:
        inv_data = [{'item': k, **v} for k, v in st.session_state.inventory.items()]
        conn.update(worksheet="Inventory", data=pd.DataFrame(inv_data))
        conn.update(worksheet="Sales", data=st.session_state.sales_df)
        conn.update(worksheet="Expenses", data=st.session_state.expenses_df)
        conn.update(worksheet="Waste", data=st.session_state.waste_df)
        st.cache_data.clear()
        return True
    except: return False

if 'inventory' not in st.session_state:
    try:
        inv_df = conn.read(worksheet="Inventory", ttl=0)
        st.session_state.inventory = inv_df.set_index('item').to_dict('index') if not inv_df.empty else {}
        st.session_state.sales_df = conn.read(worksheet="Sales", ttl=0)
        st.session_state.expenses_df = conn.read(worksheet="Expenses", ttl=0)
        st.session_state.waste_df = conn.read(worksheet="Waste", ttl=0)
    except:
        st.session_state.inventory = {}; st.session_state.sales_df = pd.DataFrame(columns=['date', 'item', 'amount', 'profit', 'method', 'customer_name', 'bill_id'])
        st.session_state.expenses_df = pd.DataFrame(columns=['date', 'reason', 'amount']); st.session_state.waste_df = pd.DataFrame(columns=['date', 'item', 'qty', 'loss_value'])

if 'CATEGORIES' not in st.session_state:
    st.session_state.CATEGORIES = ["مواد غذائية", "منظفات", "أدوات منزلية", "أخرى"]

# 3. القائمة الجانبية
with st.sidebar:
    st.markdown("### أهلاً أبو عمر 👋")
    menu = st.radio("القائمة:", ["🛒 نقطة البيع", "📦 المخزن والجرد", "📊 التقارير المالية", "⚙️ الإعدادات"])
    if st.button("🔄 تحديث"): st.rerun()

# --- التنفيذ ---

if menu == "🛒 نقطة البيع":
    st.markdown("<h1 class='main-title'>🛒 البيع السريع (كل الأصناف)</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    cat_sel = c1.selectbox("📂 القسم", ["الكل"] + st.session_state.CATEGORIES)
    search = c2.text_input("🔍 ابحث هنا...")
    
    # فلترة وعرض كافة الأصناف دون استثناء
    items = {k: v for k, v in st.session_state.inventory.items() if (cat_sel == "الكل" or v.get('قسم') == cat_sel) and (search.lower() in k.lower())}
    
    cols = st.columns(4) # عرض 4 أصناف في كل سطر حتى تنتهي القائمة بالكامل
    temp_bill = []
    
    for idx, (it, data) in enumerate(items.items()):
        with cols[idx % 4]:
            st.markdown(f"<div style='background:#f9f9f9; border:1px solid #ddd; padding:10px; border-radius:10px; text-align:center;'><b>{it}</b><br><span style='color:green;'>{data['بيع']} ₪</span><br><small>المخزن: {data['كمية']}</small></div>", unsafe_allow_html=True)
            val = st.number_input(f"الكمية", key=f"sale_{it}", min_value=0.0, step=0.1)
            if val > 0:
                temp_bill.append({'item': it, 'qty': val, 'amount': val * data['بيع'], 'profit': (data['بيع'] - data['شراء']) * val})
    
    if temp_bill and st.button("✅ تنفيذ البيع لجميع المختار", use_container_width=True):
        bid = str(uuid.uuid4())[:8]
        for row in temp_bill:
            st.session_state.inventory[row['item']]['كمية'] -= row['qty']
            new_row = {'date': datetime.now().strftime("%Y-%m-%d"), 'item': row['item'], 'amount': row['amount'], 'profit': row['profit'], 'method': 'نقدي', 'customer_name': 'زبون', 'bill_id': bid}
            st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)
        sync_to_google(); st.success("تم الحفظ!"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.markdown("<h1 class='main-title'>📦 قائمة الجرد الشاملة</h1>", unsafe_allow_html=True)
    if st.session_state.inventory:
        # عرض جدول واحد ضخم فيه كل شيء
        full_data = []
        for k, v in st.session_state.inventory.items():
            full_data.append({'الصنف': k, 'القسم': v.get('قسم'), 'الشراء': v['شراء'], 'البيع': v['بيع'], 'الكمية': v['كمية']})
        
        st.dataframe(pd.DataFrame(full_data), use_container_width=True, height=600) # تم زيادة الارتفاع ليظهر الكل
    else:
        st.warning("المخزن فارغ.")

elif menu == "⚙️ الإعدادات":
    st.markdown("<h1 class='main-title'>⚙️ الإدارة</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["✨ صنف جديد", "✏️ تعديل صنف موجود"])
    
    with t1:
        with st.form("new"):
            n = st.text_input("الاسم")
            cat = st.selectbox("القسم", st.session_state.CATEGORIES)
            b = st.number_input("شراء")
            s = st.number_input("بيع")
            q = st.number_input("كمية")
            if st.form_submit_button("إضافة"):
                st.session_state.inventory[n] = {'قسم': cat, 'شراء': b, 'بيع': s, 'كمية': q}
                sync_to_google(); st.rerun()

    with t2:
        if st.session_state.inventory:
            # هنا تظهر كل الأصناف في القائمة المنسدلة للتعديل
            edit_name = st.selectbox("اختر الصنف للتعديل", list(st.session_state.inventory.keys()))
            d = st.session_state.inventory[edit_name]
            with st.form("edit"):
                new_n = st.text_input("الاسم", value=edit_name)
                new_b = st.number_input("شراء", value=float(d['شراء']))
                new_s = st.number_input("بيع", value=float(d['بيع']))
                new_q = st.number_input("كمية", value=float(d['كمية']))
                if st.form_submit_button("حفظ التعديل"):
                    if new_n != edit_name: del st.session_state.inventory[edit_name]
                    st.session_state.inventory[new_n] = {'قسم': d.get('قسم'), 'شراء': new_b, 'بيع': new_s, 'كمية': new_q}
                    sync_to_google(); st.rerun()
