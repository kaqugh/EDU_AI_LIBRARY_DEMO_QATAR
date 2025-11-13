import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI

from offline_retrieval import recommend_for_user, semantic_search_books
from manager_dashboard_full import manager_dashboard_full

# ========== CONFIGURATION ==========
USERS_CSV = "data/users_profiles.csv"
BOOKS_CSV = "data/books.csv"

# ========== LOAD API KEY ==========
OPENAI_API_KEY = None
try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_KEY")
except:
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ========== UI HEADER ==========
def ministry_header():
    st.markdown("""
        <div style="background-color:#E8F3FB; padding:15px; border-radius:10px; border:1px solid #c8e1f0; text-align:center; font-family:'Tajawal', sans-serif;">
        <h3 style="margin:0; color:#003366;">
            🇶🇦 وزارة التربية والتعليم والتعليم العالي – 
            <span style="color:#0059b3;">Ministry of Education and Higher Education - Qatar</span>
        </h3></div>""", unsafe_allow_html=True)

# ========== FILE HANDLING ==========
def load_users():
    return pd.read_csv(USERS_CSV, encoding="utf-8-sig")

def save_users(df):
    df.to_csv(USERS_CSV, index=False, encoding="utf-8-sig")

def load_books():
    return pd.read_csv(BOOKS_CSV, encoding="utf-8-sig")

def save_books(df):
    df.to_csv(BOOKS_CSV, index=False, encoding="utf-8-sig")

