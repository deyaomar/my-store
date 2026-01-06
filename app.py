import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="نظام أبو عمر المتكامل", layout="wide", page_icon="🍏")

# التصميم الجمالي المطور
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 2.5em; background-color: #1e4d2b; color: white; }
    .stButton>button:hover { background-color: #2e7d32; border: 1px solid gold; }
    .category-header { background-color: #e8f5e9; padding: 8px; border-radius: 8px; color: #1b5e20; font-weight: bold; margin-top: 15px; border-right: 5px solid #2e7d32; }
    .stock-text { font-size: 14px; font-weight: bold; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# نظام الدخول
if 'logged_in' not in st.session_state:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("<h1 style='text-align:center;'>🔐 دخول النظام</h1>", unsafe_allow_html=True)
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if pwd == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # البيانات الأساسية
    if 'inventory' not in st.session_state:
        st.session_state.inventory = {
            "بطاطا": {"كمية": 38.4, "شراء": 3.0, "بيع": 3.33, "قسم": "خضار وفواكه"},
            "ليمون": {"كمية": 27.5, "شراء": 4.0, "بيع": 6.0, "قسم": "خضار وفواكه"},
            "فستق": {"كمية": 10.0, "شراء": 12.0, "بيع": 18.0, "قسم": "مكسرات"},
            "نسكافيه": {"كمية": 50.0, "شراء": 0.8, "بيع": 1.5, "قسم": "نسكافيه ومشروبات"}
        }
    if 'daily_profit' not in st.session_state: st.session_state.daily_profit = 0.0

    menu = st.sidebar.radio("القائمة:", ["💎 منصة البيع", "🏪 المخزن الشامل", "🍂 قسم التوالف"])
    
    if st.sidebar.button("🚪 خروج"):
        st.session_state.pop('logged_in')
        st.rerun()

    # --- 1. منصة البيع ---
    if menu == "💎 منصة البيع":
        st.markdown("<h1 style='text-align:center;'>🛒 فاتورة مبيعات</h1>", unsafe_allow_html=True)
        st.metric("📈 أرباح اليوم", f"{st.session_state.daily_profit:.2f} ₪")
        
        bill_items = []
        cats = ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]
        
        for cat in cats:
            with st.expander(f"📂 قسم {cat}", expanded=True):
                items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
                for item in items:
                    c1, c2, c3, c4 = st.columns([0.5, 2, 2, 2])
                    with c1: sel = st.checkbox("", key=f"s_{item}")
                    with c2: st.markdown(f"**{item}**")
                    with c3: mode = st.radio("", ["شيكل", "كمية"], key=f"m_{item}", horizontal=True, label_visibility="collapsed")
                    with c4: val = st.number_input("", min_value=0.0, key=f"v_{item}", label_visibility="collapsed")
                    
                    if sel and val > 0:
                        inv = st.session_state.inventory[item]
                        q = val if mode == "كمية" else val / inv["بيع"]
                        bill_items.append({"صنف": item, "كمية": q, "مبلغ": (val if mode == "شيكل" else val * inv["بيع"]), "ربح": (inv["بيع"] - inv["شراء"]) * q})

        if bill_items:
            if st.button("✅ تأكيد البيع النهائي"):
                summary = []
                for e in bill_items:
                    st.session_state.inventory[e["صنف"]]["كمية"] -= e["كمية"]
                    st.session_state.daily_profit += e["ربح"]
                    new_stock = st.session_state.inventory[e["صنف"]]["كمية"]
                    summary.append(f"✅ {e['صنف']}: المتبقي {new_stock:.2f}")
                
                for msg in summary:
                    st.info(msg)
                st.balloons()
                st.success("تم خصم المبيعات وتحديث المخزن!")

    # --- 2. المخزن الشامل ---
    elif menu == "🏪 المخزن الشامل":
        st.markdown("<h1 style='text-align:center;'>🏪 إدارة المخزن</h1>", unsafe_allow_html=True)
        
        # إضافة صنف مع تصفير القائمة
        with st.expander("➕ إضافة صنف جديد", expanded=False):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("اسم الصنف")
                cat = st.selectbox("القسم", ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"])
                c_a1, c_a2, c_a3 = st.columns(3)
                q = c_a1.number_input("الكمية")
                b = c_a2.number_input("شراء")
                s = c_a3.number_input("بيع")
                if st.form_submit_button("إضافة للمخزن"):
                    if n:
                        st.session_state.inventory[n] = {"كمية": q, "شراء": b, "بيع": s, "قسم": cat}
                        st.success(f"✔️ تم إضافة {n} بنجاح!")
                    else: st.error("اكتب اسم الصنف أولاً")

        for cat in ["خضار وفواكه", "مكسرات", "نسكافيه ومشروبات"]:
            st.markdown(f"<div class='category-header'>📂 {cat}</div>", unsafe_allow_html=True)
            items = {k: v for k, v in st.session_state.inventory.items() if v.get('قسم') == cat}
            for item, data in items.items():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1.5])
                col1.markdown(f"<span class='stock-text'>{item}</span>", unsafe_allow_html=True)
                col2.write(f"{data['كمية']:.1f}")
                col3.write(f"{data['شراء']}")
                col4.write(f"{data['بيع']}")
                with col5:
                    sc1, sc2 = st.columns(2)
                    if sc1.button("📝", key=f"ed_{item}"): 
                        st.session_state.edit_target = item
                    if sc2.button("🗑️", key=f"del_{item}"):
                        st.session_state.confirm_delete = item
        
        # نافذة تأكيد الحذف
        if 'confirm_delete' in st.session_state:
            st.warning(f"⚠️ هل أنت متأكد من حذف {st.session_state.confirm_delete}؟")
            c_del1, c_del2 = st.columns(2)
            if c_del1.button("نعم، احذف"):
                del st.session_state.inventory[st.session_state.confirm_delete]
                del st.session_state.confirm_delete
                st.rerun()
            if c_del2.button("إلغاء"):
                del st.session_state.confirm_delete
                st.rerun()

        # نافذة التعديل
        if 'edit_target' in st.session_state:
            target = st.session_state.edit_target
            st.markdown(f"### 🛠️ تعديل صنف: {target}")
            col_u1, col_u2, col_u3 = st.columns(3)
            u_q = col_u1.number_input("الكمية", value=st.session_state.inventory[target]["كمية"])
            u_b = col_u2.number_input("الشراء", value=st.session_state.inventory[target]["شراء"])
            u_s = col_u3.number_input("البيع", value=st.session_state.inventory[target]["بيع"])
            if st.button("حفظ التعديلات"):
                st.session_state.inventory[target].update({"كمية": u_q, "شراء": u_b, "بيع": u_s})
                del st.session_state.edit_target
                st.success("تم التحديث!")
                st.rerun()

    # --- 3. التوالف ---
    elif menu == "🍂 قسم التوالف":
        st.markdown("<h1>🍂 تسجيل الخسائر</h1>", unsafe_allow_html=True)
        it_w = st.selectbox("الصنف", list(st.session_state.inventory.keys()))
        q_w = st.number_input("الكمية التالفة")
        if st.button("تأكيد خصم التالف"):
            st.session_state.inventory[it_w]["كمية"] -= q_w
            st.session_state.daily_profit -= (q_w * st.session_state.inventory[it_w]["شراء"])
            st.warning(f"تم الخصم. المتبقي من {it_w}: {st.session_state.inventory[it_w]['كمية']:.2f}")
