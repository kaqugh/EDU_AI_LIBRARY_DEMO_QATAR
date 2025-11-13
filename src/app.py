import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI

from offline_retrieval import recommend_for_user, semantic_search_books
from manager_dashboard_full import manager_dashboard_full


# ============================================================
#  MINISTRY HEADER
# ============================================================
def ministry_header():
    st.markdown(
        """
        <div style="
            background-color:#E8F3FB;
            padding:15px;
            border-radius:10px;
            border:1px solid #c8e1f0;
            text-align:center;
            font-family:'Tajawal', sans-serif;">
            <h3 style="margin:0; color:#003366;">
                🇶🇦 وزارة التربية والتعليم والتعليم العالي – 
                <span style="color:#0059b3;">Ministry of Education and Higher Education - Qatar</span>
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
#  LOAD API KEY
# ============================================================
OPENAI_API_KEY = None

try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
except Exception:
    pass

if not OPENAI_API_KEY:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
    except:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

USERS_CSV = "data/users_profiles.csv"
BOOKS_CSV = "data/books.csv"


# ============================================================
#  CSV LOAD/SAVE FUNCTIONS
# ============================================================
def load_users():
    return pd.read_csv(USERS_CSV, encoding="utf-8-sig")

def save_users(df):
    df.to_csv(USERS_CSV, index=False, encoding="utf-8-sig")

def load_books():
    return pd.read_csv(BOOKS_CSV, encoding="utf-8-sig")

def save_books(df):
    df.to_csv(BOOKS_CSV, index=False, encoding="utf-8-sig")


# ============================================================
#  LOGGING
# ============================================================
def log_interaction(user, question, answer):
    os.makedirs("logs", exist_ok=True)
    row = [
        user.get("name"), user.get("role"), user.get("school"),
        question, answer[:100],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


# ============================================================
#  AI ANSWER (NORMAL GPT)
# ============================================================
def ai_answer(user_name: str, question: str, context: str = "") -> str:

    system_msg = (
        "أنت مساعد مكتبة ذكي تابع لوزارة التعليم في قطر. "
        "أجب بالعربية وبشكل مختصر ودقيق. ركّز على كتب المناهج والمدارس."
    )

    if not OPENAI_API_KEY:
        return f"📚 (وضع تجريبي بدون مفتاح OpenAI). سؤالك: {question}"

    try:
        prompt = f"المستخدم: {user_name}\nالسياق:\n{context}\nالسؤال: {question}"
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
        return f"⚠️ خطأ أثناء الاتصال بـ OpenAI: {e}"


# ============================================================
#  CHECK → IS QUESTION A BORROW REQUEST?
# ============================================================
def is_borrow_intent(q):
    keywords = ["استعارة", "استعير", "أخذ كتاب", "احجز", "أريد كتاب", "borrow"]
    return any(k in q for k in keywords)


# ============================================================
#  CHECK → USER ASKING ABOUT AVAILABILITY?
# ============================================================
def is_availability_intent(q):
    keywords = ["متوفر", "متاح", "available", "status", "هل يوجد"]
    return any(k in q for k in keywords)


# ============================================================
#  BORROW BOOK LOGIC
# ============================================================
def handle_borrow(user, question):
    books = load_books()
    users = load_users()

    # STEP 1: find closest book
    results = semantic_search_books(question, k=1)
    if not results:
        return "❌ لم أجد كتابًا مشابهًا لهذا الاسم."

    book_title, _ = results[0]

    book_row = books[books["title"] == book_title]
    if book_row.empty:
        return "❌ تعذر العثور على هذا الكتاب في قاعدة البيانات."

    book_index = book_row.index[0]

    # if already borrowed
    if books.loc[book_index, "status"] == "borrowing":
        return f"❌ الكتاب **{book_title}** مستعار حاليًا. متوقع عودته في: {books.loc[book_index, 'borrow_end']}"

    # check if user already borrowed one
    u = users[users["user_id"] == user["user_id"]].index[0]
    if str(users.loc[u, "borrowed_books"]).strip() != "":
        return "⚠️ لا يمكنك استعارة أكثر من كتاب واحد حاليًا."

    # PROCESS BORROW
    today = datetime.today()
    return_date = today + timedelta(days=7)

    # update book
    books.loc[book_index, "status"] = "borrowing"
    books.loc[book_index, "borrow_start"] = today.date().isoformat()
    books.loc[book_index, "borrow_end"] = return_date.date().isoformat()

    # update user
    users.loc[u, "borrowed_books"] = book_title
    users.loc[u, "borrow_start"] = today.date().isoformat()
    users.loc[u, "borrow_end"] = return_date.date().isoformat()

    save_books(books)
    save_users(users)

    return f"✅ تم حجز كتاب **{book_title}** لك حتى تاريخ **{return_date.date().isoformat()}**."


# ============================================================
#  CHECK AVAILABILITY
# ============================================================
def handle_availability(question):
    books = load_books()
    results = semantic_search_books(question, k=1)

    if not results:
        return "❌ لم أجد كتابًا مطابقًا."

    title, _ = results[0]
    row = books[books["title"] == title].iloc[0]

    if row["status"] == "available":
        return f"📗 الكتاب **{title}** متوفر الآن."

    else:
        return (
            f"❌ الكتاب **{title}** مستعار حاليًا.\n"
            f"📅 تاريخ الإرجاع المتوقع: {row['borrow_end']}"
        )


# ============================================================
#  LOGIN VIEW
# ============================================================
def login_view():
    ministry_header()
    st.title("📘 نظام المكتبة الذكية – Qatar EDU AI Library")
    st.caption(f"🔑 Key Active: {bool(OPENAI_API_KEY)}")

    df = load_users()

    # Normalization to avoid RTL issues
    def normalize(s):
        return str(s).replace("\u200f","").replace("\u200e","").strip().lower()

    df["rn"] = df["role"].apply(normalize)

    df["bucket"] = df["rn"].apply(
        lambda r:
            "طالب" if "طالب" in r or "student" in r else
            "معلم" if "معلم" in r or "teacher" in r else
            "مدير قسم المكتبات"
    )

    students = df[df["bucket"] == "طالب"]
    teachers = df[df["bucket"] == "معلم"]
    ministry = df[df["bucket"] == "مدير قسم المكتبات"]

    col1, col2, col3 = st.columns(3)

    # Students
    with col1:
        st.subheader("🎓 الطلاب")
        name = st.selectbox("اختر اسم الطالب", ["— اختر —"] + sorted(students["name"].tolist()), key="st_sel")
        if st.button("دخول الطالب"):
            if name != "— اختر —":
                user = students[students["name"] == name].iloc[0].to_dict()
                _login_user(user)
                st.rerun()

    # Teachers
    with col2:
        st.subheader("👨‍🏫 المعلمون")
        name = st.selectbox("اختر اسم المعلم", ["— اختر —"] + sorted(teachers["name"].tolist()), key="t_sel")
        if st.button("دخول المعلم"):
            if name != "— اختر —":
                user = teachers[teachers["name"] == name].iloc[0].to_dict()
                _login_user(user)
                st.rerun()

    # Ministry
    with col3:
        st.subheader("🏛️ موظفو الوزارة")
        name = st.selectbox("اختر اسم الموظف", ["— اختر —"] + sorted(ministry["name"].tolist()), key="m_sel")
        if st.button("دخول الوزارة"):
            if name != "— اختر —":
                user = ministry[ministry["name"] == name].iloc[0].to_dict()
                _login_user(user)
                st.rerun()


def _login_user(user):
    st.session_state["user"] = {
        "name": user["name"],
        "role": user["role"],
        "user_id": user["user_id"],
        "school": user.get("department", "")
    }
    st.session_state["page"] = "chat"
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": f"👋 مرحبًا {user['name']}! كيف يمكنني مساعدتك اليوم؟"
    }]
    st.session_state["last_question"] = None
    st.toast("✔️ تم تسجيل الدخول")


# ============================================================
#  CHAT VIEW
# ============================================================
def chat_view():
    ministry_header()

    user = st.session_state["user"]

    if st.button("🏠 العودة للرئيسية"):
        st.session_state.clear()
        st.rerun()

    st.title("🤖 الوكيل الذكي لمكتبات مدارس قطر – AI Library Agent")
    st.sidebar.success(f"{user['name']} – {user['role']}")

    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            st.markdown(f"**🤖 المكتبة الذكية:** {msg['content']}")
        else:
            st.markdown(f"**🧑‍💻 أنت:** {msg['content']}")

    q = st.chat_input("اكتب سؤالك هنا...")
    if q and q != st.session_state.get("last_question"):
        st.session_state["last_question"] = q
        st.session_state["messages"].append({"role": "user", "content": q})

        # Determine intent
        if is_borrow_intent(q):
            ans = handle_borrow(user, q)

        elif is_availability_intent(q):
            ans = handle_availability(q)

        else:
            # normal GPT answer
            try:
                recs = recommend_for_user(user["name"], k=3)
                ctx = "\n".join([f"- {t}" for t, _ in (recs or [])])
            except:
                ctx = ""
            ans = ai_answer(user["name"], q, ctx)

        st.session_state["messages"].append({"role": "assistant", "content": ans})
        log_interaction(user, q, ans)
        st.rerun()


# ============================================================
#  MAIN CONTROLLER
# ============================================================
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
