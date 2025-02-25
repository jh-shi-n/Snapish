from flask import request, jsonify
from functools import wraps
from config import BaseConfig
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 헤더에서 토큰 가져오기
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]

        if not token:
            return jsonify({'message': '토큰이 필요합니다.'}), 401

        try:
            data = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=['HS256'])
            user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '토큰이 만료되었습니다.'}), 401
        except Exception:
            return jsonify({'message': '토큰 인증에 실패하였습니다.'}), 401

        # Pass user_id to the route
        return f(user_id, *args, **kwargs)
    return decorated