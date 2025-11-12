
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from collections import Counter

LOGS_CSV = "logs/user_activity.csv"
BOOKS_CSV = "data/books_dataset.csv"
USERS_CSV = "data/users_profiles.csv"

def manager_dashboard_full():
    st.header("📊 لوحة مدير قسم المكتبات — EDU_AI_LIBRARY (شاملة)")
    st.caption("تحليلات الكتب والمستخدمين والنشاط")

    if not os.path.exists(LOGS_CSV):
        st.warning("⚠️ لا يوجد نشاط مسجل بعد.")
        return

    logs = pd.read_csv(LOGS_CSV, names=["name","school","role","question","answer","timestamp"])
    books = pd.read_csv(BOOKS_CSV)
    users = pd.read_csv(USERS_CSV)

    # 🔔 تنبيهات ذكية
    st.subheader("🔔 التنبيهات الذكية")
    if len(logs) > 0:
        logs["timestamp"] = pd.to_datetime(logs["timestamp"], errors="coerce")
        recent = logs[logs["timestamp"] >= pd.Timestamp.today().normalize() - pd.Timedelta(days=7)]
        if len(recent) > 0:
            st.success(f"📈 نشاط أسبوعي: {len(recent)} تفاعل جديد خلال آخر 7 أيام.")
        else:
            st.warning("⚠️ لا يوجد نشاط جديد خلال الأسبوع الحالي.")
    else:
        st.info("لا توجد بيانات كافية للتنبيهات.")

    # KPIs
    st.subheader("📈 مؤشرات الأداء")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("عدد المستخدمين", len(users))
    c2.metric("عدد الكتب", len(books))
    c3.metric("عمليات البحث", len(logs))
    c4.metric("عدد المدارس/الأقسام", users["department"].nunique())

    # حالة الكتب
    st.subheader("📚 حالة الكتب")
    if "availability" in books.columns:
        st.bar_chart(books["availability"].value_counts())
    else:
        st.info("لم يتم تحديد عمود 'availability' في الكتب.")

    # النشاط حسب الدور
    st.subheader("👥 النشاط حسب الدور")
    st.bar_chart(logs["role"].value_counts())

    # المدارس الأكثر نشاطًا
    st.subheader("🏫 المدارس/الأقسام الأكثر نشاطًا")
    st.bar_chart(logs["school"].value_counts().head(10))

    # الكلمات الأكثر شيوعًا
    st.subheader("🧠 الكلمات الشائعة في الأسئلة")
    all_words = " ".join(logs["question"].dropna().astype(str)).split()
    common = Counter(all_words).most_common(10)
    st.dataframe(pd.DataFrame(common, columns=["الكلمة","عدد التكرار"]))

    # النشاط الزمني
    st.subheader("⏱️ النشاط الزمني")
    if logs["timestamp"].notnull().any():
        logs["date"] = logs["timestamp"].dt.date
        daily = logs.groupby("date").size()
        st.line_chart(daily)

    # الاستعارات حسب المادة
    st.subheader("📦 الاستعارات/الاهتمامات حسب المادة")
    if "subject" in books.columns:
        st.bar_chart(books["subject"].value_counts().head(10))

    # المستخدمون الأكثر تفاعلًا
    st.subheader("⭐ المستخدمون الأكثر تفاعلًا")
    st.table(logs["name"].value_counts().head(10))

    # تصدير
    st.subheader("📤 تصدير التقرير")
    csv_data = logs.to_csv(index=False)
    st.download_button("📥 تحميل CSV", csv_data, file_name=f"library_logs_{datetime.now().date()}.csv")

    with st.expander("👁️‍🗨️ عرض قواعد البيانات"):
        tabA, tabB, tabC = st.tabs(["📗 الكتب","👥 المستخدمون","🕓 السجلات"])
        with tabA: st.dataframe(books)
        with tabB: st.dataframe(users)
        with tabC: st.dataframe(logs)
