import os

baseUrl = os.getenv('BASE_URL')

def get_full_url(url):
    if not url:
        return None
    if url.startswith('http'):
        return url
    return f"{baseUrl}{url}"
