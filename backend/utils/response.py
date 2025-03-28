from flask import jsonify

def success_response(message="요청이 성공적으로 처리되었습니다.", data=None, status_code=200):
    return jsonify({
        "status": "success",
        "message": message,
        "data": data
    }), status_code

def error_response(message="잘못된 요청입니다.", error="Bad Request", status_code=400):
    return jsonify({
        "status": "error",
        "message": message,
        "error": error
    }), status_code