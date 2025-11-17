# ✅ Final version of app.py with fixed emoji line and Qatar-only scope filter

import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
from offline_retrieval import recommend_for_user, semantic_search_books

USERS_CSV = "data/users_profiles.csv"
BOOKS_CSV = "data/books.csv"

OPENAI_API_KEY = st.secrets.get("OPENAI_KEY", None)
st.sidebar.write("🔐 Key Loaded:", bool(OPENAI_API_KEY))
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ========== LOAD DATA ==========
def load_users():
    return pd.read_csv(USERS_CSV, encoding="utf-8-sig")

def save_users(df):
    df.to_csv(USERS_CSV, index=False, encoding="utf-8-sig")

def load_books():
    return pd.read_csv(BOOKS_CSV, encoding="utf-8-sig")

def save_books(df):
    df.to_csv(BOOKS_CSV, index=False, encoding="utf-8-sig")

# ========== HEADER UI ==========
def ministry_header():
    st.markdown("""
        <div style="background-color:#E8F3FB; padding:15px; border-radius:10px; border:1px solid #c8e1f0; text-align:center; font-family:'Tajawal', sans-serif;">
        <h3 style="margin:0; color:#003366;">
            🇶🇦 وزارة التربية والتعليم والتعليم العالي – 
            <span style="color:#0059b3;">Ministry of Education and Higher Education - Qatar</span>
        </h3></div>""", unsafe_allow_html=True)

# ========== FILTER ==========
FORBIDDEN_WORDS = ["السعودية", "مصر", "الكويت", "العراق", "الإمارات", "أمريكا", "USA", "UK", "India", "Germany"]

# ========== LOGGING ==========
def log_interaction(user, question, answer):
    os.makedirs("logs", exist_ok=True)
    row = [user.get("name"), user.get("role"), user.get("department"), question, answer[:120], datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

# ========== DETECT LANGUAGE ==========
def detect_language(user):
    lang = str(user.get("preferred_language", "Arabic")).lower()
    return "AR" if "arab" in lang else "EN"

# ========== AI ==========
def ai_answer(user, question, context=""):
    lang = detect_language(user)
    if not client:
        return "🔒 No OpenAI key found." if lang == "EN" else "🔒 لا يوجد مفتاح OpenAI مفعّل."

    if any(w.lower() in question.lower() for w in FORBIDDEN_WORDS):
        return "❌ المساعد الذكي مخصص فقط لخدمة مكتبات قطر المدرسية." if lang == "AR" else "❌ This assistant only supports Qatar school libraries."

    system_msg = "You are a helpful assistant for Qatar school libraries only. Always decline unrelated questions."
    prompt = f"User: {user['name']}\nContext:\n{context}\n\nQuestion: {question}"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}],
            max_tokens=300, temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error from OpenAI: {e}"

# ========== INTENTS ==========
def is_borrow_intent(q):
    return any(k in q.lower() for k in ["استعارة", "أريد كتاب", "borrow"])

def is_return_intent(q):
    return any(k in q.lower() for k in ["إرجاع", "ارجاع", "return"])

def is_availability_intent(q):
    return any(k in q.lower() for k in ["متاح", "متوفر", "available"])

def is_recommendation_intent(q):
    return any(k in q.lower() for k in ["انصحني", "اقتراح", "recommend"])

# ========== CHAT ==========
def chat_view():
    ministry_header()
    user = st.session_state["user"]
    lang = detect_language(user)
    if st.button("🏠 العودة للرئيسية"):
        st.session_state.clear()
        st.rerun()
    st.title("🤖 المساعد الذكي للمكتبة" if lang == "AR" else "🤖 Smart Library Assistant")
    for msg in st.session_state.get("messages", []):
        icon = "🧑‍💻" if msg['role'] == 'user' else "🤖"
        st.markdown(f"**{icon}:** {msg['content']}")
    q = st.chat_input("اكتب سؤالك هنا..." if lang == "AR" else "Type your question here...")
    if q and q != st.session_state.get("last_question"):
        st.session_state["last_question"] = q
        st.session_state["messages"].append({"role": "user", "content": q})
        if is_borrow_intent(q):
            ans = handle_borrow(user)
        elif is_return_intent(q):
            ans = handle_return(user)
        elif is_availability_intent(q):
            ans = handle_availability(user)
        elif is_recommendation_intent(q):
            ans = handle_recommendation(user)
        else:
            ctx = "\n".join([f"- {t}" for t, _ in recommend_for_user(user["name"], k=3)])
            ans = ai_answer(user, q, ctx)
        st.session_state["messages"].append({"role": "assistant", "content": ans})
        log_interaction(user, q, ans)
        st.rerun()

# ========== LOGIN ==========
def login_view():
    ministry_header()
    st.title("📘 تسجيل الدخول إلى مكتبة قطر الذكية")
    df = load_users()
    df = df[df["active"] == True]
    df["group"] = df["role"].apply(lambda r: "طالب" if "طالب" in r else "معلم" if "معلم" in r else "وزارة")
    col1, col2, col3 = st.columns(3)
    for group, col in zip(["طالب", "معلم", "وزارة"], [col1, col2, col3]):
        with col:
            st.subheader(f"📋 {group}")
            subset = df[df["group"] == group]
            name = st.selectbox(f"اختر اسم {group}", sorted(subset["name"]), key=group)
            if st.button(f"تسجيل الدخول ({group})", key=f"btn_{group}"):
                user = subset[subset["name"] == name].iloc[0].to_dict()
                st.session_state["user"] = user
                st.session_state["messages"] = [{"role": "assistant", "content": f"👋 مرحبًا {user['name']}! كيف يمكنني مساعدتك اليوم؟"}]
                st.session_state["page"] = "chat"
                st.rerun()

# ========== MAIN ==========
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

