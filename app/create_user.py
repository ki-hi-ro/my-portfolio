from app.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

db = SessionLocal()

users = [
    {
        "username": "hiroki",
        "password": "M2MWVwnXNkCZ",
        "role": "admin"
    },
    {
        "username": "partner",
        "password": "qCxeiBn7Bz92",
        "role": "partner"
    }
]

for user_data in users:

    existing_user = (
        db.query(User)
        .filter(
            User.username == user_data["username"]
        )
        .first()
    )

    if existing_user:
        print(
            f'{user_data["username"]} は既に存在します'
        )
        continue

    user = User(
        username=user_data["username"],
        password_hash=pwd_context.hash(
            user_data["password"]
        ),
        role=user_data["role"]
    )

    db.add(user)

db.commit()

print("ユーザー作成完了")

db.close()
