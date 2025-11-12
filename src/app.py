import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI

# Optional existing imports
from offline_retrieval import recommend_for_user, semantic_search_books
from manager_dashboard_full import manager_dashboard_full


# -------------------------------------------------------------------
# وزارة التربية والتعليم - الشريط العلوي الرسمي
# -------------------------------------------------------------------
def ministry_header():
    st.markdown(
        """
        <div style="
            background-color:#E8F3FB;
            padding:15px 20px;
            border-radius:10px;
            text-align:center;
            border:1px solid #c8e1f0;
            margin-bottom:20px;">
            <h3 style="margin:0; color:#003366; font-family:'Tajawal',sans-serif;">
                🇶🇦 وزارة التربية والتعليم والتعليم العالي – 
                <span style="color:#0073e6;">Ministry of Education and Higher Education - Qatar</span>
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------------------------------------------------------
# Load API key (works for Streamlit Secrets OR local .env)
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

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
USERS_CSV = "data/users_profiles.csv"


# -------------------------------------------------------------------
# Utility: log user activity
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
# GPT helper
# -------------------------------------------------------------------
def ai_answer(user_name: str, question: str, context: str = "") -> str:
    """Use OpenAI if key exists, otherwise fallback demo reply."""
    system_msg = (
        "أنت مساعد مكتبة ذكي تابع لوزارة التربية والتعليم والتعليم العالي في قطر. "
        "قدّم إجابات قصيرة ودقيقة بالعربية. ركّز على الكتب، المراجع، والتعليم."
    )

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
# Login view (Improved with icons + dropdowns for each group)
# -------------------------------------------------------------------
def login_view():
    ministry_header()   # شعار الوزارة العلوي

    st.title("📘 EDU_AI_LIBRARY — Qatar")
    st.subheader("واجهة الدخول الرئيسية")
    st.markdown(f"🔑 **Key Active:** `{bool(OPENAI_API_KEY)}`")

    # تحميل بيانات المستخدمين
    df = pd.read_csv(USERS_CSV, encoding="utf-8-sig").dropna(subset=["name", "role"])
    df["name"] = df["name"].astype(str).str.strip()

    # تقسيم المستخدمين إلى مجموعات
    students = df[df["role"].str.contains("طالب", case=False, na=False)]
    teachers = df[df["role"].str.contains("معلم", case=False, na=False)]
    ministry = df[df["role"].str.contains("مدير قسم المكتبات", case=False, na=False)]

    # 3 أعمدة رئيسية
    col1, col2, col3 = st.columns(3)

    # ---- الطلاب ----
    with col1:
        st.markdown("### 🎓 الطلاب")
        selected_student = st.selectbox(
            "اختر اسم الطالب:",
            ["— اختر —"] + sorted(students["name"].tolist()),
            key="student_select",
            label_visibility="collapsed"
        )
        if st.button("✅ دخول الطالب", use_container_width=True):
            if selected_student != "— اختر —":
                user = students[students["name"] == selected_student].iloc[0].to_dict()
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
                st.session_state["last_question"] = None
                st.toast(f"✅ تم تسجيل دخول الطالب {user['name']}")
                st.rerun()
            else:
                st.warning("الرجاء اختيار اسم من القائمة.")

    # ---- المعلمون ----
    with col2:
        st.markdown("### 👨‍🏫 المعلمون")
        selected_teacher = st.selectbox(
            "اختر اسم المعلم:",
            ["— اختر —"] + sorted(teachers["name"].tolist()),
            key="teacher_select",
            label_visibility="collapsed"
        )
        if st.button("✅ دخول المعلم", use_container_width=True):
            if selected_teacher != "— اختر —":
                user = teachers[teachers["name"] == selected_teacher].iloc[0].to_dict()
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
                     "content": f"🎓 أهلًا {user['name']}! كيف يمكن للمكتبة مساعدتك اليوم؟"}
                ]
                st.session_state["last_question"] = None
                st.toast(f"✅ تم تسجيل دخول المعلم {user['name']}")
                st.rerun()
            else:
                st.warning("الرجاء اختيار اسم من القائمة.")

    # ---- موظفو الوزارة ----
    with col3:
        st.markdown("### 🏛️ موظفو الوزارة")
        selected_ministry = st.selectbox(
            "اختر اسم الموظف:",
            ["— اختر —"] + sorted(ministry["name"].tolist()),
            key="ministry_select",
            label_visibility="collapsed"
        )
        if st.button("✅ دخول الوزارة", use_container_width=True):
            if selected_ministry != "— اختر —":
                user = ministry[ministry["name"] == selected_ministry].iloc[0].to_dict()
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
                     "content": f"🏛️ مرحبًا {user['name']} من وزارة التعليم! كيف يمكن للمكتبة مساعدتك اليوم؟"}
                ]
                st.session_state["last_question"] = None
                st.toast(f"✅ تم تسجيل دخول {user['name']} من الوزارة")
                st.rerun()
            else:
                st.warning("الرجاء اختيار اسم من القائمة.")


# -------------------------------------------------------------------
# Chat view
# -------------------------------------------------------------------
def chat_view():
    ministry_header()   # شعار الوزارة العلوي
    user = st.session_state.get("user", {})

    cols = st.columns([0.15, 0.85])
    with cols[0]:
        if st.button("🏠 العودة للرئيسية", help="العودة إلى واجهة الدخول"):
            st.session_state.clear()
            st.rerun()
    with cols[1]:
        st.title("💬 مكتبة قطر الذكية — AI Library Agent")

    st.sidebar.success(f"✅ {user.get('name','')} — {user.get('role','')}")
    st.sidebar.caption(f"🔑 Key Active: {bool(OPENAI_API_KEY)}")

    # Show chat history
    for msg in st.session_state.get("messages", []):
        if msg["role"] == "assistant":
            st.markdown(f"**🤖 المكتبة الذكية:** {msg['content']}")
        else:
            st.markdown(f"**🧑‍💻 {user.get('name','المستخدم')}:** {msg['content']}")

    q = st.chat_input("اكتب سؤالك هنا...")
    if q and q != st.session_state.get("last_question"):
        st.session_state["last_question"] = q
        st.session_state["messages"].append({"role": "user", "content": q})

        try:
            recs = recommend_for_user(user.get("name",""), k=3)
            ctx = "\n".join([f"- {t}" for t, _ in (recs or [])])
        except Exception:
            ctx = ""

        ans = ai_answer(user_name=user.get("name",""), question=q, context=ctx)
        st.session_state["messages"].append({"role": "assistant", "content": ans})
        log_interaction(user, q, ans)
        st.rerun()


# -------------------------------------------------------------------
# Main controller
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
