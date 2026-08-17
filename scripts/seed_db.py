from app.seed import seed_demo_data
from app.db import SessionLocal

def main():
    db = SessionLocal()
    try:
        seed_demo_data(db)
        print("Seeded demo data")
    finally:
        db.close()

if __name__ == '__main__':
    main()
