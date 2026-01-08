import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

# 1. إعدادات الصفحة الأساسية (التصميم الأصلي)
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide")

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

# 2. تحميل البيانات الأساسية
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
    inv_df = safe_read_csv('inventory_final.csv', ['item', 'branch', 'قسم', 'شراء', 'بيع', 'كمية', 'سعر_القطعة'])
    st.session_state.inventory = inv_df.to_dict('records')

# --- إضافة قسم السجائر كقسم أساسي ---
if 'categories' not in st.session_state:
    cat_df = safe_read_csv('categories_final.csv', ['name'])
    saved_cats = cat_df['name'].tolist() if not cat_df.empty else []
    st.session_state.categories = list(dict.fromkeys(["السجائر"] + saved_cats))

def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# 3. بوابة الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        db = pd.read_csv(get_db_path())
        m = db[(db['user_name'] == u) & (db['password'] == p)]
        if not m.empty:
            st.session_state.logged_in, st.session_state.user_role, st.session_state.active_user = True, m.iloc[0]['role'], u
            st.session_state.my_branch = m.iloc[0]['branch_name']
            st.rerun()
        else: st.error("خطأ في البيانات")
    st.stop()

# 4. القائمة الجانبية
st.sidebar.title(f"أهلاً {st.session_state.active_user}")
menu = st.sidebar.radio("القائمة الرئيسية", ["🛒 نقطة البيع", "📦 المخزن والجرد", "💸 المصروفات", "📊 التقارير المالية", "⚙️ إدارة الأصناف"])

if st.sidebar.button("🚪 خروج"):
    st.session_state.clear(); st.rerun()

# --- قسم إدارة الأصناف (التعديل المطلوب) ---
if menu == "⚙️ إدارة الأصناف":
    st.header("⚙️ إدارة الأصناف")
    t_add, t_manage, t_cats = st.tabs(["➕ إضافة أصناف", "🛠️ جرد وتعديل", "📂 الأقسام"])

    with t_add:
        target_branch = st.session_state.my_branch
        selected_cat = st.selectbox("اختر القسم لفتح تعليمات التسجيل:", st.session_state.categories)
        
        with st.form("add_form", clear_on_submit=True):
            if selected_cat == "السجائر":
                st.info("📋 تعليمات قسم السجائر: أدخل سعر العلبة وسعر السيجارة المفرد")
                n = st.text_input("اسم نوع الدخان")
                q = st.text_input("الكمية (بالعلبة)")
                b = st.text_input("سعر التكلفة للعلبة")
                s = st.text_input("سعر بيع العلبة")
                sub_p = st.text_input("سعر بيع السيجارة الواحدة")
            else:
                n = st.text_input("اسم الصنف")
                q = st.text_input("الكمية")
                b = st.text_input("سعر الشراء")
                s = st.text_input("سعر البيع")
                sub_p = "0"

            if st.form_submit_button("إضافة الصنف"):
                if n:
                    st.session_state.inventory.append({
                        "item": n, "قسم": selected_cat, "شراء": clean_num(b), 
                        "بيع": clean_num(s), "كمية": clean_num(q), 
                        "branch": target_branch, "سعر_القطعة": clean_num(sub_p)
                    })
                    auto_save(); st.success("تمت الإضافة بنجاح"); st.rerun()

    with t_manage:
        df_inv = pd.DataFrame(st.session_state.inventory)
        if not df_inv.empty:
            edited_df = st.data_editor(df_inv)
            if st.button("حفظ التغييرات"):
                st.session_state.inventory = edited_df.to_dict('records')
                auto_save(); st.success("تم التحديث")

    with t_cats:
        nc = st.text_input("اسم القسم الجديد")
        if st.button("حفظ القسم"):
            if nc and nc not in st.session_state.categories:
                st.session_state.categories.append(nc); auto_save(); st.rerun()

# --- باقي الأقسام الأصلية ---
elif menu == "🛒 نقطة البيع":
    st.header("🛒 شاشة البيع")
    my_inv = [i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]
    search = st.text_input("🔍 بحث سريـع...")
    for it in my_inv:
        if not search or search.lower() in it['item'].lower():
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(it['item'])
            mode = cols[1].selectbox("النوع", ["بالوحدة", "بالتجزئة"] if it.get('سعر_القطعة', 0) > 0 else ["بالوحدة"], key=f"m_{it['item']}")
            val = clean_num(cols[2].text_input("المبلغ ₪", key=f"p_{it['item']}"))
            if cols[3].button("بيع", key=f"b_{it['item']}") and val > 0:
                if mode == "بالتجزئة":
                    qty = (val / it['سعر_القطعة']) / 20 if it['قسم'] == "السجائر" else (val / it['سعر_القطعة'])
                    profit = val - ((it['شراء'] / 20) * (val / it['سعر_القطعة']))
                else:
                    qty = val / it['بيع']; profit = (it['بيع'] - it['شراء']) * qty
                
                # خصم الكمية
                for idx, item in enumerate(st.session_state.inventory):
                    if item['item'] == it['item'] and item['branch'] == st.session_state.my_branch:
                        st.session_state.inventory[idx]['كمية'] -= qty
                
                new_s = {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'item': it['item'], 'amount': val, 'profit': profit, 'method': 'نقداً', 'customer_name': 'عام', 'customer_phone': '', 'bill_id': str(uuid.uuid4())[:8], 'branch': st.session_state.my_branch}
                st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_s])], ignore_index=True)
                auto_save(); st.success("تم البيع"); st.rerun()

elif menu == "📦 المخزن والجرد":
    st.header("📦 حالة المخزن")
    st.table(pd.DataFrame([i for i in st.session_state.inventory if i.get('branch') == st.session_state.my_branch]))

elif menu == "💸 المصروفات":
    st.header("💸 تسجيل مصروف")
    r = st.text_input("البيان")
    a = st.number_input("المبلغ", min_value=0.0)
    if st.button("حفظ"):
        new_e = {'date': datetime.now().strftime("%Y-%m-%d"), 'reason': r, 'amount': a, 'branch': st.session_state.my_branch}
        st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, pd.DataFrame([new_e])], ignore_index=True)
        auto_save(); st.success("تم الحفظ")

elif menu == "📊 التقارير المالية":
    st.header("📊 التقارير")
    s_df = st.session_state.sales_df[st.session_state.sales_df['branch'] == st.session_state.my_branch]
    st.metric("إجمالي المبيعات", f"{s_df['amount'].sum()} ₪")
    st.dataframe(s_df)
