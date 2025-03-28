from sqlalchemy import (
                    create_engine, Column, Integer, String, DateTime, ForeignKey, 
                    Enum, Boolean, Text, DECIMAL, JSON, Float, VARCHAR, 
                    )
from sqlalchemy.orm import relationship, sessionmaker, scoped_session, declarative_base

from config import BaseConfig
from datetime import datetime

# DATABASE 엔진 생성
engine = create_engine(BaseConfig.DATABASE_URL, pool_pre_ping=True)
Session = scoped_session(sessionmaker(bind=engine))

# DATABASE base 모델 선언
Base = declarative_base()

# 데이터베이스 모델 정의
class User(Base):
    __tablename__ = 'Users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    full_name = Column(String(100))
    age = Column(Integer)
    preferred_font_size = Column(Enum('small', 'medium', 'large'), default='medium')
    avatar = Column(String(255), nullable=True)  # New field for avatar
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship('UserSession', back_populates='user', cascade='all, delete')
    locations = relationship('Location', back_populates='user', cascade='all, delete')
    catches = relationship('Catch', back_populates='user', cascade='all, delete')
    rankings = relationship('Ranking', back_populates='user', cascade='all, delete')
    ai_consent = relationship('AIConsent', back_populates='user', uselist=False, cascade='all, delete')
    fish_diaries = relationship('FishDiary', back_populates='user', cascade='all, delete')
    posts = relationship('CommunicationBoard', back_populates='user', cascade='all, delete')
    tournament_participants = relationship('TournamentParticipant', back_populates='user', cascade='all, delete')


class UserSession(Base):
    __tablename__ = 'UserSessions'

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    session_token = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    user = relationship('User', back_populates='sessions')


class Location(Base):
    __tablename__ = 'Locations'

    location_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    address = Column(String(255))
    manual_entry = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='locations')
    weather_data = relationship('WeatherData', back_populates='location', cascade='all, delete')
    catches = relationship('Catch', back_populates='location', cascade='all, delete')


class FishSpecies(Base):
    __tablename__ = 'FishSpecies'

    species_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum('freshwater', 'saltwater'), nullable=False)
    is_prohibited = Column(Boolean, default=False)
    prohibited_season_start = Column(DateTime)
    prohibited_season_end = Column(DateTime)
    seasonal_info = Column(String(255))
    bait_recommendation = Column(String(255))

    catches = relationship('Catch', back_populates='species')


class Catch(Base):
    __tablename__ = 'Catches'

    catch_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    location_id = Column(Integer, ForeignKey('Locations.location_id', ondelete='CASCADE'))
    species_id = Column(Integer, ForeignKey('FishSpecies.species_id', ondelete='SET NULL'))
    catch_date = Column(DateTime, default=datetime.utcnow)
    fish_size_cm = Column(DECIMAL(5, 2))
    photo_url = Column(String(255))
    detect_data = Column(JSON)
    weight_kg = Column(DECIMAL(10, 3), nullable=True)  # 무게(kg)
    length_cm = Column(DECIMAL(10, 2), nullable=True)  # 길이(cm)
    latitude = Column(DECIMAL(10, 8), nullable=True)  # 위도
    longitude = Column(DECIMAL(11, 8), nullable=True)  # 경도
    memo = Column(Text, nullable=True)  # 메모

    user = relationship('User', back_populates='catches')
    location = relationship('Location', back_populates='catches')  # Existing line
    species = relationship('FishSpecies', back_populates='catches')  # Existing line
    tournament_participants = relationship('TournamentParticipant', back_populates='catch')  # Add this line
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIConsent(Base):
    __tablename__ = 'AIConsent'

    consent_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime, default=datetime.utcnow)  # 동의 날짜 추가
    consent_type = Column(String(50))  # 동의 유형 추가 (예: 'fish_data', 'privacy')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='ai_consent')


class FishDiary(Base):
    __tablename__ = 'FishDiaries'

    diary_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    title = Column(String(255))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='fish_diaries')


class CommunicationBoard(Base):
    __tablename__ = 'CommunicationBoard'

    post_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    title = Column(String(255))
    content = Column(Text)
    images = Column(JSON, default=list)  # Store multiple image URLs as JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='posts')
    likes = relationship('PostLike', back_populates='post', cascade='all, delete')
    comments = relationship('PostComment', back_populates='post', cascade='all, delete')
    retweets = relationship('PostRetweet', back_populates='post', cascade='all, delete')


class PostLike(Base):
    __tablename__ = 'PostLikes'

    like_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('CommunicationBoard.post_id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship('CommunicationBoard', back_populates='likes')
    user = relationship('User')


class PostComment(Base):
    __tablename__ = 'PostComments'

    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('CommunicationBoard.post_id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post = relationship('CommunicationBoard', back_populates='comments')
    user = relationship('User')


class PostRetweet(Base):
    __tablename__ = 'PostRetweets'

    retweet_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('CommunicationBoard.post_id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship('CommunicationBoard', back_populates='retweets')
    user = relationship('User')


class WeatherData(Base):
    __tablename__ = 'WeatherData'

    weather_id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey('Locations.location_id', ondelete='CASCADE'))
    date = Column(DateTime, default=datetime.utcnow)
    weather_info = Column(JSON)
    tide_data = Column(JSON)

    location = relationship('Location', back_populates='weather_data')


class Tournament(Base):
    __tablename__ = 'Tournaments'

    tournament_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    participants = relationship('TournamentParticipant', back_populates='tournament', cascade='all, delete')


class TournamentParticipant(Base):
    __tablename__ = 'TournamentParticipants'

    participant_id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey('Tournaments.tournament_id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    catch_id = Column(Integer, ForeignKey('Catches.catch_id', ondelete='SET NULL'))
    score = Column(Integer)

    tournament = relationship('Tournament', back_populates='participants')
    user = relationship('User', back_populates='tournament_participants')
    catch = relationship('Catch', back_populates='tournament_participants')

# Add the Ranking class
class Ranking(Base):
    __tablename__ = 'Rankings'

    ranking_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id', ondelete='CASCADE'))
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='rankings')

# Add the TidalObservation class
class TidalObservation(Base):
    __tablename__ = 'TidalObservations'

    obs_station_id = Column(Integer, primary_key=True, autoincrement=True)
    obs_post_id = Column(String(20), unique=True)  # 고유 키로 설정
    obs_post_name = Column(String(50), nullable=False)
    obs_lat = Column(Float, nullable=False)
    obs_lon = Column(Float, nullable=False)
    data_type = Column(String(50), nullable=False)
    obs_object = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# 낚시터 db 컬럼
class FishingPlace(Base):
    __tablename__ = 'FishingPlace'

    fishing_place_id = Column(Integer, primary_key=True, autoincrement=True)  # 고유 식별자
    name = Column(String(255), nullable=False)  # 낚시터명
    type = Column(String(100), nullable=False)  # 낚시터 유형
    address_road = Column(String(255), nullable=True)  # 소재지 도로명 주소
    address_land = Column(String(255), nullable=True)  # 소재지 지번 주소
    latitude = Column(Float, nullable=False)  # WGS84 위도
    longitude = Column(Float, nullable=False)  # WGS84 경도
    phone_number = Column(String(50), nullable=True)  # 낚시터 전화번호
    main_fish_species = Column(Text, nullable=True)  # 주요 어종
    usage_fee = Column(VARCHAR(500), nullable=True)  # 이 요금
    safety_facilities = Column(Text, nullable=True)  # 안전 시설 현황
    convenience_facilities = Column(Text, nullable=True)  # 편익 시설 현황
