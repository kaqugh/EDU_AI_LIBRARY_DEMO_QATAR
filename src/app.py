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
# Function: Login View (Three Main Icons)
# -------------------------------------------------------------
def login_view():
    st.title("📘 EDU_AI_LIBRARY — Qatar")
    st.subheader("واجهة الدخول الرئيسية")

    df = pd.read_csv(USERS_CSV)
    col1, col2, col3 = st.columns(3)

    st.markdown("### 👥 اختر الفئة:")

    # --- Students Button ---
    with col1:
        if st.button("🎓 الطلاب", use_container_width=True):
            st.session_state["selected_group"] = "طالب"
            st.experimental_rerun()

    # --- Teachers Button ---
    with col2:
        if st.button("👨‍🏫 المعلمون", use_container_width=True):
            st.session_state["selected_group"] = "معلم"
            st.experimental_rerun()

    # --- Library Managers Button ---
    with col3:
        if st.button("🏛️ موظفو الوزارة", use_container_width=True):
            st.session_state["selected_group"] = "مدير قسم المكتبات"
            st.experimental_rerun()

    # --- Show group members when clicked ---
    if "selected_group" in st.session_state:
        group = st.session_state["selected_group"]
        st.markdown(f"### 🧾 قائمة {group}:")

        filtered = df[df["role"].str.contains(group, case=False, na=False)]
        selected_name = st.selectbox("اختر اسمك من القائمة:", filtered["name"].tolist())

        if st.button("✅ تسجيل الدخول", use_container_width=True):
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
            st.success(f"✅ تم تسجيل دخول {user['name']}")
            st.experimental_rerun()


# -------------------------------------------------------------
# Function: Chat View (AI Library Conversation)
# -------------------------------------------------------------
def chat_view():
    user = st.session_state.get("user", {})
    st.sidebar.success(f"✅ {user.get('name','')} — {user.get('role','')}")
    st.title("💬 مكتبة قطر الذكية – AI Library Agent")

    # Display all messages
    for msg in st.session_state.get("messages", []):
        if msg["role"] == "assistant":
            st.markdown(f"**🤖 المكتبة الذكية:** {msg['content']}")
        else:
            st.markdown(f"**🧑‍💻 {user.get('name','المستخدم')}:** {msg['content']}")

    # Chat input
    q = st.chat_input("اكتب سؤالك هنا...")
    if q:
        st.session_state["messages"].append({"role": "user", "content": q})
        # Generate a simple answer (demo mode)
        ans = f"📚 المكتبة الذكية: سؤالك كان '{q}'. سأساعدك بالبحث عن الكتب والمراجع ذات الصلة."
        st.session_state["messages"].append({"role": "assistant", "content": ans})
        log_interaction(user, q, ans)
        st.experimental_rerun()


# -------------------------------------------------------------
# Function: Main Entry
# -------------------------------------------------------------
def main():
    st.set_page_config(page_title="EDU_AI_LIBRARY — Online Demo", layout="wide")
    if "page" not in st.session_state:
        login_view()
    elif st.session_state["page"] == "chat":
        chat_view()
    else:
        login_view()


if __name__ == "__main__":
    main()
