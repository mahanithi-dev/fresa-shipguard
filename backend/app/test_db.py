from sqlalchemy import text
from app.db import engine


try:
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT
                    SYS_CONTEXT('USERENV', 'DB_NAME') AS db_name,
                    SYS_CONTEXT('USERENV', 'SERVICE_NAME') AS service_name
                FROM dual
            """)
        )

        print("Database connection successful!")
        print(result.fetchone())

except Exception as e:
    print("Database connection failed:")
    print(e)