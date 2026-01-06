import streamlit as st
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="نظام جرد أبو عمر", layout="wide")
PASSWORD = "123"

# نظام الدخول
if 'logged_in' not in st.session_state:
    st.title("🔐 دخول نظام أبو عمر")
    pwd = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("دخول"):
        if pwd == PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun()
        else: st.error("خطأ في كلمة السر!")
else:
    # القائمة الجانبية للتحكم
    st.sidebar.title("🛠️ لوحة التحكم")
    menu = st.sidebar.radio("اختر العملية:", ["عرض الجرد والبيع", "إضافة صنف جديد", "تعديل كمية / حذف صنف"])
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # البيانات الأساسية
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3},
            "ليمون": {"كمية": 27.5, "شراء": 4},
            "تفاح": {"كمية": 23.0, "شراء": 9},
            "كلمنتينا": {"كمية": 22.4, "شراء": 4},
            "بصل ناشف": {"كمية": 20.9, "شراء": 2.13},
            "بندورة": {"كمية": 12.0, "شراء": 7},
            "خيار": {"كمية": 12.6, "شراء": 5}
        }

    # --- الصفحة الأولى: عرض الجرد والبيع ---
    if menu == "عرض الجرد والبيع":
        st.header("🛒 تسجيل عملية بيع")
        c1, c2, c3 = st.columns(3)
        with c1:
            item_sel = st.selectbox("اختر الصنف", list(st.session_state.inventory.keys()))
        with c2:
            amt_sel = st.number_input("الكمية المباعة (كيلو)", min_value=0.0, step=0.5)
        with c3:
            if st.button("✅ تأكيد البيع"):
                if st.session_state.inventory[item_sel]["كمية"] >= amt_sel:
                    st.session_state.inventory[item_sel]["كمية"] -= amt_sel
                    st.success(f"تم خصم {amt_sel} من {item_sel}")
                else: st.error("الكمية لا تكفي!")

        st.divider()
        st.header("📊 حالة المخزن")
        df = pd.DataFrame(st.session_state.inventory).T
        df['رأس المال المتبقي'] = df['كمية'] * df['شراء']
        st.table(df)
        st.metric("إجمالي قيمة البضاعة", f"{df['رأس المال المتبقي'].sum():,.2f} شيكل")

    # --- الصفحة الثانية: إضافة منتج جديد ---
    elif menu == "إضافة صنف جديد":
        st.header("✨ إضافة صنف جديد للمحل")
        new_name = st.text_input("اسم الصنف (مثلاً: موز)")
        new_qty = st.number_input("الكمية المتوفرة", min_value=0.0)
        new_price = st.number_input("سعر الشراء (للكيلو)", min_value=0.0)
        if st.button("➕ إضافة المنتج"):
            if new_name and new_name not in st.session_state.inventory:
                st.session_state.inventory[new_name] = {"كمية": new_qty, "شراء": new_price}
                st.success(f"تم إضافة {new_name} للجرد بنجاح!")
            else: st.error("الصنف موجود مسبقاً أو الاسم فارغ")

    # --- الصفحة الثالثة: تعديل وحذف ---
    elif menu == "تعديل كمية / حذف صنف":
        st.header("⚙️ تعديل أو حذف بضاعة")
        edit_item = st.selectbox("اختر الصنف للتعديل/الحذف", list(st.session_state.inventory.keys()))
        
        col_edit, col_del = st.columns(2)
        with col_edit:
            st.subheader("تعديل الكمية")
            add_more = st.number_input("أضف كمية جديدة (للزيادة)", min_value=0.0)
            if st.button("🆙 تحديث الكمية"):
                st.session_state.inventory[edit_item]["كمية"] += add_more
                st.success(f"تمت زيادة كمية {edit_item}")
        
        with col_del:
            st.subheader("حذف الصنف نهائياً")
            st.warning("انتبه! الحذف لا يمكن التراجع عنه")
            if st.button("🗑️ حذف الصنف من القائمة"):
                del st.session_state.inventory[edit_item]
                st.rerun()
