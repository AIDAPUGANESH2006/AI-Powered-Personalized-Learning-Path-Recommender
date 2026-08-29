from app.database import engine
from sqlalchemy import text
try:
    with engine.connect() as c:
        r = c.execute(text("SELECT version()"))
        print("DB OK:", r.fetchone()[0][:60])
except Exception as e:
    print("FAIL:", e)
