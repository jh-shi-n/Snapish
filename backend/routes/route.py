from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, send_from_directory, current_app
from sqlalchemy import text, func
import os
import logging
import base64
import uuid
import jwt
import io
import requests

from config import BaseConfig
from decorator import token_required
from services.weather_service import get_sea_weather_by_seapostid, get_weather_by_coordinates
from services.lunar_tide_cycle_info import get_tide_cycle, calculate_moon_phase
from services.openai_assistant import assistant_talk_request, assistant_talk_get
from utils import allowed_file, optimize_image, get_full_url, success_response, error_response, custom_sort_key

from models.model import (
    Session,
    User, Catch, AIConsent, CommunicationBoard, PostLike,
    PostComment, FishingPlace, TidalObservation
)

def set_route(app: Flask, model, device):
    # Base Page
    @app.route('/')
    def hello():
        return 'Welcome to SNAPISH'

    # 물떼 정보 받아오기
    @app.route('/api/tide-cycles', methods=['GET'])
    def get_tide_cycles_info():
        now_date = request.args.get('nowdate')
        if not now_date:
            return error_response("'nowdate' 파라미터가 필요합니다.",
                                "Bad Request",
                                400)
        try:
            parsed_date = datetime.strptime(now_date, "%Y-%m-%d")
        except ValueError:
            return error_response("Invalid date format. Use YYYY-MM-DD",
                                "Bad Request",
                                400)

        try:
            lunar_date, seohae, other = get_tide_cycle(parsed_date)
            moon_phase = calculate_moon_phase(parsed_date)
            
            json_result = {
                "lunar_date": lunar_date,
                "seohae": seohae,
                "other": other,
                "moon_phase": moon_phase,
            }
            return success_response("요청이 성공적으로 처리되었습니다.",
                                    json_result)

        except Exception as e:
            return error_response("요청 진행 중 오류가 발생하였습니다.",
                                  "Internal server error",
                                  500)
        

    @app.route('/signup', methods=['POST', 'GET'])
    def signup():
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return error_response("잘못된 요청입니다.",
                                  "Bad Request : Form error",
                                  400)
            
        session = Session()
        existing_user = session.query(User).filter(
                            (User.username == username) | (User.email == email)
                        ).first()

        if existing_user:
            session.close()
            return error_response("충돌",
                                  "Confilcted : Already existed User",
                                  409)

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            created_at=datetime.now()
        )

        session.add(new_user)
        session.commit()
        session.close()

        return success_response("요청이 성공적으로 처리되었습니다.",
                                None,
                                201)

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return error_response("정보가 정상적으로 입력되지 않았습니다.",
                                  "Bad Request",
                                  400)

        session = Session()
        try:
            user = session.query(User).filter_by(username=username).first()

            if user and check_password_hash(user.password_hash, password):
                # 토큰 생성
                payload = {
                    'user_id': user.user_id,
                    'exp': datetime.now() + timedelta(hours=24)  # 수정된 부분
                }
                token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm='HS256')

                success_login_data = {'message': '로그인 성공',
                                'token': token,
                                'user': {
                                    'user_id': user.user_id,
                                    'username': user.username,
                                    'email': user.email,
                                    # 필요한 사용자 정보 추가
                                }}

                return success_response("요청이 성공적으로 처리되었습니다",
                                        success_login_data)
            else:
                return error_response("로그인 실패 : 잘못된 아이디나 비밀번호입니다.",
                                      "Unauthorized",
                                      401)
        except Exception as e:
            return error_response("요청 진행 중 오류가 발생하였습니다.",
                                'Internal Server Error', 
                                500)
        finally:
            session.close()
            


    # predict API
    @app.route('/predict', methods=['POST'])
    @token_required
    def predict(user_id):
        try:
            if 'image' in request.files:
                file = request.files['image']
                # 파일 이름이 비어있는지 먼저 확인
                if file.filename == '':
                    return error_response("파일이 선택되지 않았습니다.",
                                          "Method Not Allowed",
                                          405)   
                # 파일 타입 검증
                if not allowed_file(file.filename):
                    return error_response("지원하지 않는 파일 형식입니다.",
                                          "Unsupported Media Type",
                                          415)               
                try:
                    img = Image.open(file.stream).convert('RGB')
                except Exception as e:
                    return error_response("요청 파일을 처리할 수 없습니다",
                                          "Bad Request",
                                          400)

            # 이미지 최적화
            try:
                img = optimize_image(img)
            except:
                return error_response("요청 파일을 처리할 수 없습니다",
                                    "Bad Request",
                                    400)

            results = model(img, exist_ok=True, device=device)
            detections = []
            
            with app.app_context():
                for result in results:  # Iterate over results
                    for cls, conf, bbox in zip(result.boxes.cls, result.boxes.conf, result.boxes.xyxy):
                        if float(conf) > current_app.config["CONF_SCORE"]:
                            detections.append({
                                'label': current_app.config["LABELS_KOREAN"].get(int(cls), '알 수 없는 라벨'),
                                'confidence': float(conf),
                                'prohibited_dates': current_app.config["PROHIBITED_DATES"].get(
                                                    current_app.config["LABELS_KOREAN"].get(int(cls), ''), ''),
                                'bbox': bbox.tolist()
                            })
                        
            detections.sort(key=lambda x: x['confidence'], reverse=True)
            
            # 검출 여부에 따라 if-else
            if detections:
                top_fish = detections[0]['label']
                try:
                    assistant_request_id = assistant_talk_request(f"{top_fish}")
                
                except Exception as e:
                    print(f"assistant_request_id 호출 실패 : {e}")
                    assistant_request_id = None

            else:
                if not results[0].boxes.cls.size(0) :
                    return error_response("물고기를 감지할 수 없습니다.",
                                          "Unprocessable Entity",
                                          422)
                else:
                    return error_response("물고기를 감지할 수 없습니다.",
                                          "No content",
                                          204)

            # 결과 DB 저장
            session = Session()
            token = request.headers.get('Authorization')
            if token:
                token = token.split(' ')[1]
                try:
                    data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=['HS256'])
                    user_id = data['user_id']
                    current_user = session.query(User).filter_by(user_id=user_id).first()
                except:
                    current_user = None
            else:
                current_user = None

            if current_user:
                # Check if catchId is provided in the request
                catch_id = request.args.get('catchId')
                if catch_id:
                    # Update existing catch
                    existing_catch = session.query(Catch).filter_by(catch_id=catch_id, user_id=current_user.user_id).first()
                    if existing_catch:
                        existing_catch.detect_data = detections
                        existing_catch.photo_url = filename
                        existing_catch.catch_date = datetime.now()
                        session.commit()
                        response_data = {
                            'id': existing_catch.catch_id,
                            'detections': detections,
                            'imageUrl': filename
                        }
                    else:
                        return jsonify({'error': 'Catch not found'}), 404
                else:
                    # Save new catch
                    filename = secure_filename(f"{uuid.uuid4().hex}.jpg")
                    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                    img.save(file_path, format='JPEG')

                    new_catch = Catch(
                        user_id=current_user.user_id,
                        photo_url=filename,
                        detect_data=detections,
                        catch_date=datetime.now()
                    )
                    session.add(new_catch)
                    session.commit()
                    response_data = {
                        'id': new_catch.catch_id,
                        'detections': detections,
                        'imageUrl': filename,
                        'assistant_request_id': assistant_request_id
                    }
            else:
                raise Exception("토큰이 필요합니다.", 
                                400)

            session.close()
            
            return success_response("요청이 성공적으로 처리되었습니다",
                                    response_data)
        except Exception as e:
            return error_response("요청 진행 중 오류가 발생하였습니다.",
                                  "Internal Server Error",
                                  500)
        
    @app.route('/predict/chat', methods=['POST'])
    def assistant_talk_result():
        thread_id = request.form.get('thread_id')
        run_id = request.form.get('run_id')
        
        print(thread_id, run_id)
        
        try:
            formatted_text = assistant_talk_get(thread_id, run_id)
            
            print(formatted_text)
            
            if not formatted_text:
                return error_response("생성된 답변이 없습니다",
                                      "Not Found",
                                      404)
                
            return success_response("요청을 성공적으로 처리하였습니다",
                                    formatted_text)
                        
        except TimeoutError:
            return error_response("요청 시간이 초과되었습니다.",
                                "TimeOut",
                                408)
        except Exception as e:
            return error_response("요청 진행 중 오류가 발생하였습니다.",
                                  "Internal server error",
                                  500)

    @app.route('/profile', methods=['GET', 'PUT'])
    @token_required
    def profile(user_id):
        session = Session()
        current_user = session.query(User).filter_by(user_id=user_id).first()
        
        # TO-DO : Add login route
        if not current_user:
            session.close()
            return error_response("현재 세션에 로그인된 유저를 찾을 수 없습니다.",
                                  "Not Found",
                                  404)

        # 로그인 이후 Profile 표시 시, 사용
        if request.method == 'GET':
            try:
                user_data = {
                    'user_id': current_user.user_id,
                    'username': current_user.username,
                    'email': current_user.email,
                    'full_name': current_user.full_name,
                    'age': current_user.age,
                    'avatar': current_user.avatar,
                }
                return success_response("요청이 성공적으로 처리되었습니다.",
                                        user_data)
            except Exception as e:
                return error_response(f"서버 오류: {str(e)}", 500)
                
            finally:
                session.close()
        
        # 로그인 이후 Profile 페이지에서 프로필 변경 시 사용
        elif request.method == 'PUT':
            data = request.get_json()
            # 기존 Form과 다른 형태거나, 데이터가 없는 경우
            if not data:
                session.close()
                return error_response("잘못된 요청입니다.",
                                      "Bad Request",
                                      400)
                
            # 비밀번호 검증 작업 수행 후, 데이터 업데이트
            try:
                if data.get('current_password') and data.get('new_password'):
                    if not check_password_hash(current_user.password_hash, data['current_password']):
                        return error_response("입력된 비밀번호가 맞지 않습니다.", 
                                              400)
                    
                    current_user.password_hash = generate_password_hash(data['new_password'])

                current_user.username = data.get('username', current_user.username)
                current_user.email = data.get('email', current_user.email)
                current_user.full_name = data.get('full_name', current_user.full_name)
                current_user.age = data.get('age', current_user.age)

                session.commit() 
                return success_response("요청이 성공적으로 처리되었습니다.", 
                                        None)

            except Exception as e:
                session.rollback()
                return error_response(f"서버 오류: {str(e)}", 
                                      500)

            finally:
                session.close()

    # # TO-DO : 현재 사용되지않는 기능, 사용할거면 Home의 updateDisplayCaches에 반영시켜야함
    # @app.route('/recent-activities', methods=['GET', 'POST'])
    # @token_required
    # def recent_activities(user_id):
    #     session = Session()
        
    #     try:
    #         current_user = session.query(User).filter_by(user_id=user_id).first()
    #         if not current_user:
    #             session.close()
    #             return error_response("유저를 찾을 수 없습니다",
    #                                 "Not Found",
    #                                 404)

    #         # 최근 활동을 조회 (예: 데이터베이스에서 최근 5개 캐치를 가져오기)
    #         activities = session.query(Catch).filter_by(user_id=current_user.user_id).order_by(Catch.catch_date.desc()).limit(5).all()
    #         session.close()
            
    #         recent_activities = [
    #             {
    #                 'fish': catch.species.name if catch.species else '알 수 없음',
    #                 'location': catch.location.address if catch.location else '알 수 없음',
    #                 'date': catch.catch_date.strftime('%Y-%m-%d'),
    #                 'image': catch.photo_url or '/placeholder.svg?height=80&width=80',
    #             }
    #             for catch in activities
    #         ]
            
    #         return success_response("요청이 성공적으로 처리되었습니다.",
    #                                 recent_activities)
    #     # jsonify({'activities': recent_activities})

    #     except:
    #         pass
    #     finally:
    #         session.close()
            

    @app.route('/catches', methods=['POST'])
    @token_required
    def create_catch(user_id):
        data = request.get_json()
        session = Session()
        try:
            new_catch = Catch(
                user_id=user_id,
                photo_url=data.get('imageUrl'),
                detect_data=data.get('detections'),
                catch_date=datetime.strptime(data.get('catch_date'), '%Y-%m-%d')
            )
            session.add(new_catch)
            session.commit()
            
            new_catch_info = {
                        'id': new_catch.catch_id,
                        'imageUrl': new_catch.photo_url,
                        'detections': new_catch.detect_data,
                        'catch_date': new_catch.catch_date.strftime('%Y-%m-%d'),
                        'weight_kg': float(new_catch.weight_kg) if new_catch.weight_kg else None,
                        'length_cm': float(new_catch.length_cm) if new_catch.length_cm else None,
                        'latitude': float(new_catch.latitude) if new_catch.latitude else None,
                        'longitude': float(new_catch.longitude) if new_catch.longitude else None,
                        'memo': new_catch.memo,
                        'message': '성공적으로 추가되었습니다.'
                        }
            
            return success_response("요청이 성공적으로 처리되었습니다",
                                    new_catch_info)
        # jsonify({
        #         'message': '성공적으로 추가되었습니다.'
        #     })
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/catches', methods=['GET', 'POST'])
    @token_required
    def get_catches(user_id):
        session = Session()
        try:
            current_user = session.query(User).filter_by(user_id=user_id).first()
            if not current_user:
                return jsonify({'message': 'User not found'}), 404

            catches = session.query(Catch).filter_by(user_id=current_user.user_id).all()
            
            # 모든 필요한 데이터를 포함하여 반환
            return jsonify([{
                'id': catch.catch_id,
                'imageUrl': catch.photo_url,
                'detections': catch.detect_data,
                'catch_date': catch.catch_date.strftime('%Y-%m-%d'),
                'weight_kg': float(catch.weight_kg) if catch.weight_kg else None,
                'length_cm': float(catch.length_cm) if catch.length_cm else None,
                'latitude': float(catch.latitude) if catch.latitude else None,
                'longitude': float(catch.longitude) if catch.longitude else None,
                'memo': catch.memo
            } for catch in catches])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/catches/<int:catch_id>', methods=['PUT'])
    @token_required
    def update_catch(user_id, catch_id):
        data = request.get_json()
        session = Session()
        try:
            catch = session.query(Catch).filter_by(catch_id=catch_id, user_id=user_id).first()
            if not catch:
                session.close()
                return jsonify({'error': 'Catch not found'}), 404

            # 데이터 유효성 검사
            try:
                if 'weight_kg' in data:
                    weight = float(data['weight_kg']) if data['weight_kg'] is not None else None
                    if weight is not None and (weight < 0 or weight > 999.999):
                        return jsonify({'error': 'Weight must be between 0 and 999.999 kg'}), 400
                    catch.weight_kg = weight

                if 'length_cm' in data:
                    length = float(data['length_cm']) if data['length_cm'] is not None else None
                    if length is not None and (length < 0 or length > 999.99):
                        return jsonify({'error': 'Length must be between 0 and 999.99 cm'}), 400
                    catch.length_cm = length

                if 'latitude' in data:
                    lat = float(data['latitude']) if data['latitude'] is not None else None
                    if lat is not None and (lat < -90 or lat > 90):
                        return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
                    catch.latitude = lat

                if 'longitude' in data:
                    lon = float(data['longitude']) if data['longitude'] is not None else None
                    if lon is not None and (lon < -180 or lon > 180):
                        return jsonify({'error': 'Longitude must be between -180 and 180'}), 400
                    catch.longitude = lon
            except ValueError:
                return jsonify({'error': 'Invalid numeric value provided'}), 400

            # Update existing fields
            if 'detections' in data:
                catch.detect_data = data['detections']
            if 'catch_date' in data:
                catch.catch_date = datetime.strptime(data['catch_date'], '%Y-%m-%d')
            if 'memo' in data:
                catch.memo = data['memo']

            session.commit()
            return jsonify({
                'id': catch.catch_id,
                'imageUrl': catch.photo_url,
                'detections': catch.detect_data,
                'catch_date': catch.catch_date.strftime('%Y-%m-%d'),
                'weight_kg': float(catch.weight_kg) if catch.weight_kg else None,
                'length_cm': float(catch.length_cm) if catch.length_cm else None,
                'latitude': float(catch.latitude) if catch.latitude else None,
                'longitude': float(catch.longitude) if catch.longitude else None,
                'memo': catch.memo
            })
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating catch: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/catches/<int:catch_id>', methods=['DELETE'])
    @token_required
    def delete_catch(user_id, catch_id):
        session = Session()
        current_user = session.query(User).filter_by(user_id=user_id).first()
        if not current_user:
            session.close()
            return jsonify({'message': 'User not found'}), 404

        catch = session.query(Catch).filter_by(catch_id=catch_id, user_id=current_user.user_id).first()
        if not catch:
            session.close()
            return jsonify({'message': 'Catch not found'}), 404

        try:
            session.delete(catch)
            session.commit()
            session.close()
            return jsonify({'message': 'Catch deleted successfully'}), 200
        except Exception as e:
            session.rollback()
            session.close()
            logging.error(f"Error deleting catch: {e}")
            return jsonify({'error': 'Error deleting catch'}), 500

    @app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
    def uploaded_file(filename):
        response = send_from_directory('uploads', filename)
        # 캐시 컨트롤 헤더 추가
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1년
        response.headers['Vary'] = 'Accept-Encoding'
        return response

    @app.route('/predict/save', methods=['GET', 'POST'])
    @token_required
    def get_detections(user_id):
        imageUrl = request.args.get('imageUrl')
        if not imageUrl:
            return jsonify({'error': 'imageUrl is required'}), 400

        try:
            session = Session()
            catch = session.query(Catch).filter_by(photo_url=imageUrl).first()
            session.close()

            if not catch:
                return jsonify({'error': 'No catch found for the provided imageUrl'}), 404

            return jsonify({'detections': catch.detect_data, 'imageUrl': catch.photo_url})
        except Exception as e:
            logging.error(f"Error in get_detections: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/spots', methods=['GET'])
    def fishing_spot_all():
        session = Session()
        fishing_spots = session.query(FishingPlace).all()
        session.close()

        try:
            locations = [{
                'fishing_place_id': spot.fishing_place_id,
                'name': spot.name,
                'type': spot.type,
                'latitude': spot.latitude,
                'longitude': spot.longitude,
                'address_road': " ".join(spot.address_road.split()[:3]),
                'address_land': " ".join(spot.address_land.split()[:3]),
            } for spot in fishing_spots]
            
            locations = sorted(locations, key=custom_sort_key)
            
            return success_response("요청을 성공적으로 처리하였습니다",
                                    locations)

        except Exception as e:
            return error_response("요청 진행 중 오류가 발생하였습니다.",
                                'Internal Server Error', 
                                500)
            
    @app.route('/api/spots/<int:spot_id>', methods=['GET'])
    def fishing_spot_by_id(spot_id):
        try:
            if not spot_id:
                return error_response("id 파라미터가 제공되지 않았습니다.", 
                                      'Bad Request', 
                                      400)

            with Session() as session:
                spot = session.query(FishingPlace).filter(FishingPlace.fishing_place_id == spot_id).first()
                
            if spot:
                location = {
                    'fishing_place_id': spot.fishing_place_id,
                    'name': spot.name,
                    'type': spot.type,
                    'latitude': spot.latitude,
                    'longitude': spot.longitude,
                    'address_road': spot.address_road,
                    'address_land': spot.address_land,
                    'phone_number': spot.phone_number,
                    'main_fish_species': spot.main_fish_species,
                    'usage_fee': spot.usage_fee,
                    'safety_facilities': spot.safety_facilities,
                    'convenience_facilities' : spot.convenience_facilities, 
                }
                return success_response("요청을 성공적으로 처리하였습니다", 
                                        location)
            else:
                return error_response("해당 ID에 맞는 낚시터를 찾을 수 없습니다.", 
                                      'Not Found', 
                                      404)

        except Exception as e:
            return error_response("요청 진행 중 오류가 발생하였습니다.",
                                'Internal Server Error',
                                500)

        
    # Endpoint to handle avatar upload
    @app.route('/profile/avatar', methods=['POST'])
    @token_required
    def upload_avatar(user_id):
        if 'avatar' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{uuid.uuid4().hex}.jpg")
            file_path = os.path.join(current_app.config["AVATAR_UPLOAD_FOLDER"], filename)
            file.save(file_path)
            
            session = Session()
            try:
                # Query the user within the new session
                current_user = session.query(User).filter_by(user_id=user_id).first()
                if not current_user:
                    return jsonify({'error': 'User not found'}), 404

                # Update user's avatar URL
                current_user.avatar = f"/uploads/avatars/{filename}"
                session.commit()
                avatar_url = current_user.avatar
            except Exception as e:
                session.rollback()
                logging.error(f"Error uploading avatar: {e}")
                return jsonify({'error': 'Avatar upload failed'}), 500
            finally:
                session.close()

            return jsonify({'message': 'Avatar uploaded successfully', 'avatarUrl': avatar_url}), 200
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
    # 요청 지점 위치와 가장 가까운 관측소의 해양 날씨 API 호출
    @app.route('/api/weather/sea', methods=['POST'])
    def get_sea_weather_api():
        lat = request.form.get('lat')
        lon = request.form.get('lon')

        if lat is None or lon is None:
            return error_response('입력값이 잘못되었습니다.', 
                                  'Invalid input',
                                  400)

        ## ST_Distance_Sphere를 사용하여 DB 내 데이터 비교 후 조건에 맞는 데이터 선정 (1)
        try:
            with Session() as session:
                query_obsrecent = session.query(
                        TidalObservation.obs_station_id,
                        TidalObservation.obs_post_id,
                        TidalObservation.obs_post_name,
                        func.ST_Distance_Sphere(
                            func.Point(lon, lat), func.Point(TidalObservation.obs_lon, TidalObservation.obs_lat)
                        ).label('distance')
                    ).filter(
                        TidalObservation.obs_object.like('%조위%'),
                        TidalObservation.obs_object.like('%수온%'),
                        TidalObservation.obs_object.like('%기온%'),
                        TidalObservation.obs_object.like('%기압%')
                    ).order_by('distance').first()
        except:
            query_obsrecent = None
            
        ## ST_Distance_Sphere를 사용하여 DB 내 데이터 비교 후 조건에 맞는 데이터 선정 (2)
        try:
            with Session() as session:
                query_obspretab = session.query(
                        TidalObservation.obs_station_id,
                        TidalObservation.obs_post_id,
                        TidalObservation.obs_post_name,
                        func.ST_Distance_Sphere(
                            func.Point(lon, lat), func.Point(TidalObservation.obs_lon, TidalObservation.obs_lat)
                        ).label('distance')
                    ).filter(
                        TidalObservation.obs_object.like('%조수간만%'),
                        TidalObservation.obs_object.notlike('%없음%')
                    ).order_by('distance').first()
        except:
            query_obspretab = None
        
        # 선정된 데이터 기반 해양 관측소 API 호출    
        try:
            if query_obsrecent and query_obspretab:
                print(f"obs recent : {query_obsrecent}")
                print(f"obs pretab : {query_obspretab}")
                # 조위 관측 정보
                obsrecent_data = {
                    'obs_station_id': query_obsrecent[0],
                    'obs_post_id': query_obsrecent[1],
                    'obs_post_name': query_obsrecent[2],
                    'distance': query_obsrecent[3] / 1000
                }

                # 조수간만 관측소 정보
                obspretab_data = {
                    'obs_station_id': query_obspretab[0],
                    'obs_post_id': query_obspretab[1],
                    'obs_post_name': query_obspretab[2],
                    'distance': query_obspretab[3] / 1000
                }

                # KHOA API 호출
                try:
                    api_data = get_sea_weather_by_seapostid({
                        'obsrecent': obsrecent_data['obs_post_id'],
                        'obspretab': obspretab_data['obs_post_id']
                    })

                    # 프론트엔드 내 렌더링 데이터 구성
                    closest_data = {
                        'obsrecent': {
                            **obsrecent_data,
                            'api_response': api_data['obsrecent']
                        },
                        'obspretab': {
                            **obspretab_data,
                            'api_response': api_data['obspretab']
                        }
                    }
                    return success_response("요청이 성공적으로 처리되었습니다",
                                            closest_data)

                except Exception as e:
                    return error_response('API request failed',
                                          e,
                                          500)
            else:
                return error_response("잘못된 요청입니다.",
                                      'Bad Request', 
                                      400)
        except Exception as e:
            return error_response("요청 진행 중 오류가 발생하였습니다.",
                                'Internal Server Error', 
                                500)
            
    @app.route('/api/weather/land', methods=['POST'])
    def get_weather_api():
        try:
            lat = request.form.get('lat')
            lon = request.form.get('lon')
            
            if not lat or not lon:
                return error_response("잘못된 요청입니다.", 
                                    'Latitude and longitude are required', 
                                    400)
            try:
                lat = float(lat)
                lon = float(lon)
                
            except Exception as e:
                return error_response("잘못된 요청입니다",
                                    'Invalid coordinate format',
                                    400)
            # Get weather data
            weather_data = get_weather_by_coordinates(lat, lon)
            if not weather_data:
                return error_response('API 호출 진행 중 문제가 발생하였습니다.',
                                        'Internal Server Error',
                                        500)
                
            return success_response("요청을 성공적으로 처리하였습니다.", 
                                    weather_data)
            
        except Exception as e:
            return error_response("요청 진행 중 문제가 발생하였습니다.",
                                  "Internal Server Error",
                                  500)
                
    @app.route('/api/consent/check', methods=['GET'])
    @token_required
    def check_consent(user_id):
        session = Session()
        try:
            consent = session.query(AIConsent).filter_by(user_id=user_id).first()
            return jsonify({
                'hasConsent': bool(consent and consent.consent_given),
                'lastConsentDate': consent.consent_date.isoformat() if consent else None
            })
        finally:
            session.close()

    @app.route('/api/consent', methods=['POST', 'GET'])
    @token_required
    def update_consent(user_id):
        data = request.get_json()
        consent_given = data.get('consent', False)
        
        session = Session()
        try:
            consent = session.query(AIConsent).filter_by(user_id=user_id).first()
            if consent:
                consent.consent_given = consent_given
                consent.consent_date = datetime.now()
            else:
                consent = AIConsent(
                    user_id=user_id,
                    consent_given=consent_given,
                    consent_date=datetime.now()
                )
                session.add(consent)
            session.commit()
            return jsonify({'message': 'Consent updated successfully'})
        finally:
            session.close()

    # 서비스 목록 API 추가
    @app.route('/api/services', methods=['GET', 'POST'])
    def get_services():
        # 기본 서비스 목록 반환
        services = [
            {
                "id": 1,
                "name": "물때 정보",
                "icon": "/icons/tide.png",
                "route": "/spots"
            },
            {
                "id": 2,
                "name": "날씨 정보",
                "icon": "/icons/weather.png",
                "route": "/spots"
            },
            {
                "id": 3,
                "name": "내 기록",
                "icon": "/icons/record.png",
                "route": "/catches"
            },
            {
                "id": 4,
                "name": "커뮤니티",
                "icon": "/icons/community.png",
                "route": "/community"
            },
            # 추가 서비스들...
        ]
        return jsonify(services)



    @app.route('/api/posts', methods=['GET', 'POST'])
    @token_required
    def get_posts(user_id):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            session = Session()
            
            # Calculate total posts and pages
            total = session.query(CommunicationBoard).count()
            offset = (page - 1) * per_page
            
            # Get posts with pagination
            posts = session.query(CommunicationBoard)\
                .order_by(CommunicationBoard.created_at.desc())\
                .offset(offset)\
                .limit(per_page)\
                .all()
                
            result = []
            for post in posts:
                user = session.query(User).get(post.user_id)
                
                # Get like status for current user
                is_liked = session.query(PostLike)\
                    .filter_by(post_id=post.post_id, user_id=user_id)\
                    .first() is not None
                
                post_data = {
                    'post_id': post.post_id,
                    'user_id': post.user_id,
                    'username': user.username if user else 'Unknown',
                    'avatar': get_full_url(user.avatar) if user and user.avatar else None,
                    'title': post.title,
                    'content': post.content,
                    'images': [get_full_url(image) for image in (post.images or [])],
                    'created_at': post.created_at.isoformat(),
                    'likes_count': session.query(PostLike).filter_by(post_id=post.post_id).count(),
                    'comments_count': session.query(PostComment).filter_by(post_id=post.post_id).count(),
                    'is_liked': is_liked
                }
                result.append(post_data)
                
            total_pages = (total + per_page - 1) // per_page
            
            return jsonify({
                'posts': result,
                'total': total,
                'pages': total_pages,
                'current_page': page
            })
        except Exception as e:
            logging.error(f"Error getting posts: {str(e)}")
            return jsonify({'error': '게시물을 불러오는 중 오류가 발생했습니다.'}), 500
        finally:
            session.close()

    @app.route('/api/posts', methods=['POST', 'GET'])
    @token_required
    def create_post(user_id):
        session = Session()
        try:
            # Get form data
            title = request.form.get('title')
            content = request.form.get('content')
            images = request.files.getlist('images')

            if not title or not content:
                return jsonify({'error': '제목과 내용은 필수입니다.'}), 400

            # Create new post
            new_post = CommunicationBoard(
                user_id=user_id,
                title=title,
                content=content,
                images=[],  # Initialize empty list for images
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Handle image uploads
            for image in images:
                if image and allowed_file(image.filename):
                    try:
                        filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                        image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                        image.save(image_path)
                        new_post.images.append(f'/uploads/{filename}')
                    except Exception as e:
                        logging.error(f"Error saving image {image.filename}: {str(e)}")
                        continue

            session.add(new_post)
            session.commit()

            # Get user info for response
            user = session.query(User).get(user_id)

            response_data = {
                'message': '게시물이 성공적으로 작성되었습니다.',
                'post': {
                    'post_id': new_post.post_id,
                    'user_id': user_id,
                    'username': user.username,
                    'avatar': get_full_url(user.avatar),
                    'title': new_post.title,
                    'content': new_post.content,
                    'images': [get_full_url(url) for url in new_post.images],
                    'created_at': new_post.created_at.isoformat(),
                    'updated_at': new_post.updated_at.isoformat(),
                    'likes_count': 0,
                    'comments_count': 0,
                    'is_liked': False
                }
            }
            return jsonify(response_data), 201

        except Exception as e:
            session.rollback()
            logging.error(f"Error creating post: {str(e)}")
            return jsonify({'error': '게시물 작성 중 오류가 발생했습니다.'}), 500
        finally:
            session.close()

    @app.route('/api/posts/<int:post_id>', methods=['GET', 'POST'])
    @token_required
    def get_post(user_id, post_id):
        session = Session()
        try:
            post = session.query(CommunicationBoard).get(post_id)
            if not post:
                return jsonify({'error': '게시물을 찾을 수 없습니다.'}), 404

            user = session.query(User).get(post.user_id)
            if not user:
                return jsonify({'error': '게시물 작성자를 찾을 수 없습니다.'}), 500

            # Check if the current user has liked this post
            is_liked = session.query(PostLike).filter_by(
                post_id=post_id,
                user_id=user_id
            ).first() is not None

            # Get counts
            likes_count = session.query(PostLike).filter_by(post_id=post_id).count()
            comments_count = session.query(PostComment).filter_by(post_id=post_id).count()

            # Handle images safely
            images = []
            if post.images:
                if isinstance(post.images, list):
                    images = [get_full_url(image) for image in post.images]
                else:
                    logging.warning(f"Unexpected images type for post {post_id}: {type(post.images)}")
                    images = []

            response_data = {
                'post_id': post.post_id,
                'user_id': post.user_id,
                'username': user.username,
                'avatar': get_full_url(user.avatar),
                'title': post.title,
                'content': post.content,
                'images': images,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat() if post.updated_at else post.created_at.isoformat(),
                'likes_count': likes_count,
                'comments_count': comments_count,
                'is_liked': is_liked
            }

            return jsonify(response_data)
        except Exception as e:
            logging.error(f"Error getting post {post_id}: {str(e)}")
            return jsonify({'error': '게시물을 불러오는 중 오류가 발생했습니다.'}), 500
        finally:
            session.close()

    @app.route('/api/posts/<int:post_id>', methods=['PUT'])
    @token_required
    def update_post(user_id, post_id):
        session = Session()
        try:
            post = session.query(CommunicationBoard).filter_by(post_id=post_id, user_id=user_id).first()
            if not post:
                return jsonify({'error': '게시물을 찾을 수 없거나 수정 권한이 없습니다.'}), 404

            # 현재 이미지 목록 백업
            current_images = post.images.copy() if post.images else []

            # 폼 데이터와 파일 가져오기
            data = request.form
            new_images = request.files.getlist('images')
            removed_images = request.form.getlist('removed_images[]')
            existing_images = request.form.getlist('existing_images[]')

            # 이미지 목록 초기화
            post.images = []

            # 기존 이미지 처리
            for image_url in existing_images:
                if image_url in current_images:
                    post.images.append(image_url)

            # 새 이미지 처리
            for image in new_images:
                if image and allowed_file(image.filename):
                    try:
                        filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                        image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                        image.save(image_path)
                        post.images.append(f'/uploads/{filename}')
                    except Exception as e:
                        logging.error(f"Error saving image {image.filename}: {str(e)}")

            # 삭제된 이미지 파일 제거
            for image_url in removed_images:
                if image_url in current_images:
                    try:
                        file_path = os.path.join(app.root_path, image_url.lstrip('/'))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        logging.error(f"Error removing file {image_url}: {str(e)}")

            # 게시물 내용 업데이트
            post.title = data.get('title', post.title)
            post.content = data.get('content', post.content)
            post.updated_at = datetime.now()

            session.commit()

            response_data = {
                'message': '게시물이 성공적으로 수정되었습니다.',
                'post': {
                    'post_id': post.post_id,
                    'title': post.title,
                    'content': post.content,
                    'images': [get_full_url(url) for url in post.images],
                    'updated_at': post.updated_at.isoformat()
                }
            }
            return jsonify(response_data)

        except Exception as e:
            session.rollback()
            logging.error(f"Error updating post {post_id}: {str(e)}")
            return jsonify({'error': '게시물 수정 중 오류가 발생했습니다.'}), 500
        finally:
            session.close()

    @app.route('/api/posts/<int:post_id>', methods=['DELETE'])
    @token_required
    def delete_post(user_id, post_id):
        session = Session()
        try:
            post = session.query(CommunicationBoard).filter_by(post_id=post_id, user_id=user_id).first()
            if not post:
                return jsonify({'error': '게시물을 찾을 수 없거나 삭제 권한이 없습니다.'}), 404

            # Delete all associated images
            if post.images:
                for image_url in post.images:
                    image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(image_url))
                    if os.path.exists(image_path):
                        os.remove(image_path)

            session.delete(post)
            session.commit()

            return jsonify({'message': '게시물이 성공적으로 삭제되었습니다.'})
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting post: {str(e)}")
            return jsonify({'error': '게시물 삭제 중 오류가 발생했습니다.'}), 500
        finally:
            session.close()

    @app.route('/api/posts/<int:post_id>/like', methods=['POST', 'GET'])
    @token_required
    def toggle_like(user_id, post_id):
        session = Session()
        try:
            # Check if post exists
            post = session.query(CommunicationBoard).get(post_id)
            if not post:
                return jsonify({'error': '게시물을 찾을 수 없습니다.'}), 404

            # Check if user already liked the post
            existing_like = session.query(PostLike).filter_by(
                post_id=post_id,
                user_id=user_id
            ).first()

            if existing_like:
                # Unlike
                session.delete(existing_like)
                session.commit()
                likes_count = session.query(PostLike).filter_by(post_id=post_id).count()
                return jsonify({
                    'message': '좋아요가 취소되었습니다.',
                    'is_liked': False,
                    'likes_count': likes_count
                })
            else:
                # Like
                new_like = PostLike(post_id=post_id, user_id=user_id)
                session.add(new_like)
                session.commit()
                likes_count = session.query(PostLike).filter_by(post_id=post_id).count()
                return jsonify({
                    'message': '좋아요가 추가되었습니다.',
                    'is_liked': True,
                    'likes_count': likes_count
                })

        except Exception as e:
            session.rollback()
            logging.error(f"Error toggling like for post {post_id}: {str(e)}")
            return jsonify({'error': '좋아요 처리 중 오류가 발생했습니다.'}), 500
        finally:
            session.close()

    @app.route('/api/posts/<int:post_id>/comments', methods=['GET', 'POST'])
    @token_required
    def get_comments(user_id, post_id):
        session = Session()
        try:
            # Check if post exists
            post = session.query(CommunicationBoard).get(post_id)
            if not post:
                return jsonify({'error': '게시물을 찾을 수 없습니다.'}), 404

            # Get comments with user information
            comments = session.query(PostComment, User).join(
                User, PostComment.user_id == User.user_id
            ).filter(
                PostComment.post_id == post_id
            ).order_by(
                PostComment.created_at.desc()
            ).all()

            comments_data = [{
                'comment_id': comment.comment_id,
                'user_id': comment.user_id,
                'username': user.username,
                'avatar': get_full_url(user.avatar),
                'content': comment.content,
                'created_at': comment.created_at.isoformat()
            } for comment, user in comments]

            return jsonify({'comments': comments_data})

        except Exception as e:
            logging.error(f"Error getting comments for post {post_id}: {str(e)}")
            return jsonify({'error': '댓글을 불러오는 중 오류가 발생했습니다.'}), 500
        finally:
            session.close()

    @app.route('/api/posts/<int:post_id>/comments', methods=['POST', 'GET'])
    @token_required
    def create_comment(user_id, post_id):
        session = Session()
        try:
            # Check if post exists
            post = session.query(CommunicationBoard).get(post_id)
            if not post:
                return jsonify({'error': '게시물을 찾을 수 없습니다.'}), 404

            data = request.get_json()
            if not data or not data.get('content'):
                return jsonify({'error': '댓글 내용이 필요합니다.'}), 400

            # Create new comment
            new_comment = PostComment(
                post_id=post_id,
                user_id=user_id,
                content=data['content']
            )
            session.add(new_comment)
            session.commit()

            # Get user info for response
            user = session.query(User).get(user_id)
            
            comment_data = {
                'comment_id': new_comment.comment_id,
                'user_id': user_id,
                'username': user.username,
                'avatar': get_full_url(user.avatar),
                'content': new_comment.content,
                'created_at': new_comment.created_at.isoformat()
            }

            return jsonify({
                'message': '댓글이 성공적으로 작성되었습니다.',
                'comment': comment_data
            })

        except Exception as e:
            session.rollback()
            logging.error(f"Error creating comment for post {post_id}: {str(e)}")
            return jsonify({'error': '댓글 작성 중 오류가 발생했습니다.'}), 500
        finally:
            session.close()

    @app.route('/api/posts/top', methods=['GET', 'POST'])
    def get_top_posts():
        session = Session()
        try:
            # Get top 5 posts by likes
            top_posts = session.query(CommunicationBoard)\
                .outerjoin(PostLike)\
                .group_by(CommunicationBoard.post_id)\
                .order_by(func.count(PostLike.like_id).desc(), CommunicationBoard.created_at.desc())\
                .limit(5)\
                .all()

            if not top_posts:
                # If no posts with likes, get the most recent 5 posts
                top_posts = session.query(CommunicationBoard)\
                    .order_by(CommunicationBoard.created_at.desc())\
                    .limit(5)\
                    .all()

            result = []
            for post in top_posts:
                user = session.query(User).get(post.user_id)
                post_data = {
                    'post_id': post.post_id,
                    'user_id': post.user_id,
                    'username': user.username if user else 'Unknown',
                    'avatar': get_full_url(user.avatar) if user else None,
                    'title': post.title,
                    'content': post.content,
                    'images': [get_full_url(image) for image in (post.images or [])],
                    'created_at': post.created_at.isoformat(),
                    'likes_count': session.query(PostLike).filter_by(post_id=post.post_id).count(),
                    'comments_count': session.query(PostComment).filter_by(post_id=post.post_id).count(),
                }
                result.append(post_data)

            return jsonify(result)
        except Exception as e:
            logging.error(f"Error getting top posts: {str(e)}")
            return jsonify({'error': 'Error fetching top posts'}), 500
        finally:
            session.close()
            
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
        
    # 애플리케이션 종료 시 세 제거
    @app.teardown_appcontext
    def remove_session(exception=None):
        Session.remove()