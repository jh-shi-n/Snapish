from routes.route import app
from flask import request
from flask_cors import CORS

import os
import torch
from ultralytics import YOLO

# Initialize variables
BASE_URL = os.getenv('BASE_URL')
AI_MODEL_URL = os.getenv('AI_MODEL_URL')

# CORS (Cross-origin resource sharing) 설정
CORS(app, resources={r"/*": {
    "origins": [f'{BASE_URL}:5000', f'{BASE_URL}:8080'],  
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}}, supports_credentials=True)

# AI Engine
try:
    if not AI_MODEL_URL:
        raise ValueError("환경 변수 'AI_MODEL_URL'이 설정되지 않았습니다.")

    model_path = os.path.abspath(AI_MODEL_URL)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"YOLO 모델 파일이 존재하지 않습니다: {model_path}")

    # Model run environment
    if torch.cuda.is_available():
        device = 'cuda'
    elif torch.backends.mps.is_available():
        device = 'mps'
    else:
        device = 'cpu'
    
    # Load Model
    model = YOLO(model_path).to(device)
    print(f"YOLO 모델 로드 완료: {model_path} (디바이스: {device})")

except Exception as e:
    print(f"Error: {e}")
    model = None

# Flask 모든 응답에 대해 후처리 수행하도록 설정
@app.after_request
def add_header(response):
    """
    Cache setting for upload directory (1 year)
    """
    if request.path.startswith('/uploads/'):
        response.cache_control.max_age = 31536000  
        response.cache_control.public = True
    return response
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)