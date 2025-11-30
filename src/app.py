# ✅ Final Combined Version: EDU AI Library – Qatar
import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
from offline_retrieval import recommend_for_user

USERS_CSV = "data/users_profiles.csv"
BOOKS_CSV = "data/books.csv"
OPENAI_API_KEY = st.secrets.get("OPENAI_KEY", None)
st.sidebar.write("🔐 Key Loaded:", bool(OPENAI_API_KEY))
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

FORBIDDEN_WORDS = ["USA", "France", "India", "porn", "Israel", "sex", "LGBT", "alcohol"]
def violates_policy(text): return any(w.lower() in text.lower() for w in FORBIDDEN_WORDS)

def log_event(layer, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.setdefault("logs", []).append(f"{timestamp} [{layer}] {message}")

def ministry_header():
    st.markdown("""
    <div style='background-color:#E8F3FB; padding:15px; border-radius:10px; border:1px solid #c8e1f0; text-align:center; font-family:Tajawal,sans-serif;'>
    <h3 style='margin:0; color:#003366;'>🇶🇦 وزارة التربية والتعليم والتعليم العالي – 
    <span style='color:#0059b3;'>Ministry of Education and Higher Education - Qatar</span></h3></div>
    """, unsafe_allow_html=True)

def load_users(): return pd.read_csv(USERS_CSV, encoding="utf-8-sig")
def save_users(df): df.to_csv(USERS_CSV, index=False, encoding="utf-8-sig")
def load_books(): return pd.read_csv(BOOKS_CSV, encoding="utf-8-sig")
def save_books(df): df.to_csv(BOOKS_CSV, index=False, encoding="utf-8-sig")

def detect_language(user):
    lang = str(user.get("preferred_language", "Arabic")).lower()
    return "AR" if "arab" in lang else "EN"

def ai_answer(user, question, context=""):
    lang = detect_language(user)
    if not client:
        return "🔒 لا يوجد مفتاح OpenAI مفعّل." if lang == "AR" else "🔒 OpenAI key not found."
    if violates_policy(question):
        return "❌ المساعد الذكي مخصص فقط لخدمة مكتبات قطر المدرسية." if lang == "AR" else "❌ Assistant is limited to Qatar schools."

    system_msg = "You are a smart assistant for school libraries in Qatar. Avoid answering unrelated questions."
    prompt = f"User: {user['name']}\nContext:\n{context}\n\nQuestion: {question}"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}],
            max_tokens=300, temperature=0.4
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {e}"

def log_interaction(user, q, ans):
    os.makedirs("logs", exist_ok=True)
    row = [user.get("name"), user.get("role"), user.get("department"), q, ans[:100], datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)
    log_event("Governance", f"Logged interaction: {user['name']}")

def handle_borrow(user):
    books, users = load_books(), load_users()
    uid = user["user_id"]
    uidx = users[users["user_id"] == uid].index[0]
    if str(users.loc[uidx, "borrowed_books"]).strip():
        return "📘 لديك كتاب معار حاليًا. يرجى إرجاعه أولاً."
    results = recommend_for_user(user["name"], k=1)
    if not results: return "📘 لم يتم العثور على كتاب للاستعارة."
    title, _ = results[0]
    bidx = books[books["title"] == title].index
    if bidx.empty: return "❌ لم يتم العثور على الكتاب."
    bidx = bidx[0]
    if books.loc[bidx, "status"] == "borrowing":
        return f"📕 الكتاب {title} مستعار حالياً."
    today, ret = datetime.today().date(), datetime.today().date() + timedelta(days=7)
    books.loc[bidx, ["status", "borrow_start", "borrow_end"]] = ["borrowing", today, ret]
    users.loc[uidx, ["borrowed_books", "borrow_start", "borrow_end", "borrowed_books_count"]] = [title, today, ret, 1]
    save_books(books); save_users(users)
    return f"✅ تم استعارة الكتاب **{title}** حتى {ret}."

def handle_return(user):
    books, users = load_books(), load_users()
    uid = user["user_id"]
    uidx = users[users["user_id"] == uid].index[0]
    title = users.loc[uidx, "borrowed_books"]
    if not isinstance(title, str) or not title.strip():
        return "📘 لا يوجد كتاب لإرجاعه."
    bidx = books[books["title"] == title].index[0]
    books.loc[bidx, ["status", "borrow_start", "borrow_end"]] = ["available", "", ""]
    users.loc[uidx, ["borrowed_books", "borrow_start", "borrow_end", "borrowed_books_count"]] = ["", "", "", 0]
    save_books(books); save_users(users)
    return f"✅ تم إرجاع الكتاب **{title}**."

def chat_view():
    ministry_header()
    user = st.session_state["user"]
    lang = detect_language(user)
    if st.button("🏠 العودة"):
        st.session_state.clear(); st.rerun()
    st.title("🤖 المساعد الذكي للمكتبة")
    for m in st.session_state.get("messages", []):
        icon = "🧑‍💻" if m["role"] == "user" else "🤖"
        st.markdown(f"**{icon}:** {m['content']}")
    q = st.chat_input("اكتب سؤالك هنا...")
    if q and q != st.session_state.get("last_question"):
        st.session_state["last_question"] = q
        st.session_state["messages"].append({"role": "user", "content": q})
        if "استعارة" in q:
            ans = handle_borrow(user); log_event("Intent", "borrow")
        elif "إرجاع" in q:
            ans = handle_return(user); log_event("Intent", "return")
        else:
            ctx = "\n".join([f"- {t}" for t, _ in recommend_for_user(user["name"], k=3)])
            ans = ai_answer(user, q, ctx)
        st.session_state["messages"].append({"role": "assistant", "content": ans})
        log_interaction(user, q, ans)
        st.rerun()

def login_view():
    ministry_header()
    st.title("📘 تسجيل الدخول إلى مكتبة قطر")
    df = load_users()
    df = df[df["active"] == True]
    df["group"] = df["role"].apply(lambda r: "طالب" if "طالب" in r else "معلم" if "معلم" in r else "وزارة")
    col1, col2, col3 = st.columns(3)
    for group, col in zip(["طالب", "معلم", "وزارة"], [col1, col2, col3]):
        with col:
            st.subheader(f"📋 {group}")
            subset = df[df["group"] == group]
            name = st.selectbox(f"اختر اسم {group}", sorted(subset["name"]), key=group)
            if st.button(f"تسجيل ({group})", key=f"btn_{group}"):
                user = subset[subset["name"] == name].iloc[0].to_dict()
                st.session_state["user"] = user
                st.session_state["messages"] = [{"role": "assistant", "content": f"👋 مرحبًا {user['name']}! كيف أساعدك؟"}]
                st.session_state["page"] = "chat"
                st.rerun()

def main():
    st.set_page_config(page_title="EDU AI Library – Qatar", layout="wide")
    if "page" not in st.session_state: login_view()
    elif st.session_state["page"] == "chat": chat_view()

if __name__ == "__main__":
    main()
