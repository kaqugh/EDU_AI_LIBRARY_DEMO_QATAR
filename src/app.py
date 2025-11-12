import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI

# Optional existing imports
from offline_retrieval import recommend_for_user, semantic_search_books
from manager_dashboard_full import manager_dashboard_full

# -------------------------------------------------------------------
#  Load API key (works for Streamlit Cloud Secrets OR local .env)
# -------------------------------------------------------------------
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
    except Exception:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

# -------------------------------------------------------------------
#  Basic setup
# -------------------------------------------------------------------
USERS_CSV = "data/users_profiles.csv"
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# -------------------------------------------------------------------
#  Log user activity
# -------------------------------------------------------------------
def log_interaction(user, question, answer):
    os.makedirs("logs", exist_ok=True)
    row = [
        user.get("name"), user.get("school"), user.get("role"),
        question, (answer[:120] + "...") if answer else "",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


# -------------------------------------------------------------------
#  GPT helper
# -------------------------------------------------------------------
def ai_answer(user_name: str, question: str, context: str = "") -> str:
    """Use OpenAI if key exists, otherwise fallback demo reply."""
    system_msg = (
        "أنت مساعد مكتبة ذكي تابع لوزارة التربية والتعليم والتعليم العالي في قطر. "
        "قدّم إجابات قصيرة ودقيقة بالعربية. ركّز على الكتب، المراجع، والتعليم."
    )

    # no key → demo reply
    if not OPENAI_API_KEY:
        return f"📚 (وضع تجريبي بلا مفتاح) سؤالك: «{question}»."

    try:
        prompt = f"المستخدم: {user_name}\nالسياق:\n{context}\nالسؤال: {question}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            max_tokens=350,
            temperature=0.3
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        return f"⚠️ تعذر استخدام واجهة OpenAI الآن. السبب: {e}"


# -------------------------------------------------------------------
#  Login view
# -------------------------------------------------------------------
def login_view():
    st.title("📘 EDU_AI_LIBRARY — Qatar")
    st.subheader("واجهة الدخول الرئيسية")
    st.markdown(f"🔑 **Key detected:** `{bool(OPENAI_API_KEY)}`")

    df = pd.read_csv(USERS_CSV, encoding="utf-8-sig").dropna(subset=["name", "role"])
    df["name"] = df["name"].astype(str).str.strip()

    st.markdown("### 👥 اختر الفئة:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓 الطلاب", use_container_width=True):
            st.session_state["selected_group"] = "طالب"
    with col2:
        if st.button("👨‍🏫 المعلمون", use_container_width=True):
            st.session_state["selected_group"] = "معلم"
    with col3:
        if st.button("🏛️ موظفو الوزارة", use_container_width=True):
            st.session_state["selected_group"] = "مدير قسم المكتبات"

    if "selected_group" in st.session_state:
        group = st.session_state["selected_group"]
        st.markdown(f"### 🧾 قائمة {group}:")
        filtered = df[df["role"].str.contains(group, case=False, na=False)]
        if filtered.empty:
            st.warning("⚠️ لا توجد أسماء ضمن هذه الفئة.")
            return

        selected_name = st.selectbox("اختر اسمك الكامل:", filtered["name"].tolist(), key="user_select")

        if st.button("✅ تسجيل الدخول", use_container_width=True) and selected_name:
            user = filtered[filtered["name"] == selected_name].iloc[0].to_dict()
            st.session_state["user"] = {
                "name": user["name"],
                "role": user["role"],
                "school": user.get("department", ""),
                "user_id": user.get("user_id", ""),
                "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state["page"] = "chat"
            st.session_state["messages"] = [
                {"role": "assistant",
                 "content": f"🎉 مرحبًا {user['name']}! هذه مكتبتك الذكية. كيف يمكنني مساعدتك اليوم؟"}
            ]
            st.toast(f"✅ تم تسجيل دخول {user['name']}")
            st.stop()


# -------------------------------------------------------------------
#  Chat view
# -------------------------------------------------------------------
def chat_view():
    user = st.session_state.get("user", {})

    cols = st.columns([0.15, 0.85])
    with cols[0]:
        if st.button("🏠 العودة للرئيسية", help="العودة إلى واجهة الدخول"):
            st.session_state.clear()
            st.stop()
    with cols[1]:
        st.title("💬 مكتبة قطر الذكية — AI Library Agent")

    st.sidebar.success(f"✅ {user.get('name','')} — {user.get('role','')}")
    st.sidebar.caption(f"🔑 OpenAI Key Active: {bool(OPENAI_API_KEY)}")

    for msg in st.session_state.get("messages", []):
        if msg["role"] == "assistant":
            st.markdown(f"**🤖 المكتبة الذكية:** {msg['content']}")
        else:
            st.markdown(f"**🧑‍💻 {user.get('name','المستخدم')}:** {msg['content']}")

    q = st.chat_input("اكتب سؤالك هنا...")
    if q:
        st.session_state["messages"].append({"role": "user", "content": q})

        # optional small context from recommendations
        try:
            recs = recommend_for_user(user.get("name",""), k=3)
            ctx = "\n".join([f"- {t}" for t, _ in (recs or [])])
        except Exception:
            ctx = ""

        ans = ai_answer(user_name=user.get("name",""), question=q, context=ctx)
        st.session_state["messages"].append({"role": "assistant", "content": ans})
        log_interaction(user, q, ans)
        st.stop()


# -------------------------------------------------------------------
#  Main controller
# -------------------------------------------------------------------
def main():
    st.set_page_config(page_title="EDU_AI_LIBRARY — Online Demo", layout="wide")
    if "page" not in st.session_state:
        login_view()
    elif st.session_state["page"] == "chat" and "user" in st.session_state:
        chat_view()
    else:
        login_view()


if __name__ == "__main__":
    main()
