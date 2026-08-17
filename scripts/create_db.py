from app.db import Base, engine

def main():
    Base.metadata.create_all(bind=engine)
    print("DB created")

if __name__ == '__main__':
    main()
