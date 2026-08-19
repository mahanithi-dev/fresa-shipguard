import os
from urllib.parse import urlparse
import oracledb

def get_oracle_credentials():
    db_url = os.environ.get("DATABASE_URL", "")
    if "oracle" in db_url:
        parsed = urlparse(db_url.replace("oracle+oracledb://", "oracle://"))
        return {
            "user": parsed.username or "SYSTEM",
            "password": parsed.password or os.environ.get("ORACLE_PASSWORD", ""),
            "dsn": f"{parsed.hostname or 'localhost'}:{parsed.port or 1521}/FREE"
        }
    return {
        "user": os.environ.get("ORACLE_USER", "SYSTEM"),
        "password": os.environ.get("ORACLE_PASSWORD", ""),
        "dsn": os.environ.get("ORACLE_DSN", "localhost:1521/FREE")
    }

def main():
    creds = get_oracle_credentials()
    if not creds["password"]:
        print("Notice: ORACLE_PASSWORD or DATABASE_URL not set in environment. Skipping live Oracle verification.")
        return

    try:
        conn = oracledb.connect(user=creds["user"], password=creds["password"], dsn=creds["dsn"])
        cursor = conn.cursor()
        cursor.execute("SELECT column_name FROM all_tab_columns WHERE table_name = 'SHIPMENTS' AND owner = :owner", owner=creds["user"].upper())
        cols = [r[0] for r in cursor.fetchall()]
        print("Columns in SHIPMENTS:", cols)

        cursor.execute("SELECT * FROM SHIPMENTS WHERE shipment_ref = :ref", ref="SHP-ORACLE-TEST-001")
        row = cursor.fetchone()
        if row:
            print("\nVerified record in Oracle SHIPMENTS table:")
            for col, val in zip(cols, row):
                print(f"  {col}: {val}")

            cursor.execute("SELECT column_name FROM all_tab_columns WHERE table_name = 'RISK_SCORES' AND owner = :owner", owner=creds["user"].upper())
            rcols = [r[0] for r in cursor.fetchall()]
            cursor.execute("SELECT * FROM RISK_SCORES WHERE shipment_id = :sid", sid=row[0])
            risk_row = cursor.fetchone()
            if risk_row:
                print("\nVerified record in Oracle RISK_SCORES table:")
                for col, val in zip(rcols, risk_row):
                    print(f"  {col}: {val}")

        conn.close()
    except Exception as e:
        print(f"Oracle verification notice: {e}")

if __name__ == "__main__":
    main()

