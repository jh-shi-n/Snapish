# config.py
from dotenv import load_dotenv
import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Call .env file
load_dotenv()

class BaseConfig(object):
    # Upload directory setup 
    UPLOAD_FOLDER = 'uploads'
    AVATAR_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
    
    # Initialize directory : upload folder
    @staticmethod
    def init_app(app):
        """
        Ensure necessary folders exist
        """
        os.makedirs(BaseConfig.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(BaseConfig.AVATAR_UPLOAD_FOLDER, exist_ok=True)
    
    # Client-allowed extension setup
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Os environment
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # AI model config
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    CONF_SCORE = 0.5
    
    # AI model - Detect result label mapping
    LABELS_KOREAN = {
        0: '감성돔',
        1: '대구',
        2: '꽃게',
        3: '갈치',
        4: '말쥐치',
        5: '넙치',
        6: '조피볼락',
        7: '삼치',
        8: '문치가자미',
        9: '참문어',
        10: '돌돔',
        11: '참돔',
        12: '낙지',
        13: '대게',
        14: '살오징어',
        15: '옥돔',
        16: '주꾸미'
        }

    # AI model - prohibited date
    PROHIBITED_DATES = {
        "넙치": "",
        "조피볼락": "",
        "참돔": "",
        "감성돔": "05.01~05.31",
        "돌돔": "",
        "명태": "01.01~12.31",
        "대구": "01.16~02.15",
        "살오징어": "04.01~05.31",
        "고등어": "04.01~06.30",
        "삼치": "05.01~05.31",
        "참문어": "05.16~06.30",
        "전어": "05.01~07.15",
        "말쥐치": "05.01~07.31",
        "주꾸미": "05.11~08.31",
        "낙지": "06.01~06.30",
        "참홍어": "06.01~07.15",
        "꽃게": "06.21~08.20",
        "대게": "06.01~11.30",
        "갈치": "07.01~07.31",
        "참조기": "07.01~07.31",
        "붉은대게": "07.10~08.25",
        "옥돔": "07.21~08.20",
        "연어": "10.01~11.30",
        "쥐노래미": "11.01~12.31",
        "문치가자미": "12.01~01.31"
    }
