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

if 'inventory' not in st.session_state:
    if os.path.exists('inventory_final.csv'):
        try:
            inv_df = pd.read_csv('inventory_final.csv')
            inv_df = inv_df.drop_duplicates(subset=[inv_df.columns[0]], keep='last')
            st.session_state.inventory = inv_df.set_index(inv_df.columns[0]).to_dict('index')
        except Exception as e:
            st.error(f"خطأ في قراءة ملف المخزن: {e}")
            st.session_state.inventory = {}
    else:
        st.session_state.inventory = {}

if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('categories_final.csv')['name'].tolist() if os.path.exists('categories_final.csv') else ["خضار وفواكه", "مكسرات"]

if 'p_method' not in st.session_state: st.session_state.p_method = "تطبيق"
if 'show_cust_fields' not in st.session_state: st.session_state.show_cust_fields = False
if 'current_bill_id' not in st.session_state: st.session_state.current_bill_id = None

def auto_save():
    if st.session_state.inventory:
        inv_df_to_save = pd.DataFrame.from_dict(st.session_state.inventory, orient='index')
        inv_df_to_save.to_csv('inventory_final.csv', index=True)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. التنسيق الاحترافي (CSS) - 
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* --- التنسيق الجديد لنقطة البيع (البطاقات) --- */
    .item-card {
        background-color: #f8f9fa; /* لون خلفية فاتح ومريح */
        border: 2px solid #e1e4e8;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .item-card:hover {
        border-color: #27ae60;
        box-shadow: 0 6px 12px rgba(39, 174, 96, 0.15);
    }
    .stock-label {
        color: #666;
        font-size: 14px;
        font-weight: bold;
    }
    .price-tag {
        color: #27ae60;
        font-weight: 900;
        font-size: 20px;
        background: rgba(39, 174, 96, 0.1);
        padding: 2px 8px;
        border-radius: 5px;
    }
    /* -------------------------------------- */

    /* تنسيق القائمة الجانبية (القديم اللي عجبك) */
    [data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-left: 2px solid #27ae60;
    }
    .sidebar-user {
        background-color: #1a1a1a;
        padding: 25px 10px;
        border-radius: 15px;
        margin: 15px 10px;
        border: 2px solid #27ae60;
        text-align: center;
        color: #ffffff !important;
        font-weight: 900;
        font-size: 24px;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
        font-size: 18px !important;
        font-weight: 900 !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] {
        background-color: #27ae60 !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > span:first-child {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. نظام تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.markdown("<h1 class='main-title'>🔒 نظام إدارة أبو عمر</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة مرور الإدارة", type="password")
    if st.button("دخول النظام"):
        if pwd == "123": st.session_state.logged_in = True; st.rerun()
else:
    # --- بناء القائمة الجانبية المنسقة ---
    with st.sidebar:
        st.markdown("<div class='sidebar-user'>أهلاً أبو عمر 👋</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-title'>التنقل السريع</div>", unsafe_allow_html=True)
        
        menu = st.radio(
            "Menu",
            ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ الإعدادات"],
            label_visibility="collapsed"
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 خروج آمن", use_container_width=True):
            st.session_state.clear(); st.rerun()

    # --- 1. نقطة البيع ---
   if menu == "🛒 نقطة البيع":
        st.markdown("<h1 class='main-title'>🛒 شاشة البيع السريع</h1>", unsafe_allow_html=True)
        
        # شريط علوي لطريقة الدفع والبحث
        top_c1, top_c2 = st.columns([1, 2])
        with top_c1:
            st.session_state.p_method = st.radio("💳 طريقة الدفع", ["تطبيق", "نقداً"], horizontal=True)
        with top_c2:
            search_q = st.text_input("🔍 ابحث عن صنف لبيعه الآن...", placeholder="اكتب اسم الصنف هنا...")

        bill_items = []
        
        # عرض الأصناف بتنسيق احترافي
        for cat in st.session_state.categories:
            items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            if search_q: items = {k: v for k, v in items.items() if search_q in k}
            
            if items:
                st.markdown(f"### 📂 {cat}")
                # تقسيم الشاشة لعمودين للأصناف لتقليل طول الصفحة
                cols = st.columns(2)
                for idx, (item, data) in enumerate(items.items()):
                    with cols[idx % 2]:
                        st.markdown(f"""
                        <div class="item-card">
                            <div style='display: flex; justify-content: space-between;'>
                                <b>{item}</b>
                                <span class="price-tag">{format_num(data['بيع'])} ₪</span>
                            </div>
                            <div class="stock-label">المتوفر: {format_num(data['كمية'])} كجم</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        c1, c2 = st.columns([1, 1])
                        mode = c1.segmented_control("النوع", ["₪", "كجم"], key=f"m_{item}", default="₪")
                        val = clean_num(c2.text_input("المقدار", key=f"v_{item}", placeholder="0.0"))
                        
                        if val > 0:
                            qty = val if mode == "كجم" else val / data["بيع"]
                            bill_items.append({
                                "item": item, "qty": qty, 
                                "amount": val if mode == "₪" else val * data["بيع"], 
                                "profit": (data["بيع"] - data["شراء"]) * qty
                            })
                st.markdown("---")

        # زر إتمام العملية مثبت في الأسفل
        if bill_items:
            total_bill = sum(item['amount'] for item in bill_items)
            st.warning(f"⚠️ إجمالي الفاتورة الحالية: {format_num(total_bill)} ₪")
            if st.button("🚀 تأكيد وطباعة الفاتورة", type="primary", use_container_width=True):
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
                    st.session_state.inventory[n] = {"قسم": cat, "شراء": clean_num(b), "بيع": clean_num(s), "كمية": clean_num(q)}
                    auto_save()
                    st.success(f"تم حفظ {n}")
                    st.rerun()
