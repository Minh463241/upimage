# utils/auth.py
from functools import wraps
from flask import session, flash, redirect, url_for

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Bạn không có quyền truy cập chức năng này", "danger")
            return redirect(url_for('staff.staff_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def staff_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role')
        if role not in ['admin', 'staff']:
            flash("Bạn cần đăng nhập với vai trò admin hoặc nhân viên để truy cập chức năng này", "danger")
            return redirect(url_for('user.index'))
        return f(*args, **kwargs)
    return decorated_function