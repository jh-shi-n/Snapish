from sqlalchemy import inspect
from models import Base, engine

def init_db():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if tables:
        print("✅ Database already initialized. Skipping table creation.")
        
    else:
        print("🚀 Initializing database tables...")
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully.")


if __name__ == "__main__":
    init_db()
