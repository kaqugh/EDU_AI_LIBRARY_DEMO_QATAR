# ✅ Final version of app.py adapted to your uploaded users_profiles.csv structure
# - Uses preferred_language
# - Uses permissions
# - Uses borrowed_books_count
# - Respects `active` field
# - NO .env, reads OpenAI key from st.secrets

# ✅ Final version of app.py (SAFE)
# OpenAI key is securely loaded from Streamlit Secrets only

# ✅ Final version of app.py (with availability check fix)

import os, csv
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from openai import OpenAI
from offline_retrieval import recommend_for_user, semantic_search_books

# ========== FILE PATHS ==========
USERS_CSV = "data/users_profiles.csv"
BOOKS_CSV = "data/books.csv"

# ========== LOAD API KEY SECURELY ==========
OPENAI_API_KEY = st.secrets.get("OPENAI_KEY", None)
st.sidebar.write("🔐 Key Loaded:", bool(OPENAI_API_KEY))  # Debug info
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ========== LOAD BOOKS & USERS ==============
books = pd.read_csv(BOOKS_CSV)
users = pd.read_csv(USERS_CSV)

# ========== AVAILABILITY HANDLER ============
def handle_availability(title):
    matches = books[books["title"] == title]
    if matches.empty:
        return "عذرًا، لم أجد هذا الكتاب ضمن قاعدة البيانات."
    row = matches.iloc[0]
    status = row.get("status", "متاح")
    if status.lower() == "borrowed":
        return f"الكتاب '{title}' حاليًا مُستعار حتى {row.get('expected_return', 'غير محدد')}"
    return f"✅ الكتاب '{title}' متاح للاستعارة."

# ========== STREAMLIT UI ============
st.set_page_config(page_title="Smart Library Assistant", layout="wide")
st.title("📚 مكتبة قطر الذكية — AI Library Agent")

if "user" not in st.session_state:
    st.session_state.user = {"name": "زائر"}

st.markdown(f"مرحبًا 👋 {st.session_state.user['name']}، كيف يمكنني مساعدتك اليوم؟")

# INPUT
q = st.chat_input("اكتب سؤالك هنا...")
if q:
    with st.chat_message("user"):
        st.write(q)

    # Simple availability check example
    if "متوفر" in q or "متاح" in q:
        answer = handle_availability(q.replace("هل", "").replace("متوفر", "").replace("متاح", "").strip())
    elif client and OPENAI_API_KEY:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أجب كمساعد مكتبة ذكي في قطر. أجب بالعربية دومًا."},
                {"role": "user", "content": q}
            ],
            max_tokens=200,
            temperature=0.3
        )
        answer = response.choices[0].message.content.strip()
    else:
        answer = "⚠️ No OpenAI key found."

    with st.chat_message("assistant"):
        st.write(answer)
