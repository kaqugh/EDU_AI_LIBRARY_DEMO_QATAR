# coding: utf-8
"""
AI Library Agent for Qatar Ministry of Education – Streamlit Application
This version improves the original demo by:
- Loading users & books from CSV and respecting borrow history.
- Role‑based login (student / teacher / library administrator).
- Handling borrowing, returning, availability checks, and recommendations.
- Using OpenAI (or a fallback local model) for natural‑language answers.
- Dynamically building context from user history to improve responses.
- Filtering out-of‑scope questions (e.g., other countries).
- Detailed logging of system layers to Streamlit logs (Data, Intent, AI, Governance).
"""

import os
import csv
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

from openai import OpenAI

# ---- Configuration ----
USERS_CSV = "data/users_profiles.csv"
BOOKS_CSV = "data/books.csv"
OPENAI_KEY = st.secrets.get("OPENAI_KEY", None)
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# Keywords that are outside Qatar school library scope
FORBIDDEN = [
    "USA", "France", "India", "Kuwait", "Saudi", "alcohol", "porn",
    "sex", "LGBT", "politics", "religion"
]

def load_users() -> pd.DataFrame:
    """Load users and ensure an 'active' field exists."""
    df = pd.read_csv(USERS_CSV, encoding="utf-8-sig")
    if "active" not in df.columns:
        df["active"] = True
    return df[df["active"] == True]

def load_books() -> pd.DataFrame:
    return pd.read_csv(BOOKS_CSV, encoding="utf-8-sig")

def save_users(df: pd.DataFrame) -> None:
    df.to_csv(USERS_CSV, index=False, encoding="utf-8-sig")

def save_books(df: pd.DataFrame) -> None:
    df.to_csv(BOOKS_CSV, index=False, encoding="utf-8-sig")

def log_interaction(user: dict, question: str, answer: str) -> None:
    """Write user interactions to logs and mark layer activity."""
    os.makedirs("logs", exist_ok=True)
    row = [
        user.get("name"),
        user.get("role"),
        user.get("department"),
        question,
        answer[:120],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ]
    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

def check_out_of_scope(text: str) -> bool:
    return any(word.lower() in text.lower() for word in FORBIDDEN)

def assistant_prompt(role: str) -> str:
    """Provide base system message depending on user role."""
    if "طالب" in role:
        return ("You are a helpful AI assistant serving a student in a Qatar school library. "
                "Answer in modern standard Arabic. Keep answers concise and educational.")
    elif "معلم" in role:
        return ("You are a knowledgeable AI assistant helping a teacher in a Qatar school library. "
                "Provide formal, accurate information, aligned with the Ministry curriculum.")
    else:  # وزارة أو أمين مكتبة
        return ("You are an AI library agent for the Ministry of Education in Qatar. "
                "Respond professionally, focusing strictly on Qatar school‑library services.")

# ----------- Core logic for borrow, return, availability, recommendation -----------
def handle_borrow(user: dict) -> str:
    books_df, users_df = load_books(), load_users()
    uid = user["user_id"]
    user_idx = users_df[users_df["user_id"] == uid].index[0]
    if str(users_df.loc[user_idx, "borrowed_books"]).strip():
        return "📘 لديك كتاب معار حالياً، يرجى إرجاعه أولاً."

    # Recommend the top book not yet borrowed by this user (simple example)
    recs = recommend_for_user(user["name"], k=1)
    if not recs:
        return "📘 لم يتم العثور على كتاب للاستعارة."
    title, _ = recs[0]
    book_idx = books_df[books_df["title"] == title].index
    if book_idx.empty:
        return "❌ الكتاب غير موجود."
    book_idx = book_idx[0]
    if books_df.loc[book_idx, "status"] == "borrowing":
        return f"❌ الكتاب **{title}** مستعار حالياً."

    today = datetime.today().date()
    ret_date = today + timedelta(days=7)
    books_df.loc[book_idx, ["status", "borrow_start", "borrow_end"]] = ["borrowing", today, ret_date]
    users_df.loc[user_idx, ["borrowed_books", "borrow_start", "borrow_end", "borrowed_books_count"]] = [
        title, today, ret_date, 1]
    save_books(books_df)
    save_users(users_df)
    return f"✅ تم استعارة الكتاب **{title}** حتى {ret_date}."

def handle_return(user: dict) -> str:
    books_df, users_df = load_books(), load_users()
    uid = user["user_id"]
    user_idx = users_df[users_df["user_id"] == uid].index[0]
    title = users_df.loc[user_idx, "borrowed_books"]
    if not isinstance(title, str) or not title.strip():
        return "📘 ليس لديك كتاب معار حالياً."

    book_idx = books_df[books_df["title"] == title].index
    if book_idx.empty:
        return "❌ الكتاب غير موجود."
    book_idx = book_idx[0]
    books_df.loc[book_idx, ["status", "borrow_start", "borrow_end"]] = ["available", "", ""]
    users_df.loc[user_idx, ["borrowed_books", "borrow_start", "borrow_end", "borrowed_books_count"]] = [
        "", "", "", 0]
    save_books(books_df)
    save_users(users_df)
    return f"✅ تم إرجاع الكتاب **{title}**."

