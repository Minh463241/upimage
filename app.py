# app.py
import os
from flask import Flask
from datetime import timedelta
from dotenv import load_dotenv
import paypalrestsdk
import cloudinary
from routes.user_routes import user_bp
from routes.payment_routes import payment_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp
from routes.utility_routes import utility_bp
from routes.account_routes import account_bp  # Thêm import này
from utils.helpers import date_format, inject_user

# Load biến môi trường từ .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=7)

cloudinary.config(
    cloud_name="dwczro6hp",
    api_key="648677879979597",
    api_secret="-1D5fNq5hrtfGoIeZ8U7n8GHWi0",
    secure=True
)
paypalrestsdk.configure({
    "mode": "sandbox",  # "sandbox" hoặc "live"
    "client_id": "AWsHRyezYDAKZLpJRjtJz2gmGbSJKnNSM9m5YKqOF0QIcpc19g9npAJX_W9zijWkORfHn4xRBgkW-MCX",
    "client_secret": "EFHP2SK80y2L3Q-8R9o_QQpbB0-cK848UyTr0YqVllZ8l8qe_DiGrQgUvq6N_V7ESxedUIXgeQtu5zfC"
})

# Cấu hình upload file
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'avatars')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Đăng ký Blueprints
app.register_blueprint(user_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(utility_bp)
app.register_blueprint(account_bp, url_prefix='/admin')  # Thêm Blueprint mới

# Đăng ký template filter và context processor
app.jinja_env.filters['date_format'] = date_format
app.context_processor(inject_user)

if __name__ == '__main__':
    app.run(debug=True)