# ✅ Final version of app.py (restored with full login + group roles)

import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI
from offline_retrieval import recommend_for_user, semantic_search_books

# ========== FILE PATHS ==========
USERS_CSV = "data/users_profiles.csv"
BOOKS_CSV = "data/books.csv"

# ========== LOAD API KEY ==========
OPENAI_API_KEY = st.secrets.get("OPENAI_KEY", None)
st.sidebar.write("🔐 Key Loaded:", bool(OPENAI_API_KEY))
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ========== HELPER FUNCTIONS ==========
def load_users_by_role(role):
    df = pd.read_csv(USERS_CSV)
    return df[df["role"] == role]["name"].tolist()

def load_user_record(name):
    df = pd.read_csv(USERS_CSV)
    record = df[df["name"] == name]
    return record.iloc[0].to_dict() if not record.empty else None

def log_interaction(user, question, answer):
    os.makedirs("logs", exist_ok=True)
    row = [
        user.get("name"), user.get("school"), user.get("role"),
        question, (answer[:120] + "...") if answer else "",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

def handle_availability(user):
    q = st.session_state["chat_input"]
    books = pd.read_csv(BOOKS_CSV)
    for title in books["title"]:
        if title in q:
            row = books[books["title"] == title]
            if row.empty:
                return "📚 الكتاب غير موجود في قاعدة البيانات."
            status = row["status"].values[0]
            if status == "borrowed":
                due = row["return_date"].values[0]
                return f"📕 الكتاب **{title}** مستعار حاليًا. تاريخ الإرجاع المتوقع: {due}."
            else:
                return f"📗 الكتاب **{title}** متاح حاليًا للاستعارة."
    return None

def generate_answer(user, q):
    context = f"المستخدم: {user['name']}، المدرسة: {user['school']}, الدور: {user['role']}"
    prompt = f"""
You are a helpful assistant for Qatar school libraries. Answer in the user's language.
User context: {context}
Question: {q}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a school library assistant."},
                 {"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()

# ========== INTERFACES ==========
def login_view():
    st.title("📘 EDU_AI_LIBRARY — Qatar")
    st.subheader("واجهة الدخول الرئيسية")

    category = st.selectbox("🧑‍🤝‍🧑 اختر الفئة:", ["طالب", "معلم", "مدير قسم المكتبات"])
    names = load_users_by_role(category)
    name = st.selectbox("🧾 اختر اسمك:", names)

    if st.button("✅ تسجيل الدخول"):
        user = load_user_record(name)
        if not user:
            st.error("المستخدم غير موجود.")
            return
        st.session_state["user"] = {
            "name": user["name"],
            "role": user["role"],
            "school": user.get("department", "")
        }
        st.success(f"مرحبًا {user['name']} 👋")
        st.rerun()

def chat_view():
    user = st.session_state["user"]
    st.title("💬 مكتبة قطر الذكية — AI Library Agent")
    st.markdown(f"مرحبًا 🎉 **{user['name']}** - المكتبة الذكية! كيف يمكنني مساعدتك اليوم؟")
    st.button("🏠 العودة للرئيسية", on_click=lambda: st.session_state.pop("user") or st.rerun())

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    q = st.chat_input("اكتب سؤالك هنا...")
    if q:
        st.chat_message("user").write(q)
        st.session_state.chat_history.append({"role": "user", "content": q})

        ai_ans = handle_availability(user)
        if not ai_ans and client:
            ai_ans = generate_answer(user, q)
        elif not ai_ans:
            ai_ans = "⚠️ No OpenAI key found."

        st.chat_message("assistant").write(ai_ans)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_ans})
        log_interaction(user, q, ai_ans)

# ========== MAIN ==========
def main():
    st.set_page_config(page_title="EDU_AI_LIBRARY — Qatar", layout="centered")
    if "user" not in st.session_state:
        login_view()
    else:
        chat_view()

if __name__ == "__main__":
    main()
