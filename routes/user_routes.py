# routes/user_routes.py
import os
from flask import Blueprint, current_app, flash, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import io
from db_mongo import (
    rooms_collection,
    create_customer, get_all_rooms, get_customer_by_email, update_last_login, update_user_avatar,
    get_booking_history_by_customer, get_services_used_by_customer, update_customer,
    get_room_by_id, create_booking, get_booking_by_id, update_booking
)
from utils.helpers import allowed_file

user_bp = Blueprint('user', __name__, template_folder='../templates/user')

@user_bp.route('/')
def index():
    user_email = session.get('email')
    user_avatar = session.get('avatar', 'default.jpg')
    rooms = get_all_rooms()
    popular = session.get('popular')
    tiennghi = session.get('tiennghi')
    xephang = session.get('xephang')
    rating = session.get('rating')
    return render_template(
        'index.html',
        user_email=user_email,
        user_avatar=user_avatar,
        rooms=rooms,
        filter_popular=popular,
        filter_tiennghi=tiennghi,
        filter_xephang=xephang,
        filter_rating=rating
    )

@user_bp.route('/search', methods=['GET'])
def search():
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')
    adults = request.args.get('adults')
    children = request.args.get('children')
    popular = request.args.get('popular')
    tiennghi = request.args.get('tiennghi')
    xephang = request.args.get('xephang')
    rating = request.args.get('rating')
    description = request.args.get('description')
    
    if not checkin or not checkout or not adults or not children:
        flash("Vui lòng nhập đầy đủ thông tin tìm kiếm!", "error")
        return redirect(url_for('user.index'))
    
    filters = {
        "checkin": checkin,
        "checkout": checkout,
        "adults": adults,
        "children": children,
        "popular": popular,
        "tiennghi": tiennghi,
        "xephang": xephang,
        "rating": rating,
        "description": description
    }
    
    query = {}
    if description:
        query["MoTa"] = {"$regex": description, "$options": "i"}
    if tiennghi:
        query["MoTa"] = {"$regex": tiennghi, "$options": "i"}
    
    print("[DEBUG] Query tìm kiếm:", query)
    rooms = list(rooms_collection.find(query))
    
    if not rooms:
        flash("Không tìm thấy kết quả phù hợp!", "info")
    
    return render_template('index.html', 
                           rooms=rooms,
                           checkin=checkin,
                           checkout=checkout,
                           adults=adults,
                           children=children,
                           filter_popular=popular,
                           filter_tiennghi=tiennghi,
                           filter_xephang=xephang,
                           filter_rating=rating,
                           description=description)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
        
        user = get_customer_by_email(email)
        if user:
            if user.get('password') == password:
                session.permanent = True
                session['user_id'] = str(user.get('_id'))
                session['email'] = user.get('Email')
                update_last_login(user.get('Email'))
                if request.is_json:
                    return jsonify({"success": True, "message": "Đăng nhập thành công"})
                else:
                    return redirect(url_for('user.index'))
            else:
                if request.is_json:
                    return jsonify({"success": False, "message": "Mật khẩu không chính xác"})
                else:
                    flash("Mật khẩu không chính xác", "error")
                    return redirect(url_for('user.login'))
        else:
            if request.is_json:
                return jsonify({"success": False, "message": "Không tìm thấy tài khoản với email này"})
            else:
                flash("Không tìm thấy tài khoản với email này", "error")
                return redirect(url_for('user.login'))

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        ho_ten = request.form.get('ho_ten')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        dia_chi = request.form.get('dia_chi')
        cmnd = request.form.get('cmnd')
        
        if get_customer_by_email(email):
            flash("Email đã được sử dụng, vui lòng sử dụng email khác.", "error")
            return redirect(url_for('user.register'))
        
        customer_data = {
            'HoTen': ho_ten,
            'Email': email,
            'password': password,
            'DienThoai': phone,
            'DiaChi': dia_chi,
            'CMND': cmnd,
            'last_login': None,
            'avatar': None
        }
        user_id = create_customer(customer_data)
        if user_id:
            flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for('user.login'))
        else:
            flash("Đăng ký thất bại.", "error")
            return redirect(url_for('user.register'))

@user_bp.route('/update_avatar', methods=['GET', 'POST'])
def update_avatar():
    if 'user_id' not in session or 'email' not in session:
        flash("Bạn cần đăng nhập để thay đổi avatar.", "error")
        return redirect(url_for('user.login'))
    
    if request.method == 'GET':
        return render_template('update_avatar.html')
    else:
        if 'avatar' not in request.files:
            flash("Không tìm thấy file tải lên.", "error")
            return redirect(request.url)
        
        file = request.files['avatar']
        if file.filename == '':
            flash("Bạn chưa chọn file.", "error")
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"user_{session['user_id']}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
            file.save(file_path)
            update_user_avatar(session['email'], filename)
            session['avatar'] = filename
            flash("Avatar cập nhật thành công!", "success")
            return redirect(url_for('user.index'))
        else:
            flash("Loại file không được chấp nhận.", "error")
            return redirect(request.url)

@user_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user.index'))

@user_bp.route('/profile')
def profile():
    if 'email' not in session:
        flash("Bạn cần đăng nhập để xem trang cá nhân.", "error")
        return redirect(url_for('user.login'))
    
    email = session['email']
    customer = get_customer_by_email(email)
    
    if not customer:
        flash("Không tìm thấy thông tin khách hàng.", "error")
        return redirect(url_for('user.index'))
    
    booking_history = get_booking_history_by_customer(email)
    services_used = get_services_used_by_customer(email)
    return render_template('profile.html',
                           customer=customer,
                           booking_history=booking_history,
                           services_used=services_used,
                           user_email=email,
                           user_avatar=customer.avatar if hasattr(customer, 'avatar') else 'default.png',
                           user_avatar_hd=customer.avatar_hd if hasattr(customer, 'avatar_hd') else 'default_hd.png')

