# ✅ Final version of app.py (restored with full login + group roles)


# ✅ Final version of app.py adapted to your uploaded users_profiles.csv structure


# - Uses preferred_language


# - Uses permissions


# - Uses borrowed_books_count


# - Respects `active` field


# - NO .env, reads OpenAI key from st.secrets





# ✅ Final version of app.py (SAFE)


# OpenAI key is securely loaded from Streamlit Secrets only



import os, csv

import streamlit as st

import pandas as pd


from datetime import datetime


from datetime import datetime, timedelta

from openai import OpenAI

from offline_retrieval import recommend_for_user, semantic_search_books



# ========== FILE PATHS ==========

USERS_CSV = "data/users_profiles.csv"

BOOKS_CSV = "data/books.csv"




# ========== LOAD API KEY ==========


# ========== LOAD API KEY SECURELY ==========

OPENAI_API_KEY = st.secrets.get("OPENAI_KEY", None)


st.sidebar.write("🔐 Key Loaded:", bool(OPENAI_API_KEY))


st.sidebar.write("🔐 Key Loaded:", bool(OPENAI_API_KEY))  # Debug info

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None




# ========== HELPER FUNCTIONS ==========


def load_users_by_role(role):


    df = pd.read_csv(USERS_CSV)


    return df[df["role"] == role]["name"].tolist()


# (rest of your app.py code remains unchanged and safe...)








# (rest of your app.py code remains unchanged and safe...)













def load_user_record(name):


    df = pd.read_csv(USERS_CSV)


    record = df[df["name"] == name]


    return record.iloc[0].to_dict() if not record.empty else None


# ========== UI HEADER ==========


def ministry_header():


    st.markdown("""


        <div style="background-color:#E8F3FB; padding:15px; border-radius:10px; border:1px solid #c8e1f0; text-align:center; font-family:'Tajawal', sans-serif;">


        <h3 style="margin:0; color:#003366;">


            🇶🇦 وزارة التربية والتعليم والتعليم العالي – 


            <span style="color:#0059b3;">Ministry of Education and Higher Education - Qatar</span>


        </h3></div>""", unsafe_allow_html=True)




