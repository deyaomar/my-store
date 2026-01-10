import streamlit as st
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🔍 فاحص الاتصال بجوجل")

try:
    # سيحاول جلب أسماء كل الأوراق الموجودة في ملفك
    df = conn.read(worksheet="Sales", ttl=0)
    st.success("✅ تم الاتصال بنجاح!")
    st.write("الأعمدة التي وجدتها في صفحة Sales هي:")
    st.write(df.columns.tolist())
    st.write("آخر 5 أسطر مسجلة:")
    st.table(df.tail(5))
except Exception as e:
    st.error(f"❌ فشل الاتصال. الخطأ هو: {e}")
