# ✅ Final version of app.py adapted to your uploaded users_profiles.csv structure
# - Uses preferred_language
# - Uses permissions
# - Uses borrowed_books_count
# - Respects `active` field
# - NO .env, reads OpenAI key from st.secrets

# ✅ Final version of app.py (SAFE)
# OpenAI key is securely loaded from Streamlit Secrets only

# ✅ Final version of app.py (with availability check fix)
# ✅ النسخة السابقة من app.py مع واجهة تسجيل دخول للمجموعات الثلاث (طلاب، معلمون، موظفو الوزارة)
# ✅ Final version of app.py (Role-Based Login + GPT + Availability Handling)
row = books[books["title"] == title]
if not row.empty:
status = row.iloc[0]["status"]
return f"📚 حالة الكتاب '{title}': {'متوفر حاليًا ✅' if status == 'available' else 'مستعار حاليًا ❌'}"
return None


# ========== CHAT VIEW ==========
def chat_view():
st.title("💬 مكتبة قطر الذكية — AI Library Agent")
user = st.session_state.user
st.markdown(f"مرحبًا {user['name']} 🎉 — **{user['role']}**")


for msg in st.session_state.chat:
align = "🧑‍🏫" if msg["role"] == "user" else "🤖"
st.markdown(f"{align} : {msg['content']}")


q = st.chat_input("اكتب سؤالك هنا...", key="chatbox")
if q:
st.session_state.chat.append({"role": "user", "content": q})
ans = handle_availability(user)


if not ans and client:
prompt = f"""You are a helpful assistant for Qatar school libraries. Answer in the user's language.
User Role: {user['role']}
Department: {user['department']}
Question: {q}"
response = client.chat.completions.create(
model="gpt-3.5-turbo",
messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat[-3:]] + [{"role": "user", "content": prompt}]
)
ans = response.choices[0].message.content.strip()


st.session_state.chat.append({"role": "assistant", "content": ans or "لم أتمكن من فهم سؤالك تمامًا. حاول بصيغة أخرى."})
st.experimental_rerun()


# ========== LOGIN VIEW ==========
def login_view():
st.title("📘 EDU_AI_LIBRARY — Qatar")
st.subheader("واجهة الدخول الرئيسية")


group = st.selectbox("👥 اختر الفئة:", ["الطلاب", "المعلمون", "مدير قسم المكتبات"])
role_map = {"الطلاب": "طالب", "المعلمون": "معلم", "مدير قسم المكتبات": "مدير قسم المكتبات"}
filtered = users[users["role"] == role_map[group]]
name = st.selectbox("👤 اختر اسمك:", filtered["name"].tolist())


if st.button("🚀 تسجيل الدخول"):
user_row = filtered[filtered["name"] == name].iloc[0].to_dict()
st.session_state.user = {
"name": user_row["name"],
"role": user_row["role"],
"department": user_row.get("department", "")
}
st.session_state.chat = []
st.experimental_rerun()


# ========== MAIN ==============
def main():
if st.session_state.user is None:
login_view()
else:
if st.button("🏠 العودة للرئيسية"):
st.session_state.user = None
st.session_state.chat = []
st.experimental_rerun()
if st.session_state.user["role"] == "مدير قسم المكتبات":
manager_dashboard_full()
chat_view()


if __name__ == "__main__":
main()
