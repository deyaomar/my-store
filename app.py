# === نظام أبو عمر المتكامل 2026 (نسخة مصححة ومحسّنة) ===
# تم: إصلاح الأخطاء المنطقية، منع الجرد السالب، تحسين المفاتيح، تنظيف الهيكلة

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid

# ================= إعدادات الصفحة =================
st.set_page_config(page_title="نظام أبو عمر المتكامل 2026", layout="wide", page_icon="📊")

# ================= أدوات مساعدة =================
def format_num(val):
    try:
        if float(val).is_integer():
            return str(int(val))
        return f"{val:.2f}"
    except:
        return "0"

def clean_num(text):
    try:
        return float(str(text).replace(',', '.').replace('،', '.'))
    except:
        return 0.0

def safe_read_csv(path, cols):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            return pd.read_csv(path)
        except:
            pass
    return pd.DataFrame(columns=cols)

# ================= تحميل البيانات =================
FILES = {
    'sales_df': ('sales_final.csv', ['date','item','amount','profit','method','customer_name','bill_id','branch','cat']),
    'expenses_df': ('expenses_final.csv', ['date','reason','amount','branch']),
    'adjust_df': ('inventory_adjustments.csv', ['date','item','diff_qty','loss_value','branch'])
}

for key,(file,cols) in FILES.items():
    if key not in st.session_state:
        st.session_state[key] = safe_read_csv(file, cols)

if 'inventory' not in st.session_state:
    inv = safe_read_csv('inventory_final.csv',['item','branch','قسم','شراء','بيع','كمية'])
    st.session_state.inventory = inv.to_dict('records')

if 'categories' not in st.session_state:
    cats = safe_read_csv('categories_final.csv',['name'])
    st.session_state.categories = cats['name'].tolist() if not cats.empty else []

# ================= حفظ تلقائي =================
def auto_save():
    pd.DataFrame(st.session_state.inventory).to_csv('inventory_final.csv',index=False)
    st.session_state.sales_df.to_csv('sales_final.csv',index=False)
    st.session_state.expenses_df.to_csv('expenses_final.csv',index=False)
    st.session_state.adjust_df.to_csv('inventory_adjustments.csv',index=False)
    pd.DataFrame(st.session_state.categories,columns=['name']).to_csv('categories_final.csv',index=False)

# ================= تسجيل الدخول =================
def load_users():
    df = safe_read_csv('branches_config.csv',['branch_name','user_name','password'])
    if df.empty:
        return pd.DataFrame([{'branch_name':'المحل الرئيسي','user_name':'admin','password':'admin'}])
    return df

if 'logged_in' not in st.session_state:
    st.markdown("## 🔐 نظام أبو عمر المتكامل")
    with st.form("login"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور",type="password")
        if st.form_submit_button("دخول"):
            users = load_users()
            row = users[(users.user_name==u)&(users.password==p)]
            if not row.empty:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.session_state.branch = row.iloc[0]['branch_name']
                st.session_state.role = 'admin' if u=='admin' else 'shop'
                st.rerun()
            else:
                st.error("بيانات غير صحيحة")
    st.stop()

# ================= الواجهة =================
st.sidebar.success(f"👤 {st.session_state.user}")

# ================= المدير =================
if st.session_state.role == 'admin':
    menu = st.sidebar.radio("القائمة",["إدارة الفروع","التقارير العامة"])

    if menu == "إدارة الفروع":
        st.header("🏪 إدارة الفروع")
        with st.form("add_branch"):
            b = st.text_input("اسم الفرع")
            u = st.text_input("المستخدم")
            p = st.text_input("كلمة المرور")
            if st.form_submit_button("إضافة"):
                df = load_users()
                df = pd.concat([df,pd.DataFrame([{'branch_name':b,'user_name':u,'password':p}])])
                df.to_csv('branches_config.csv',index=False)
                st.success("تمت الإضافة")
                st.rerun()
        st.dataframe(load_users())

# ================= الفرع =================
else:
    menu = st.sidebar.radio("نظام الفرع",["🛒 نقطة البيع","📦 المخزن","📊 التقارير"])
    my_inv = [i for i in st.session_state.inventory if i['branch']==st.session_state.branch]

    if menu == "🛒 نقطة البيع":
        st.header(f"🛒 بيع - {st.session_state.branch}")
        bill_items = []
        for cat in st.session_state.categories:
            items = [i for i in my_inv if i['قسم']==cat]
            if items:
                with st.expander(cat):
                    for it in items:
                        k = f"qty_{it['item']}_{st.session_state.branch}"
                        val = clean_num(st.text_input(f"{it['item']} (متوفر {it['كمية']})",key=k))
                        if val>0:
                            qty = val/it['بيع']
                            if qty <= it['كمية']:
                                bill_items.append((it,qty,val))
                            else:
                                st.error(f"كمية غير كافية: {it['item']}")
        if st.button("إتمام البيع") and bill_items:
            bill_id = str(uuid.uuid4())[:8]
            for it,qty,val in bill_items:
                it['كمية'] -= qty
                profit = (it['بيع']-it['شراء'])*qty
                st.session_state.sales_df = pd.concat([
                    st.session_state.sales_df,
                    pd.DataFrame([{
                        'date':datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'item':it['item'],
                        'amount':val,
                        'profit':profit,
                        'method':'نقدي',
                        'customer_name':'زبون عام',
                        'bill_id':bill_id,
                        'branch':st.session_state.branch,
                        'cat':it['قسم']
                    }])
                ])
            auto_save()
            st.success("تم البيع بنجاح")
            st.rerun()

    elif menu == "📦 المخزن":
        st.header("📦 مخزن الفرع")
        st.dataframe(pd.DataFrame(my_inv))

    elif menu == "📊 التقارير":
        st.header("📊 تقرير الأرباح")
        df = st.session_state.sales_df
        df = df[df.branch==st.session_state.branch]
        st.metric("إجمالي المبيعات",format_num(df.amount.sum()))
        st.metric("صافي الربح",format_num(df.profit.sum()))

# ================= خروج =================
if st.sidebar.button("🚪 خروج"):
    st.session_state.clear()
    st.rerun()