@user_bp.route('/profile/booking/<booking_id>')
def booking_detail(booking_id):
    if 'email' not in session:
        flash("Bạn cần đăng nhập để xem chi tiết đặt phòng.", "error")
        return redirect(url_for('user.login'))
    
    booking = get_booking_by_id(booking_id)
    if not booking:
        flash("Không tìm thấy thông tin đặt phòng.", "error")
        return redirect(url_for('user.profile'))
    
    return render_template('booking_detail.html', booking=booking)

@user_bp.route('/profile/booking/<booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    if 'email' not in session:
        flash("Bạn cần đăng nhập để hủy đặt phòng.", "error")
        return redirect(url_for('user.login'))
    
    result = update_booking(booking_id, {"TrangThai": "Đã hủy"})
    if result:
        flash("Đặt phòng đã được hủy thành công.", "success")
    else:
        flash("Hủy đặt phòng thất bại.", "error")
    
    return redirect(url_for('user.profile'))

@user_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'email' not in session:
        flash("Bạn cần đăng nhập để chỉnh sửa thông tin.", "error")
        return redirect(url_for('user.login'))
    
    email = session['email']
    customer = get_customer_by_email(email)
    if not customer:
        flash("Không tìm thấy thông tin khách hàng.", "error")
        return redirect(url_for('user.profile'))
    
    if request.method == 'POST':
        ho_ten = request.form.get('ho_ten')
        dien_thoai = request.form.get('dien_thoai')
        cmnd = request.form.get('cmnd')
        dia_chi = request.form.get('dia_chi')
        new_password = request.form.get('password')
        
        avatar_filename = customer.get('avatar')
        file = request.files.get('avatar')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            avatar_filename = f"user_{customer.get('_id')}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], avatar_filename)
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
            file.save(file_path)
        
        bg_image_filename = customer.get('bg_image')
        bg_file = request.files.get('bg_image')
        if bg_file and allowed_file(bg_file.filename):
            filename = secure_filename(bg_file.filename)
            bg_image_filename = f"user_{customer.get('_id')}_bg_{filename}"
            bg_path = os.path.join(current_app.config['UPLOAD_FOLDER'], bg_image_filename)
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
            bg_file.save(bg_path)
        
        update_data = {
            "HoTen": ho_ten,
            "DienThoai": dien_thoai,
            "CMND": cmnd,
            "DiaChi": dia_chi,
            "avatar": avatar_filename,
            "bg_image": bg_image_filename
        }
        if new_password:
            update_data["password"] = new_password
        
        modified = update_customer(email, update_data)
        if modified:
            flash("Cập nhật thông tin thành công!", "success")
        else:
            flash("Không có thay đổi nào.", "info")
        return redirect(url_for('user.profile'))
    
    return render_template('edit_profile.html', customer=customer)

@user_bp.route('/booking/<room_id>', methods=['GET', 'POST'])
def booking(room_id):
    if request.method == 'GET':
        checkin_str = request.args.get('checkin')
        checkout_str = request.args.get('checkout')
        room = get_room_by_id(room_id)
        if not room:
            flash("Không tìm thấy phòng", "error")
            return redirect(url_for('user.index'))

        so_dem = 1
        tong_gia = room.get('price', 0)
        if checkin_str and checkout_str:
            try:
                checkin_date = datetime.strptime(checkin_str, "%Y-%m-%d")
                checkout_date = datetime.strptime(checkout_str, "%Y-%m-%d")
                so_dem = (checkout_date - checkin_date).days
                if so_dem < 1:
                    so_dem = 1
                tong_gia = so_dem * room.get('price', 0)
            except Exception as e:
                print("Error parsing dates:", e)
        
        return render_template(
            'booking.html',
            room=room,
            checkin=checkin_str,
            checkout=checkout_str,
            so_dem=so_dem,
            tong_gia=tong_gia
        )
    else:
        checkin_str = request.form.get('checkin')
        checkout_str = request.form.get('checkout')
        room = get_room_by_id(room_id)
        if room and checkin_str and checkout_str:
            try:
                checkin_date = datetime.strptime(checkin_str, "%Y-%m-%d")
                checkout_date = datetime.strptime(checkout_str, "%Y-%m-%d")
                so_dem = (checkout_date - checkin_date).days
                if so_dem < 1:
                    so_dem = 1
                tong_gia = so_dem * room.get('price', 0)
            except Exception as e:
                print("Error parsing dates in POST:", e)
                so_dem = 1
                tong_gia = room.get('price', 0)
        else:
            so_dem = 1
            tong_gia = room.get('price', 0) if room else 0

        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email') or session.get('email')
        country = request.form.get('country')
        address = request.form.get('address')
        city = request.form.get('city')
        postal_code = request.form.get('postalCode')
        region_code = request.form.get('regionCode')
        phone = request.form.get('phone')

        booking_data = {
            'customer_first_name': first_name,
            'customer_last_name': last_name,
            'email': email,
            'country': country,
            'address': address,
            'city': city,
            'phone': phone,
            'MaPhong': room_id,
            'SoPhong': room.get('SoPhong', None),
            'NgayNhan': checkin_date,
            'NgayTra': checkout_date,
            'TrangThai': "Đã đặt",
            'so_dem': so_dem,
            'tong_gia': tong_gia,
            'allow_cancel': True
        }
        create_booking(booking_data)
        return redirect(url_for('payment.create_payment', amount=tong_gia))