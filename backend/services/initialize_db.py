from sqlalchemy import select, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
import json

def insert_tidal_data(json_file_path):
    """
    데이터베이스 내 해양 관측소 데이터를 JSON 파일을 통해 업데이트
    """
    # JSON 파일 읽기
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            origin_data = json.load(f)
        data = [x for x in origin_data['result']['data']]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading Tidal JSON file: {e}")
        return

    from models.model import engine, TidalObservation

    # SQLAlchemy 세션 생성
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 기존 obs_post_id 조회
        result = session.execute(
            select(TidalObservation.obs_post_id)
        )
        existing_obs_post_ids = result.scalars().all()

        # 새 데이터 필터링 및 딕셔너리 리스트 변환
        new_data = [
            {
                "obs_post_id" : entry['obs_post_id'],
                "data_type" : entry['data_type'],
                "obs_post_name" : entry['obs_post_name'],
                "obs_lat" : float(entry['obs_lat']),
                "obs_lon" : float(entry['obs_lon']),
                "obs_object" : entry['obs_object'],
            }
            for entry in data if entry["obs_post_id"] not in existing_obs_post_ids
        ]

        # 데이터 삽입
        session.execute(insert(TidalObservation), new_data)
        session.commit()
        print(f"Inserted {len(new_data)} new tidal observations.")
        
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
    finally:
        session.close()

            
# 데이터 삽입 함수
def insert_fishing_place_data(json_file_path):
    """
    데이터베이스 내 낚시터 정보 데이터를 JSON 파일을 통해 업데이트
    """
    # JSON 파일 읽기
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            origin_data = json.load(f)
        data = origin_data['fishing']
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")
        return

    # 데이터 정제: usage_fee를 문자열로 변환
    for place in data:
        if not isinstance(place.get('usage_fee'), str):
            place['usage_fee'] = str(place['usage_fee'])

    from models.model import engine, FishingPlace

    # SQLAlchemy 세션 생성
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 기존 fishing_place_id 조회
        result = session.execute(
            select(FishingPlace.fishing_place_id)
        )
        existing_fishing_place_ids = result.scalars().all()

        # 새 데이터 필터링 및 딕셔너리 리스트 변환
        new_data = [
            {
                "name": entry["name"],
                "type": entry["type"],
                "address_road": entry["address_road"],
                "address_land": entry["address_land"],
                "latitude": float(entry["latitude"]),
                "longitude": float(entry["longitude"]),
                "phone_number": entry.get("phone_number"),
                "main_fish_species": entry.get("main_fish_species"),
                "usage_fee": entry.get("usage_fee"),
                "safety_facilities": entry.get("safety_facilities"),
                "convenience_facilities": entry.get("convenience_facilities"),
            }
            for entry in data if entry["fishing_place_id"] not in existing_fishing_place_ids
        ]

        if not new_data:
            print("No new fishing places to insert.")
            return

        # 데이터 삽입
        session.execute(insert(FishingPlace), new_data)
        session.commit()
        print(f"Inserted {len(new_data)} new fishing places.")
        
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
    finally:
        session.close()