import os
from sqlalchemy import inspect
from models import Base, engine
from services.initialize_db import insert_fishing_place_data, insert_tidal_data


def get_json_file_path(filename):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(BASE_DIR, "data", filename)
    
    return json_file_path

def init_db():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if tables:
        print("✅ Database already initialized.")
        
    else:
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully.")
        
    print("Update Tidal & fishing Place Table..")
    fishing_place_json_file_path = get_json_file_path("fishing_place_v1.json")
    tidal_json_file_path = get_json_file_path("tidal_observations.json")
    
    insert_fishing_place_data(fishing_place_json_file_path)
    insert_tidal_data(tidal_json_file_path)
        
    print("Done")
        

if __name__ == "__main__":
    init_db()
