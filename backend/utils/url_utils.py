import os
import re

baseUrl = os.getenv('BASE_URL')

def get_full_url(url):
    if not url:
        return None
    if url.startswith('http'):
        return url
    return f"{baseUrl}{url}"

def custom_sort_key(spot):
    name = spot['name'].lstrip()
    
    # 특수상황 : 아무것도없을 경우 Pass
    if not name:
        return (3, '')

    # 첫 글자 기준 정렬
    first_char = name[0]

    # 한글, 영어, 숫자, 특수문자
    if '가' <= first_char <= '힣':
        return (0, name)
    elif 'a' <= first_char.lower() <= 'z':
        return (1, name)
    else:  # 특수문자나 숫자
        return (2, name)