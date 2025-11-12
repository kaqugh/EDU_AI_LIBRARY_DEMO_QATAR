
import os, pandas as pd
from datetime import datetime

DATA_DIR = "data"
USERS_CSV = os.path.join(DATA_DIR, "users_profiles.csv")
BOOKS_CSV = os.path.join(DATA_DIR, "books_dataset.csv")
COMBINED_CSV = os.path.join(DATA_DIR, "combined_training.csv")

def main():
    users = pd.read_csv(USERS_CSV)
    books = pd.read_csv(BOOKS_CSV)

    users["text"] = (
        "User profile | name: " + users["name"].fillna("") +
        " | role: " + users["role"].fillna("") +
        " | department: " + users["department"].fillna("") +
        " | preferred_language: " + users["preferred_language"].fillna("") +
        " | interests: " + users["borrowed_subject"].fillna("")
    )
    users_out = users.rename(columns={"user_id": "id"})[["id","text"]]
    users_out["kind"] = "user"

    books["text"] = (
        "Book | title: " + books["title"].fillna("") +
        " | subject: " + books["subject"].fillna("") +
        " | language: " + books.get("language","").fillna("") +
        " | grade_level: " + books.get("grade_level","").fillna("") +
        " | description: " + books["description"].fillna("")
    )
    books_out = books.rename(columns={"id":"id"})[["id","text"]]
    books_out["kind"] = "book"

    combined = pd.concat([users_out, books_out], ignore_index=True)
    combined.to_csv(COMBINED_CSV, index=False, encoding="utf-8")
    print(f"[OK] combined_training written: {COMBINED_CSV} ({len(combined)} rows) at {datetime.now()}")

if __name__ == "__main__":
    main()
