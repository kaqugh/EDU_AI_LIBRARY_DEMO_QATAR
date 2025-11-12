import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime

from offline_retrieval import recommend_for_user, semantic_search_books
from manager_dashboard_full import manager_dashboard_full

# -------------------------------------------------------------------
# Global setup
# -------------------------------------------------------------------
ONLINE_MODE = os.environ.get("ONLINE_MODE", "true").lower() == "true"
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
# Login / Homepage View
# -------------------------------------------------------------------
def login_view():
    st.title("📘 EDU_AI_LIBRARY — Qatar")
    st.subheader("واجهة الدخول الرئيسية")

    # Load users
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

    # Show user list if group selected
    if "selected_group" in st.session_state:
        group = st.session_state["selected_group"]
        st.markdown(f"### 🧾 قائمة {group}:")

        filtered = df[df["role"].str.contains(group, case=False, na=False)]
        if filtered.empty:
            st.warning("⚠️ لا توجد أسماء ضمن هذه الفئة.")
            return

        selected_name = st.selectbox(
            "اختر اسمك الكامل:", filtered["name"].tolist(), key="user_select"
        )

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
                {"role": "assistant", "content": f"🎉 مرحبًا {user['name']}! هذه مكتبتك الذكية. كيف يمكنني مساعدتك اليوم؟"}
            ]
            st.toast(f"✅ تم تسجيل دخول {user['name']}")
            st.stop()


# -------------------------------------------------------------------
# Chat View
# -------------------------------------------------------------------
def chat_view():
    user = st.session_state.get("user", {})

    # Top bar with back button
    cols = st.columns([0.15, 0.85])
    with cols[0]:
        if st.button("🏠 العودة للرئيسية", help="العودة إلى واجهة الدخول"):
            st.session_state.clear()
            st.stop()
    with cols[1]:
        st.title("💬 مكتبة قطر الذكية — AI Library Agent")

    st.sidebar.success(f"✅ {user.get('name','')} — {user.get('role','')}")

    # Display messages
    for msg in st.session_state.get("messages", []):
        if msg["role"] == "assistant":
            st.markdown(f"**🤖 المكتبة الذكية:** {msg['content']}")
        else:
            st.markdown(f"**🧑‍💻 {user.get('name','المستخدم')}:** {msg['content']}")

    # Chat input
    q = st.chat_input("اكتب سؤالك هنا...")
    if q:
        st.session_state["messages"].append({"role": "user", "content": q})
        ans = f"📚 المكتبة الذكية: سؤالك كان '{q}'. سأساعدك في العثور على الكتب والمراجع المناسبة."
        st.session_state["messages"].append({"role": "assistant", "content": ans})
        log_interaction(user, q, ans)
        st.stop()


# -------------------------------------------------------------------
# Main Controller
# -------------------------------------------------------------------
def main():
    st.set_page_config(page_title="EDU_AI_LIBRARY — Online Demo", layout="wide")

    # Routing between pages
    if "page" not in st.session_state:
        login_view()
    elif st.session_state["page"] == "chat" and "user" in st.session_state:
        chat_view()
    else:
        login_view()


if __name__ == "__main__":
    main()

