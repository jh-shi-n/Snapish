from flask import current_app
from PIL import Image
from io import BytesIO
import os

def allowed_file(filename):
    """
    Check if the file has one of the allowed extensions.
    """

    files = '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

    return files
 
# 이미지 최적화 함수 추가
def optimize_image(image, max_size=1024):
    """Optimize image size and quality for mobile"""
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert to RGB if necessary
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    
    # Optimize
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=85, optimize=True)
    buffer.seek(0)
    
    return Image.open(buffer)