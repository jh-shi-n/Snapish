import os
import torch
from ultralytics import YOLO

def get_model(model_url):
    """
    Function for load AI model (YOLO)
    """
    try:
        if not model_url:
            raise ValueError("환경 변수 'AI_MODEL_URL'이 설정되지 않았습니다.")

        model_path = os.path.abspath(model_url)

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
        
    return model, device