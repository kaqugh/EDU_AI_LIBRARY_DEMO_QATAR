# ✅ Final version of app.py adapted to your uploaded users_profiles.csv structure
# - Uses preferred_language
# - Uses permissions
# - Uses borrowed_books_count
# - Respects `active` field
# - NO .env, reads OpenAI key from st.secrets

# ✅ Final version of app.py (SAFE)
# OpenAI key is securely loaded from Streamlit Secrets only

# ✅ Final version of app.py (with availability check fix)
# ✅ النسخة السابقة من app.py مع واجهة تسجيل دخول للمجموعات الثلاث (طلاب، معلمون، موظفو الوزارة)

import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI
from offline_retrieval import recommend_for_user, semantic_search_books

# ========== إعداد المسارات ==========
USERS_CSV = "data/users_profiles.csv"
BOOKS_CSV = "data/books.csv"

# ========== إعداد مفتاح OpenAI ==========
OPENAI_API_KEY = st.secrets.get("OPENAI_KEY", None)
st.sidebar.write("🔐 Key Loaded:", bool(OPENAI_API_KEY))
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ========== تحميل البيانات ==========
users = pd.read_csv(USERS_CSV)
books = pd.read_csv(BOOKS_CSV)

# ========== دالة تسجيل الدخول ==========
def login_view():
    st.title("📘 EDU_AI_LIBRARY — Qatar")
    st.subheader("واجهة الدخول الرئيسية")

    group = st.selectbox("👥 اختر الفئة:", ["طلاب", "معلمون", "مدير قسم المكتبات"])
    filtered = users[users["role"] == ("طالب" if group == "طلاب" else ("معلم" if group == "معلمون" else "مدير قسم المكتبات"))]
    name = st.selectbox("👤 اختر اسمك:", filtered["name"].tolist())

    if st.button("✅ تسجيل الدخول"):
        user = filtered[filtered["name"] == name].iloc[0].to_dict()
        st.session_state.user = {
            "name": user["name"],
            "role": user["role"],
            "school": user.get("department", "")
        }
        st.success(f"مرحبًا {user['name']} 👋")
        st.rerun()

# ========== دالة العرض الرئيسية ==========
def app_view():
    st.sidebar.success(f"🟢 {st.session_state['user']['name']} — {st.session_state['user']['role']}")
    st.title("🤖 مكتبة قطر الذكية — AI Library Agent")
    st.caption("هذه مكتبتك الذكية. كيف يمكنني مساعدتك اليوم؟")

    q = st.chat_input("✍️ اكتب سؤالك هنا...")
    if q:
        with st.chat_message("user"):
            st.write(q)

        if client:
            res = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "أنت مساعد مكتبة ذكي لمدارس قطر. أجِب باحترام وبالعربية فقط."},
                    {"role": "user", "content": q}
                ],
                max_tokens=250,
                temperature=0.3
            )
            answer = res.choices[0].message.content.strip()
        else:
            answer = "⚠️ لا يوجد اتصال بمفتاح OpenAI."

        with st.chat_message("assistant"):
            st.write(answer)

# ========== نقطة التشغيل ==========
def main():
    st.set_page_config(page_title="EDU AI Library", layout="wide")
    if "user" not in st.session_state:
        login_view()
    else:
        app_view()

if __name__ == "__main__":
    main()

        answer = "⚠️ No OpenAI key found."

    with st.chat_message("assistant"):
        st.write(answer)
