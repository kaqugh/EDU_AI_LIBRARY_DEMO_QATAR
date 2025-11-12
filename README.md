
# EDU_AI_LIBRARY — Qatar (Demo)

**Bilingual / ثنائي اللغة**

## What is this?
A Streamlit demo for the Ministry of Education Qatar to explore:
- Role-based login (Student/Teacher/Librarian/Manager/Admin)
- Semantic search with FAISS (books metadata)
- Manager Dashboard with analytics
- Optional offline LLM (GPT4All) for local environments

## How to run (local)
```bash
pip install -r requirements.txt
streamlit run src/app.py
```

## Streamlit Cloud (online)
- Push this repo to GitHub
- Go to https://share.streamlit.io → New app
- Select repo, branch `main`, file path `src/app.py`
- Set secrets in **.streamlit/secrets.toml** (use the template provided)
- (Optional) Set env var `ONLINE_MODE=true`

## Notes
- `requirements.offline.txt` adds GPT4All for **offline demo** only. Do not enable on Streamlit Cloud.
- Vectors (FAISS) are created at build/run time from CSVs if needed.
- No personal data is sent externally in this demo.

---

# نظام المكتبة الذكي — وزارة التعليم قطر (نسخة تجريبية)

## المزايا
- تسجيل دخول حسب الدور (طالب/معلم/أمين مكتبة/مدير قسم/مشرف)
- بحث دلالي باستخدام FAISS على بيانات الكتب
- لوحة مدير قسم المكتبات (تحليلات وتقارير)
- نموذج أوفلاين اختياري باستخدام GPT4All

## التشغيل محليًا
```bash
pip install -r requirements.txt
streamlit run src/app.py
```

## النشر على Streamlit Cloud
- ارفع هذا المجلد إلى GitHub
- حدّد ملف التشغيل: `src/app.py`
- أضف إعدادات السرية في `.streamlit/secrets.toml` (من القالب)
- (اختياري) عيّن المتغيّر `ONLINE_MODE=true`

## ملاحظات
- `requirements.offline.txt` مخصّص للوضع الأوفلاين فقط (لا يُستخدم على السحابة).
- لا تُرسل أي بيانات حساسة خارجيًا في هذا الديمو.
