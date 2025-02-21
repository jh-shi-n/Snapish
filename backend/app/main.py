from routes.route import app
from flask import request
from flask_cors import CORS

import os
import torch
from ultralytics import YOLO

baseUrl = os.getenv('BASE_URL')

CORS(app, resources={r"/*": {
    "origins": [f'{baseUrl}:5000', f'{baseUrl}:8080'],  # Ensure this matches your frontend's origin
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}}, supports_credentials=True)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = YOLO(f'./data/yolo11m_aug6_plus.pt').to(device)

# 초시 헤더를 한 after_request 데코레이터를 앱 초기화 직후에 추가
@app.after_request
def add_header(response):
    if request.path.startswith('/uploads/'):
        response.cache_control.max_age = 31536000  # 1년
        response.cache_control.public = True
    return response
        

# Ensure the backend server is running on port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)