import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime

from offline_retrieval import recommend_for_user, semantic_search_books
from manager_dashboard_full import manager_dashboard_full

# Determine mode (online or offline)
ONLINE_MODE = os.environ.get("ONLINE_MODE", "true").lower() == "true"
USERS_CSV = "data/users_profiles.csv"

# -------------------------------------------------------------
# Function: log user activity
# -------------------------------------------------------------
def log_interaction(user, question, answer):
    os.makedirs("logs", exist_ok=True)
    row = [
        user.get("name"), user.get("school"), user.get("role"),
        question, (answer[:120] + "...") if answer else "",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

# -------------------------------------------------------------
# Function: Login view
# -------------------------------------------------------------
def login_view():
    st.title("📘 EDU_AI_LIBRARY — Qatar")
    st.subheader("تسجيل الدخول")

    name = st.text_input("👤 الاسم (كما في قائمة المستخدمين):")
    school = st.text_input("🏫 المدرسة / القسم:")
    role = st.selectbox("🎓 الدور:", ["طالب", "معلم", "أمين مكتبة", "مدير قسم المكتبات", "admin"])

    if st.button("✅ دخول"):
        df = pd.read_csv(USERS_CSV)
        match = df[df["name"].str.strip().str.lower() == name.strip().lower()]
        if match.empty:
            st.error("المستخدم غير موجود في القائمة. (هذا ديمو يسمح فقط بالأسماء الموجودة).")
            return
        user = match.iloc[0].to_dict()
        if not bool(user.get("active", True)):
            st.warning("حسابك قيد المراجعة. الرجاء التواصل مع الإدارة.")
            return
        st.session_state["user"] = {
            "name": user["name"],
            "role": user["role"],
            "school": user.get("department", ""),
            "user_id": user.get("user_id", ""),
            "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.success(f"مرحبًا {user['name']} 👋")
        st.experimental_rerun()

# -------------------------------------------------------------
# Function: Main application view
# -------------------------------------------------------------
def app_view():
    st.sidebar.success(f"✅ مسجل: {st.session_state['user']['name']} — {st.session_state['user']['role']}")
    st.title("🔎 البحث والتوصيات — Demo Online")

    # Tabs based on role
    if st.session_state["user"]["role"] == "مدير قسم المكتبات":
        tab1, tab2, tab3 = st.tabs(["📚 توصيات مخصّصة", "🔍 بحث دلالي", "📊 لوحة المدير"])
    else:
        tab1, tab2 = st.tabs(["📚 توصيات مخصّصة", "🔍 بحث دلالي"])
        tab3 = None

    # ---------------------------------------------------------
    # Tab 1: Personalized Recommendations
    # ---------------------------------------------------------
    with tab1:
        st.caption("التوصيات تعتمد على تضمينات مسبقة (Users + Books) للأوفلاين/الأونلاين")
        top = recommend_for_user(st.session_state["user"]["name"], k=5)
        if not top:
            st.info("لا توجد توصيات جاهزة.")
        else:
            for title, score in top:
                st.write(f"• **{title}**  — similarity: {score:.3f}")

        q = st.text_input("اكتب سؤالك (في مجال مكتبات قطر فقط):")
        if st.button("أرسل"):
            # Online mode: placeholder response
            if ONLINE_MODE:
                ans = f"🔹 رد تجريبي (Online): تم استقبال سؤالك '{q}'. يركّز النظام فقط على مكتبات قطر."
            else:
                # Offline mode: use local GPT4All model
                from local_model_loader import local_generate
                context = "\n".join([f"- {t}" for t, _ in top]) if top else "No prior recommendations."
                prompt = f"""You are an assistant for Qatar school libraries.
Context:
{context}
Question: {q}
Answer shortly in Arabic."""
                ans = local_generate(prompt, max_tokens=220, temp=0.2)

            st.markdown(ans)
            log_interaction(st.session_state["user"], q, ans)

    # ---------------------------------------------------------
    # Tab 2: Semantic Search
    # ---------------------------------------------------------
    with tab2:
        query = st.text_input("أدخل عبارة البحث:")
        if st.button("ابحث"):
            results = semantic_search_books(query, k=10)
            if not results:
                st.warning("لم نجد نتائج ذات صلة.")
            else:
                for title, score in results:
                    st.write(f"• **{title}**  — similarity: {score:.3f}")

    # ---------------------------------------------------------
    # Tab 3: Manager Dashboard
    # ---------------------------------------------------------
    if tab3:
        with tab3:
            manager_dashboard_full()

# -------------------------------------------------------------
# Entry point
# -------------------------------------------------------------
def main():
    st.set_page_config(page_title="EDU_AI_LIBRARY — Online Demo", layout="wide")
    if "user" not in st.session_state:
        login_view()
    else:
        app_view()

if __name__ == "__main__":
    main()

