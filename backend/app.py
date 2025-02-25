from ai_engine import get_model
from routes.route import set_route
from config import BaseConfig
from flask import Flask
from flask_cors import CORS
import os

# Initialize variables
BASE_URL = os.getenv('BASE_URL')
AI_MODEL_URL = os.getenv('AI_MODEL_URL')

model, device = get_model(AI_MODEL_URL)

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(BaseConfig)
    BaseConfig.init_app()
    
    # CORS (Cross-origin resource sharing) 설정
    CORS(app, resources={r"/*": {
        "origins": [f'{BASE_URL}:5000', f'{BASE_URL}:8080'],  
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }}, supports_credentials=True)

    # 엔드포인트 등록
    set_route(app, model, 'cpu')
    
    return app
        
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)