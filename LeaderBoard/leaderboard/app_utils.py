from werkzeug.urls import safe_url

def is_safe_url(target):
    return safe_url(target)