from sqlalchemy import text
from app.db.session import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("Connection successful!")
        print(result.scalar())

except Exception as error:
    print("Connection failed!")
    print(error)