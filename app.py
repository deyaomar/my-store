# === نظام أبو عمر المتكامل 2026 ===
# دمج صفحة مسؤول الفرع كما هي داخل نظام الصلاحيات

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

# ================= إعدادات الصفحة =================
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📊")

# ================= أدوات مساعدة =================
def format_num(val):
    try:
        if float(val).is_integer(): return str(int(val))
        return f"{val:.2f}"
    except:
        return "0"

def clean_num(text):
    try:
        return float(str(text).replace(',', '.').replace('،', '.'))
    except:
        return 0.0

# ================= تحميل البيانات =================
def safe_csv(path, cols):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            return pd.read_csv(path)
        except:
            pass
    return pd.DataFrame(columns=cols)

sales_df = safe_csv('sales_final.csv', ['date','item','amount','profit','method','customer_name','customer_phone','bill_id','branch'])
expenses_df = safe_csv('expenses_final.csv', ['date','reason','amount','branch'])
waste_df = safe_csv('waste_final.csv', ['date','item','qty','loss_value','branch'])
adjust_df = safe_csv('inventory_adjustments.csv', ['date','item','diff_qty','loss_value','branch'])

inv_df = safe_csv('inventory_final.csv', ['item','branch','قسم','شراء','بيع','كمية'])
cat_df = safe_csv('categories_final.csv', ['name'])

# ================= Session State =================
if 'inventory' not in st.session_state:
    st.session_state.inventory = inv_df.to_dict('records')
if 'categories' not in st.session_state:
    st.session_state.categories = cat_df['name'].tolist() if not cat_df.empty else []
if 'sales_df' not in st.session_state: st.session_state.sales_df = sales_df
if 'expenses_df' not in st.session_state: st.session_state.expenses_df = expenses_df
if 'waste_df' not in st.session_state: st.session_state.waste_df = waste_df
if 'adjust_df' not in st.session_state: st.session_state.adjust_df = adjust_df

# ================= حفظ =================
def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv', index=False)
    st.session_state.sales_df.to_csv('sales_final.csv', index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv', index=False)
    st.session_state.waste_df.to_csv('waste_final.csv', index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv', index=False)
    pd.DataFrame(st.session_state.categories, columns=['name']).to_csv('categories_final.csv', index=False)

# ================= تسجيل الدخول =================
def users_db():
    df = safe_csv('branches_config.csv', ['branch_name','user_name','password'])
    if df.empty:
        return pd.DataFrame([{'branch_name':'المحل الرئيسي','user_name':'admin','password':'admin'}])
    return df

if 'logged_in' not in st.session_state:
    st.markdown("## 🔐 نظام أبو عمر المتكامل")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        db = users_db()
        row = db[(db.user_name==u) & (db.password==p)]
        if not row.empty:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.session_state.branch = row.iloc[0]['branch_name']
            st.session_state.role = 'admin' if u=='admin' else 'branch'
            st.rerun()
        else:
            st.error("بيانات غير صحيحة")
    st.stop()

# ================= واجهة الفرع (كما في كودك) =================
if st.session_state.role == 'branch':
    st.sidebar.markdown(f"### 🏪 فرع: {st.session_state.branch}")
    menu = st.sidebar.radio("القائمة", ["🛒 نقطة البيع","📦 المخزن والجرد","💸 المصروفات","📊 التقارير المالية","⚙️ الإعدادات"])

    my_inv = [i for i in st.session_state.inventory if i['branch']==st.session_state.branch]

    # === نقطة البيع ===
    if menu == "🛒 نقطة البيع":
        st.header("🛒 شاشة بيع البضاعة")
        bill_items = []
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i['قسم']==cat]
            if items:
                with st.expander(cat, expanded=True):
                    for it in items:
                        k = f"{it['item']}_{st.session_state.branch}"
                        val = clean_num(st.text_input(f"{it['item']} (متوفر {it['كمية']})", key=k))
                        if val>0 and val<=it['كمية']*it['بيع']:
                            qty = val/it['بيع']
                            bill_items.append((it,qty,val))
        if st.button("إتمام البيع") and bill_items:
            bill_id = str(uuid.uuid4())[:8]
            for it,qty,val in bill_items:
                it['كمية'] -= qty
                profit = (it['بيع']-it['شراء'])*qty
                st.session_state.sales_df = pd.concat([
                    st.session_state.sales_df,
                    pd.DataFrame([{'date':datetime.now().strftime('%Y-%m-%d %H:%M'),'item':it['item'],'amount':val,'profit':profit,'method':'نقدي','customer_name':'زبون عام','customer_phone':'','bill_id':bill_id,'branch':st.session_state.branch}])
                ])
            auto_save(); st.success("تم البيع"); st.rerun()

    # === المخزن ===
    elif menu == "📦 المخزن والجرد":
        st.header("📦 مخزن الفرع")
        st.dataframe(pd.DataFrame(my_inv))

    # === المصروفات ===
    elif menu == "💸 المصروفات":
        st.header("💸 المصروفات")
        with st.form("exp"):
            r = st.text_input("البيان"); a = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("حفظ"):
                st.session_state.expenses_df = pd.concat([
                    st.session_state.expenses_df,
                    pd.DataFrame([{'date':datetime.now().strftime('%Y-%m-%d'),'reason':r,'amount':a,'branch':st.session_state.branch}])
                ])
                auto_save(); st.rerun()
        st.dataframe(st.session_state.expenses_df[st.session_state.expenses_df.branch==st.session_state.branch])

    # === التقارير ===
    elif menu == "📊 التقارير المالية":
        st.header("📊 تقارير الفرع")
        df = st.session_state.sales_df
        df = df[df.branch==st.session_state.branch]
        st.metric("إجمالي المبيعات", format_num(df.amount.sum()))
        st.metric("صافي الربح", format_num(df.profit.sum()))

    # === الإعدادات ===
    elif menu == "⚙️ الإعدادات":
        st.header("⚙️ إضافة صنف")
        with st.form("add_item"):
            n = st.text_input("الصنف")
            cat = st.selectbox("القسم", st.session_state.categories)
            b = st.number_input("شراء", min_value=0.0)
            s = st.number_input("بيع", min_value=0.0)
            q = st.number_input("الكمية", min_value=0.0)
            if st.form_submit_button("إضافة"):
                st.session_state.inventory.append({'item':n,'branch':st.session_state.branch,'قسم':cat,'شراء':b,'بيع':s,'كمية':q})
                auto_save(); st.rerun()

# ================= خروج =================
if st.sidebar.button("🚪 خروج"):
    st.session_state.clear(); st.rerun()
