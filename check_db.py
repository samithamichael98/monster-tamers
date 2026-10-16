
from sqlalchemy import select
from app.db.database import SessionLocal
from app.db.db_models import MonsterDB

db = SessionLocal()

try:
    monsters = db.scalars(
        select(MonsterDB).order_by(MonsterDB.id)
    ).all()

    for monster in monsters:
        print(
            f"{monster.id}: {monster.name} | "
            f"Type: {monster.type} | "
            f"Attack: {monster.attack} | "
            f"Defense: {monster.defense}"
        )
finally:
    db.close()