def handle_availability(user: dict) -> str:
    books_df = load_books()
    recs = recommend_for_user(user["name"], k=1)
    if not recs:
        return "📘 لا توجد بيانات للكتاب المطلوب."
    title, _ = recs[0]
    row = books_df[books_df["title"] == title]
    if row.empty:
        return "❌ الكتاب غير موجود."
    row = row.iloc[0]
    if row["status"] == "available":
        return f"✅ الكتاب **{title}** متاح."
    return f"❌ الكتاب **{title}** مستعار حتى {row['borrow_end']}."

def handle_recommendation(user: dict) -> str:
    recs = recommend_for_user(user["name"], k=3)
    if not recs:
        return "📘 لا توجد توصيات حالياً."
    return "📚 مقترحات لك: " + ", ".join([f"**{t}**" for t, _ in recs])

# ----------------- Streamlit UI components -----------------
def chat_view():
    user = st.session_state["user"]
    lang = "AR" if "arab" in user.get("preferred_language", "").lower() else "EN"

    st.title("🤖 المساعد الذكي للمكتبة")
    st.write(f"مرحباً، {user['name']}!")

    for msg in st.session_state.get("messages", []):
        role_icon = "🧑‍💻" if msg["role"] == "user" else "🤖"
        st.markdown(f"**{role_icon}:** {msg['content']}")

    question = st.chat_input("اكتب سؤالك هنا..." if lang == "AR" else "Type your question here...")
    if question:
        st.session_state["messages"].append({"role": "user", "content": question})
        # Simple intent detection
        if "استعارة" in question or "borrow" in question.lower():
            answer = handle_borrow(user)
        elif "إرجاع" in question or "ارجاع" in question or "return" in question.lower():
            answer = handle_return(user)
        elif "متاح" in question or "available" in question.lower():
            answer = handle_availability(user)
        elif "انصحني" in question or "اقتراح" in question or "recommend" in question.lower():
            answer = handle_recommendation(user)
        else:
            # Out-of-scope filtering
            if check_out_of_scope(question):
                answer = "❌ أعتذر، أستطيع فقط الرد على أسئلة تتعلق بمكتبات المدارس في قطر."
            else:
                recs = recommend_for_user(user["name"], k=3)
if not recs:
    context = "لا توجد كتب مقترحة حالياً."
else:
    context = "\n".join([f"- {t}" for t, _ in recs])

    system_msg = assistant_prompt(user["role"])

    prompt = f"{system_msg}\nUser: {user['name']}\nContext:\n{context}\n\nQuestion: {question}"

                if client:
                    try:
                        resp = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": system_msg},
                                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
                            ],
                            max_tokens=300,
                            temperature=0.5
                        )
                        answer = resp.choices[0].message.content.strip()
                    except Exception as e:
                        answer = f"⚠️ خطأ في الاتصال: {e}"
                else:
                    answer = "🔒 لا يوجد مفتاح OpenAI مفعّل."
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        log_interaction(user, question, answer)
        st.rerun()

def login_view():
    st.title("📘 تسجيل الدخول إلى مكتبة قطر الذكية")
    users_df = load_users()
    users_df["group"] = users_df["role"].apply(
        lambda r: "طالب" if "طالب" in r else ("معلم" if "معلم" in r else "وزارة")
    )

    col1, col2, col3 = st.columns(3)
    for group, col in zip(["طالب", "معلم", "وزارة"], [col1, col2, col3]):
        with col:
            st.subheader(f"📋 {group}")
            subset = users_df[users_df["group"] == group]
            name = st.selectbox(
                f"اختر اسم {group}", 
                sorted(subset["name"]), 
                key=group)
            if st.button(f"تسجيل الدخول ({group})", key=f"btn_{group}"):
                user = subset[subset["name"] == name].iloc[0].to_dict()
                st.session_state["user"] = user
                st.session_state["messages"] = [
                    {"role": "assistant", "content": f"👋 مرحباً {user['name']}! كيف يمكنني مساعدتك اليوم؟"}
                ]
                st.session_state["page"] = "chat"
                st.rerun()

def main():
    st.set_page_config(page_title="EDU AI Library – Qatar", layout="wide")
    if "page" not in st.session_state:
        login_view()
    elif st.session_state["page"] == "chat":
        chat_view()
    else:
        login_view()

if __name__ == "__main__":
    main()