# ========== LOAD DATA ==========


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


    row = [


        user.get("name"), user.get("school"), user.get("role"),


        question, (answer[:120] + "...") if answer else "",


        datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    ]


    row = [user.get("name"), user.get("role"), user.get("department"), question, answer[:120], datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

    with open("logs/user_activity.csv", "a", newline="", encoding="utf-8") as f:

        csv.writer(f).writerow(row)




def handle_availability(user):


    q = st.session_state["chat_input"]


    books = pd.read_csv(BOOKS_CSV)


    for title in books["title"]:


        if title in q:


            row = books[books["title"] == title]


            if row.empty:


                return "📚 الكتاب غير موجود في قاعدة البيانات."


            status = row["status"].values[0]


            if status == "borrowed":


                due = row["return_date"].values[0]


                return f"📕 الكتاب **{title}** مستعار حاليًا. تاريخ الإرجاع المتوقع: {due}."


            else:


                return f"📗 الكتاب **{title}** متاح حاليًا للاستعارة."


    return None





def generate_answer(user, q):


    context = f"المستخدم: {user['name']}، المدرسة: {user['school']}, الدور: {user['role']}"


    prompt = f"""


You are a helpful assistant for Qatar school libraries. Answer in the user's language.


User context: {context}


Question: {q}


"""


    response = client.chat.completions.create(


        model="gpt-3.5-turbo",


        messages=[{"role": "system", "content": "You are a school library assistant."},


                 {"role": "user", "content": prompt}],


        max_tokens=300,


        temperature=0.4,


    )


    return response.choices[0].message.content.strip()





# ========== INTERFACES ==========


def login_view():


    st.title("📘 EDU_AI_LIBRARY — Qatar")


    st.subheader("واجهة الدخول الرئيسية")





    category = st.selectbox("🧑‍🤝‍🧑 اختر الفئة:", ["طالب", "معلم", "مدير قسم المكتبات"])


    names = load_users_by_role(category)


    name = st.selectbox("🧾 اختر اسمك:", names)





    if st.button("✅ تسجيل الدخول"):


        user = load_user_record(name)


        if not user:


            st.error("المستخدم غير موجود.")


            return


        st.session_state["user"] = {


            "name": user["name"],


            "role": user["role"],


            "school": user.get("department", "")


        }


        st.success(f"مرحبًا {user['name']} 👋")


        st.rerun()


# ========== AI DETECTION ==========


def detect_language(user):


    lang = str(user.get("preferred_language", "Arabic")).lower()


    return "AR" if "arab" in lang else "EN"





def ai_answer(user, question, context=""):


    lang = detect_language(user)


    if not client:


        return "🔒 No OpenAI key found." if lang == "EN" else "🔒 لا يوجد مفتاح OpenAI مفعّل."


    prompt = f"User: {user['name']}\nContext:\n{context}\n\nQuestion: {question}"


    system_msg = "You are an intelligent library assistant for the Ministry of Education in Qatar. Reply formally in the user's preferred language."


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





# ========== LOGIC FUNCTIONS ==========


def handle_borrow(user):


    books, users = load_books(), load_users()


    uid = user["user_id"]


    uidx = users[users["user_id"] == uid].index[0]


    borrowed = str(users.loc[uidx, "borrowed_books"]).strip()


    if borrowed:


        return "📘 لديك كتاب معار حاليًا. يرجى إرجاعه أولاً."


    results = recommend_for_user(user["name"], k=1)


    if not results:


        return "📘 لم يتم العثور على كتاب للاستعارة."


    title, _ = results[0]


    bidx = books[books["title"] == title].index


    if bidx.empty:


        return "❌ لم يتم العثور على الكتاب."


    bidx = bidx[0]


    if books.loc[bidx, "status"] == "borrowing":


        return f"📕 الكتاب {title} مستعار حالياً."


    today = datetime.today().date()


    ret = today + timedelta(days=7)


    books.loc[bidx, ["status", "borrow_start", "borrow_end"]] = ["borrowing", today, ret]


    users.loc[uidx, ["borrowed_books", "borrow_start", "borrow_end", "borrowed_books_count"]] = [title, today, ret, 1]


    save_books(books)


    save_users(users)


    return f"✅ تم استعارة الكتاب **{title}** حتى تاريخ {ret}."





def handle_return(user):


    books, users = load_books(), load_users()


    uid = user["user_id"]


    uidx = users[users["user_id"] == uid].index[0]


    title = users.loc[uidx, "borrowed_books"]


    if not isinstance(title, str) or not title.strip():


        return "📘 لا يوجد كتاب لإرجاعه."


    bidx = books[books["title"] == title].index[0]


    books.loc[bidx, ["status", "borrow_start", "borrow_end"]] = ["available", "", ""]


    users.loc[uidx, ["borrowed_books", "borrow_start", "borrow_end", "borrowed_books_count"]] = ["", "", "", 0]


    save_books(books)


    save_users(users)


    return f"✅ تم إرجاع الكتاب **{title}**."




def handle_availability(user):


    books = load_books()


    results = recommend_for_user(user["name"], k=1)


    if not results:


        return "📘 لا يمكن التحقق من التوفر الآن."


    title, _ = results[0]


    row = books[books["title"] == title].iloc[0]


    if row["status"] == "available":


        return f"✅ الكتاب **{title}** متاح."


    return f"❌ الكتاب **{title}** مستعار حالياً حتى {row['borrow_end']}"





def handle_recommendation(user):


    recs = recommend_for_user(user["name"], k=3)


    return "📚 مقترحات لك: " + ", ".join([f"**{t}**" for t, _ in recs]) if recs else "لا توجد اقتراحات حالياً."





# ========== CHAT INTERFACE ==========

def chat_view():


    ministry_header()

    user = st.session_state["user"]


    st.title("💬 مكتبة قطر الذكية — AI Library Agent")


    st.markdown(f"مرحبًا 🎉 **{user['name']}** - المكتبة الذكية! كيف يمكنني مساعدتك اليوم؟")


    st.button("🏠 العودة للرئيسية", on_click=lambda: st.session_state.pop("user") or st.rerun())





    if "chat_history" not in st.session_state:


        st.session_state.chat_history = []





    for msg in st.session_state.chat_history:


        st.chat_message(msg["role"]).write(msg["content"])





    q = st.chat_input("اكتب سؤالك هنا...")


    if q:


        st.chat_message("user").write(q)


        st.session_state.chat_history.append({"role": "user", "content": q})





        ai_ans = handle_availability(user)


        if not ai_ans and client:


            ai_ans = generate_answer(user, q)


        elif not ai_ans:


            ai_ans = "⚠️ No OpenAI key found."


    lang = detect_language(user)


    if st.button("🏠 العودة للرئيسية"):


        st.session_state.clear()


        st.rerun()


    st.title("🤖 المساعد الذكي للمكتبة" if lang == "AR" else "🤖 Smart Library Assistant")


    for msg in st.session_state.get("messages", []):


        st.markdown(f"**{'🧑‍💻' if msg['role']=='user' else '🤖'}:** {msg['content']}")


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




        st.chat_message("assistant").write(ai_ans)


        st.session_state.chat_history.append({"role": "assistant", "content": ai_ans})


        log_interaction(user, q, ai_ans)


# ========== LOGIN UI ==========


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


    st.set_page_config(page_title="EDU_AI_LIBRARY — Qatar", layout="centered")


    if "user" not in st.session_state:


    st.set_page_config(page_title="EDU AI Library – Qatar", layout="wide")


    if "page" not in st.session_state:

        login_view()


    else:


    elif st.session_state["page"] == "chat":

        chat_view()


    else:


        login_view()



if __name__ == "__main__":

    main()
 
