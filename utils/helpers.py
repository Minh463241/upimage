# utils/helpers.py
import datetime
from flask import session

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def date_format(value, format_str="%d/%m/%Y"):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime(format_str)
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime(format_str)
    except Exception as e:
        return value

def inject_user():
    if 'email' in session:
        return {
            'user_email': session['email'],
            'user_avatar': session.get('user_avatar', 'default.png'),
            'user_avatar_hd': session.get('user_avatar_hd', 'default_hd.png')
        }
    return {'user_email': None}