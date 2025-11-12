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
    st.subheader("واجهة الدخول التجريبية")

    df = pd.read_csv(USERS_CSV)

    st.markdown("### 👥 اختر الفئة:")

    col1, col2, col3 = st.columns(3)

    # --- طلاب ---
    with col1:
        st.markdown("<h3 style='text-align:center;'>🎓 الطلاب</h3>", unsafe_allow_html=True)
        students = df[df["role"].str.contains("طالب", case=False, na=False)]
        for _, s in students.iterrows():
            if st.button(f"{s['name']} — {s.get('department','')}", key=f"stu_{s['name']}"):
                st.session_state["user"] = {
                    "name": s["name"],
                    "role": s["role"],
                    "school": s.get("department",""),
                    "user_id": s.get("user_id",""),
                    "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success(f"✅ تم تسجيل دخول الطالب {s['name']}")
                st.experimental_rerun()

    # --- معلمون ---
    with col2:
        st.markdown("<h3 style='text-align:center;'>👨‍🏫 المعلمون</h3>", unsafe_allow_html=True)
        teachers = df[df["role"].str.contains("معلم", case=False, na=False)]
        for _, t in teachers.iterrows():
            if st.button(f"{t['name']} — {t.get('department','')}", key=f"tea_{t['name']}"):
                st.session_state["user"] = {
                    "name": t["name"],
                    "role": t["role"],
                    "school": t.get("department",""),
                    "user_id": t.get("user_id",""),
                    "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success(f"✅ تم تسجيل دخول المعلم {t['name']}")
                st.experimental_rerun()

    # --- مدراء المكتبات ---
    with col3:
        st.markdown("<h3 style='text-align:center;'>🏛️ مدراء المكتبات</h3>", unsafe_allow_html=True)
        managers = df[df["role"].str.contains("مدير|أمين مكتبة", case=False, na=False)]
        for _, m in managers.iterrows():
            if st.button(f"{m['name']} — {m.get('department','')}", key=f"man_{m['name']}"):
                st.session_state["user"] = {
                    "name": m["name"],
                    "role": m["role"],
                    "school": m.get("department",""),
                    "user_id": m.get("user_id",""),
                    "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success(f"✅ تم تسجيل دخول المدير {m['name']}")
                st.experimental_rerun()

    st.markdown("---")
    st.caption("💡 ملاحظة: يمكن إضافة مستخدمين جدد عبر تحديث ملف users_profiles.csv.")




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