# ========== LOGGING ==========
def log_interaction(user, question, answer):
    os.makedirs("logs", exist_ok=True)
    row = [user.get("name"), user.get("role"), user.get("school"), question, answer[:120], datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

# ========== AI INTENTS ==========
def is_borrow_intent(q):
    return any(k in q for k in ["استعارة", "أريد كتاب", "أستعير", "borrow"])

def is_availability_intent(q):
    return any(k in q for k in ["متاح", "متوفر", "available"])

def is_return_intent(q):
    return any(k in q for k in ["إرجاع", "ارجاع", "أعيد", "return"])

def is_recommendation_intent(q):
    return any(k in q for k in ["انصحني", "اقتراح", "توصي", "recommend"])

# ========== AI RESPONSE ==========
def ai_answer(user_name: str, question: str, context: str = "") -> str:
    if not OPENAI_API_KEY:
        return f"🔒 لا يوجد اتصال بـ OpenAI حاليًا."
    system_msg = "أنت مساعد مكتبة ذكي تابع لوزارة التعليم في قطر. أجب دائمًا بالعربية أو الإنجليزية حسب اللغة المختارة، وبشكل رسمي وموجز."
    prompt = f"المستخدم: {user_name}\nالسياق:\n{context}\n\nالسؤال: {question}"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ خطأ في الاتصال بـ OpenAI: {e}"

# ========== BORROWING ==========
def handle_borrow(user, question):
    books, users = load_books(), load_users()
    results = semantic_search_books(question, k=1)
    if not results:
        return "❌ لم يتم العثور على كتاب مطابق."
    title, _ = results[0]
    match = books[books["title"] == title]
    if match.empty:
        return f"📘 الكتاب {title} غير موجود في قاعدة البيانات."
    book_index = match.index[0]
    if books.loc[book_index, "status"] == "borrowing":
        return f"❌ الكتاب **{title}** مستعار حاليًا وسيعود بتاريخ {books.loc[book_index, 'borrow_end']}"
    user_index = users[users["user_id"] == user["user_id"]].index[0]
    if str(users.loc[user_index, "borrowed_books"]).strip() != "":
        return "⚠️ لا يمكن استعارة أكثر من كتاب حاليًا."
    today = datetime.today()
    end = today + timedelta(days=7)
    books.loc[book_index, ["status", "borrow_start", "borrow_end"]] = ["borrowing", today.date(), end.date()]
    users.loc[user_index, ["borrowed_books", "borrow_start", "borrow_end"]] = [title, today.date(), end.date()]
    save_books(books)
    save_users(users)
    return f"✅ تم حجز الكتاب **{title}** حتى تاريخ {end.date()}"

# ========== RETURNING ==========
def handle_return(user, question):
    books, users = load_books(), load_users()
    title = user.get("borrowed_books", "").strip()
    if not title:
        return "📘 لا يوجد كتاب مسجل على حسابك حاليًا."
    user_index = users[users["user_id"] == user["user_id"]].index[0]
    book_index = books[books["title"] == title].index[0]
    books.loc[book_index, ["status", "borrow_start", "borrow_end"]] = ["available", "", ""]
    users.loc[user_index, ["borrowed_books", "borrow_start", "borrow_end"]] = ["", "", ""]
    save_books(books)
    save_users(users)
    return f"✅ تم إرجاع الكتاب **{title}**. شكرًا لك."

# ========== AVAILABILITY ==========
def handle_availability(question):
    books = load_books()
    results = semantic_search_books(question, k=1)
    if not results:
        return "📘 لم يتم العثور على عنوان مطابق."
    title, _ = results[0]
    df_match = books[books["title"] == title]
    if df_match.empty:
        key = title.split("/")[0].strip()
        df_match = books[books["title"].str.contains(key, case=False, na=False)]
    if df_match.empty:
        return f"📘 الكتاب **{title}** غير معروف."
    row = df_match.iloc[0]
    if row["status"] == "available":
        return f"📗 الكتاب **{row['title']}** متاح حاليًا."
    else:
        return f"📕 الكتاب **{row['title']}** معار حاليًا. سيعود بتاريخ {row['borrow_end']}"

# ========== CHAT UI ==========
def chat_view():
    ministry_header()
    user = st.session_state["user"]
    if st.button("🏠 العودة للواجهة الرئيسية"):
        st.session_state.clear()
        st.rerun()
    st.title("🤖 المساعد الذكي للمكتبة")
    for msg in st.session_state.get("messages", []):
        st.markdown(f"**{'🧑‍💻' if msg['role']=='user' else '🤖'}:** {msg['content']}")
    q = st.chat_input("اكتب سؤالك...")
    if q and q != st.session_state.get("last_question"):
        st.session_state["last_question"] = q
        st.session_state["messages"].append({"role": "user", "content": q})
        if is_borrow_intent(q):
            ans = handle_borrow(user, q)
        elif is_return_intent(q):
            ans = handle_return(user, q)
        elif is_availability_intent(q):
            ans = handle_availability(q)
        elif is_recommendation_intent(q):
            recs = recommend_for_user(user["name"], k=3)
            ans = "📚 اقتراحات لك: " + ", ".join([f"**{t}**" for t, _ in recs]) if recs else "لا توجد اقتراحات حالياً."
        else:
            ctx = "\n".join([f"- {t}" for t, _ in recommend_for_user(user["name"], k=3)])
            ans = ai_answer(user["name"], q, ctx)
        st.session_state["messages"].append({"role": "assistant", "content": ans})
        log_interaction(user, q, ans)
        st.rerun()

# ========== LOGIN ==========
def login_view():
    ministry_header()
    st.title("📘 واجهة تسجيل الدخول")
    df = load_users()
    df["group"] = df["role"].apply(lambda r: "طالب" if "طالب" in r else "معلم" if "معلم" in r else "وزارة")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🎓 الطلاب")
        name = st.selectbox("اختر الطالب", sorted(df[df["group"]=="طالب"]["name"]))
        if st.button("دخول كطالب"):
            user = df[df["name"]==name].iloc[0].to_dict()
            _set_session_user(user)
    with col2:
        st.subheader("👨‍🏫 المعلمون")
        name = st.selectbox("اختر المعلم", sorted(df[df["group"]=="معلم"]["name"]))
        if st.button("دخول كمعلم"):
            user = df[df["name"]==name].iloc[0].to_dict()
            _set_session_user(user)
    with col3:
        st.subheader("🏛️ موظفو الوزارة")
        name = st.selectbox("اختر الموظف", sorted(df[df["group"]=="وزارة"]["name"]))
        if st.button("دخول كوزارة"):
            user = df[df["name"]==name].iloc[0].to_dict()
            _set_session_user(user)

def _set_session_user(user):
    st.session_state["user"] = {
        "name": user["name"],
        "role": user["role"],
        "user_id": user["user_id"],
        "school": user.get("department", "")
    }
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
