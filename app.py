import os
import hashlib
import urllib.parse
from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import functools
from datetime import timedelta, datetime
import hmac
import stripe
import cloudinary
import cloudinary.uploader
# Cấu hình Cloudinary trực tiếp trong app.py
cloudinary.config(
    cloud_name="dwczro6hp",
    api_key="648677879979597",
    api_secret="-1D5fNq5hrtfGoIeZ8U7n8GHWi0",
    secure=True
)

# Import các hàm từ db_mongo.py (MongoDB)
from db_mongo import (
    create_customer,
    get_customer_by_email,
    update_last_login,
    update_user_avatar,
    get_all_rooms,
    get_all_room_types,
    add_room_type,
    get_room_by_id,
    is_room_booked,
    create_booking,
    add_room_with_image,
    add_room_to_db,
    get_all_staff,
    update_staff_role,
    create_staff, 
    update_staff_info,
    get_staff_by_id,
    delete_staff,
    staff_collection,
    get_booking_history_by_customer,
    get_services_used_by_customer,
    update_customer
)

# -------------------------------
# Cài đặt Stripe
# -------------------------------

stripe.api_key = "sk_test_51QzvBe4ItrNbWOZiuMzul21da8fG1mtQa5hj4nznqqje0PbD0zKUpKekh4rcQWlSrSnlzrCknEPAqAKYQdbpmNTs00u4BJTBxR"

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=7)

# Cấu hình cho file upload (sử dụng cho avatar và phòng)
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'avatars')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------
# ROUTE: Thay đổi ngôn ngữ
# -------------------------------
@app.route('/change_language/<lang>')
def change_language(lang):
    referrer = request.referrer or url_for('index')
    response = redirect(referrer)
    response.set_cookie('lang', lang)
    return response

# -------------------------------
# ROUTE: Trang chủ (hiển thị danh sách phòng)
# -------------------------------
@app.route('/')
def index():
    user_email = session.get('email')
    user_avatar = session.get('avatar', 'default.jpg')
    rooms = get_all_rooms()  # Lấy danh sách phòng từ MongoDB

    # Các bộ lọc (nếu có)
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

# -------------------------------
# ROUTE: Tìm kiếm (hiển thị lại trang chủ)
# -------------------------------
@app.route('/search', methods=['GET'])
def search():
    destination = request.args.get('destination')
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')
    guests = request.args.get('guests')
    print("Search data:", destination, checkin, checkout, guests)
    return render_template('index.html')

# -------------------------------
# ROUTE: Đăng nhập
# -------------------------------
@app.route('/login', methods=['GET', 'POST'])
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
                    return redirect(url_for('index'))
            else:
                if request.is_json:
                    return jsonify({"success": False, "message": "Mật khẩu không chính xác"})
                else:
                    flash("Mật khẩu không chính xác", "error")
                    return redirect(url_for('login'))
        else:
            if request.is_json:
                return jsonify({"success": False, "message": "Không tìm thấy tài khoản với email này"})
            else:
                flash("Không tìm thấy tài khoản với email này", "error")
                return redirect(url_for('login'))

# -------------------------------
# ROUTE: Đăng ký
# -------------------------------
@app.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('register'))
        
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
            return redirect(url_for('login'))
        else:
            flash("Đăng ký thất bại.", "error")
            return redirect(url_for('register'))

# -------------------------------
# ROUTE: Cập nhật avatar
# -------------------------------
@app.route('/update_avatar', methods=['GET', 'POST'])
def update_avatar():
    if 'user_id' not in session or 'email' not in session:
        flash("Bạn cần đăng nhập để thay đổi avatar.", "error")
        return redirect(url_for('auth_bp.login'))
    
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
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            file.save(file_path)
            update_user_avatar(session['email'], filename)
            session['avatar'] = filename
            flash("Avatar cập nhật thành công!", "success")
            return redirect(url_for('index'))
        else:
            flash("Loại file không được chấp nhận.", "error")
            return redirect(request.url)
# -------------------------------
# ROUTE: Đăng xuất
# -------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# -------------------------------
# ROUTE: Quản trị Admin
# -------------------------------
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Bạn không có quyền truy cập chức năng này", "danger")
            return redirect(url_for('staff_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = staff_collection.find_one({"Email": email})
        if user and user.get("password") == password:
            session['user_id'] = str(user['_id'])
            session['role'] = user.get('role', 'staff')
            if session['role'] != 'admin':
                flash("Tài khoản nhân viên không được phép truy cập chức năng admin", "danger")
                return redirect(url_for('staff_dashboard'))
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Thông tin đăng nhập không chính xác"
            return render_template('admin_login.html', error=error)
    return render_template('admin_login.html')

@app.route('/staff/dashboard')
def staff_dashboard():
    return "Đây là trang dashboard của nhân viên. Bạn không có quyền truy cập chức năng admin."

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/add_room_type', methods=['GET', 'POST'])
def add_room_type_route():
    if request.method == 'GET':
        room_types = get_all_room_types()
        return render_template('add_room_type.html', room_types=room_types)
    else:
        ten_loai = request.form.get('ten_loai')
        gia_phong = request.form.get('gia_phong')
        mota = request.form.get('mota')
        try:
            gia_phong = float(gia_phong)
        except (ValueError, TypeError):
            flash("Giá phòng không hợp lệ.", "error")
            return redirect(url_for('add_room_type_route'))
        room_type_data = {
            'name': ten_loai,
            'price': gia_phong,
            'description': mota
        }
        result = add_room_type(room_type_data)
        if result:
            flash("Thêm loại phòng thành công!", "success")
            return redirect(url_for('add_room_type_route'))
        else:
            flash("Thêm loại phòng thất bại.", "error")
            return redirect(url_for('add_room_type_route'))

# -------------------------------
# ROUTE: Thêm phòng (upload ảnh lên Cloudinary)
# -------------------------------
@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    if request.method == 'GET':
        room_types = get_all_room_types()
        return render_template('add_room.html', room_types=room_types)
    
    try:
        so_phong = request.form.get('room_number')
        ma_loai_phong = request.form.get('room_type')
        mo_ta = request.form.get('description')
        trang_thai = "Trống"
        
        file = request.files.get('room_image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Hàm add_room_with_image sẽ upload ảnh lên Cloudinary qua hàm upload_file_to_cloudinary
            add_room_with_image(file_path, filename, so_phong, ma_loai_phong, mo_ta, image_description="Ảnh phòng", trang_thai=trang_thai)
        else:
            add_room_to_db(so_phong, ma_loai_phong, mo_ta, trang_thai)
        
        flash("Thêm phòng thành công!", "success")
        return redirect(url_for('add_room'))
    
    except Exception as e:
        flash(f"Lỗi khi thêm phòng: {str(e)}", "error")
        return redirect(url_for('add_room'))



# -------------------------------
# ROUTE: Trang cá nhân
# -------------------------------
@app.route('/profile')
def profile():
    # Kiểm tra nếu khách hàng đã đăng nhập
    if 'email' not in session:
        flash("Bạn cần đăng nhập để xem trang cá nhân.", "error")
        return redirect(url_for('auth_bp.login'))
    
    email = session['email']
    customer = get_customer_by_email(email)
    
    if not customer:
        flash("Không tìm thấy thông tin khách hàng.", "error")
        return redirect(url_for('index'))
    
    booking_history = get_booking_history_by_customer(email)
    services_used = get_services_used_by_customer(email)
    
    return render_template('profile.html',
                           customer=customer,
                           booking_history=booking_history,
                           services_used=services_used)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'email' not in session:
        flash("Bạn cần đăng nhập để chỉnh sửa thông tin.", "error")
        return redirect(url_for('auth_bp.login'))
    
    email = session['email']
    customer = get_customer_by_email(email)
    if not customer:
        flash("Không tìm thấy thông tin khách hàng.", "error")
        return redirect(url_for('profile'))
    
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
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            file.save(file_path)
        
        bg_image_filename = customer.get('bg_image')
        bg_file = request.files.get('bg_image')
        if bg_file and allowed_file(bg_file.filename):
            filename = secure_filename(bg_file.filename)
            bg_image_filename = f"user_{customer.get('_id')}_bg_{filename}"
            bg_path = os.path.join(app.config['UPLOAD_FOLDER'], bg_image_filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
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
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', customer=customer)

# -------------------------------
# ROUTE: Đặt phòng (Booking) & Thanh toán
# -------------------------------
@app.route('/booking/<room_id>', methods=['GET', 'POST'])
def booking(room_id):
    if request.method == 'GET':
        checkin_str = request.args.get('checkin')
        checkout_str = request.args.get('checkout')
        room = get_room_by_id(room_id)
        if not room:
            flash("Không tìm thấy phòng", "error")
            return redirect(url_for('index'))

        so_dem = 1
        tong_gia = room.get('price', 0)
        if checkin_str and checkout_str:
            try:
                checkin_date = datetime.strptime(checkin_str, "%Y-%m-%d").date()
                checkout_date = datetime.strptime(checkout_str, "%Y-%m-%d").date()
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
                checkin_date = datetime.strptime(checkin_str, "%Y-%m-%d").date()
                checkout_date = datetime.strptime(checkout_str, "%Y-%m-%d").date()
                so_dem = (checkout_date - checkin_date).days
                if so_dem < 1:
                    so_dem = 1
                tong_gia = so_dem * room.get('price', 0)
            except Exception as e:
                print("Error parsing dates in POST:", e)
                tong_gia = 0
        else:
            tong_gia = 0

        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
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
            'postal_code': postal_code,
            'region_code': region_code,
            'phone': phone,
        }
        create_booking(booking_data)
        # Sau khi đặt phòng xong, chuyển hướng thanh toán qua Stripe Checkout
        return redirect(url_for('create_payment', amount=tong_gia))

# -------------------------------
# ROUTE: Tích hợp Thanh toán Stripe (Checkout Session)
# -------------------------------
@app.route('/create_payment')
def create_payment():
    # Lấy số tiền thanh toán (đơn vị: cents)
    # Ví dụ: nếu tong_gia là 1000, tức là $10.00
    amount = request.args.get('amount', default=1000, type=int)
    try:
        session_stripe = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Thanh toán đặt phòng khách sạn',
                    },
                    'unit_amount': amount,  # Số tiền tính bằng cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('stripe_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('stripe_cancel', _external=True),
        )
        print("Stripe Checkout Session URL:", session_stripe.url)
        return redirect(session_stripe.url, code=303)
    except Exception as e:
        return str(e), 400

@app.route('/stripe_success')
def stripe_success():
    flash("Thanh toán thành công!", "success")
    return redirect(url_for('index'))

@app.route('/stripe_cancel')
def stripe_cancel():
    flash("Thanh toán đã bị hủy!", "error")
    return redirect(url_for('index'))

# -------------------------------
# ROUTE: Quản trị Admin (các route admin khác giữ nguyên)
# -------------------------------
#thêm nhân viên
@app.route('/admin/accounts', methods=['GET', 'POST'])
@admin_required
def admin_accounts():
    if request.method == 'POST':
        HoTen = request.form.get('HoTen')
        Email = request.form.get('Email')
        password = request.form.get('password')
        role = request.form.get('role')
        if not (HoTen and Email and password and role):
            flash("Vui lòng nhập đầy đủ thông tin", "danger")
            return redirect(url_for('admin_accounts'))
        new_staff = {
            "HoTen": HoTen,
            "Email": Email,
            "password": password,
            "role": role
        }
        create_staff(new_staff)
        flash("Thêm nhân viên thành công", "success")
        return redirect(url_for('admin_accounts'))
    else:
        search_query = request.args.get('q', '')
        if search_query:
            staff_list = list(staff_collection.find(
                {"HoTen": {"$regex": search_query, "$options": "i"}},
                {"HoTen": 1, "Email": 1, "role": 1}
            ))
        else:
            staff_list = get_all_staff()
        for staff in staff_list:
            staff['_id'] = str(staff['_id'])
        return render_template('admin_accounts.html', staff_list=staff_list, search_query=search_query)

@app.route('/staff/update-role', methods=['POST'])
@admin_required
def update_staff_role_route():
    staff_id = request.form.get("staff_id")
    new_role = request.form.get("role")
    if not staff_id or new_role not in ['admin', 'staff']:
        flash("Thông tin không hợp lệ", "danger")
        return redirect(url_for('admin_accounts'))
    modified = update_staff_role(staff_id, new_role)
    if modified:
        flash("Cập nhật quyền thành công", "success")
    else:
        flash("Không có thay đổi nào", "info")
    return redirect(url_for('admin_accounts'))

@app.route('/admin/accounts/edit/<staff_id>', methods=['GET', 'POST'])
@admin_required
def edit_staff_route(staff_id):
    staff = get_staff_by_id(staff_id)
    if not staff:
        flash("Nhân viên không tồn tại", "danger")
        return redirect(url_for('admin_accounts'))
    if request.method == 'POST':
        HoTen = request.form.get('HoTen')
        Email = request.form.get('Email')
        password = request.form.get('password')
        role = request.form.get('role')
        update_data = {"HoTen": HoTen, "Email": Email, "role": role}
        if password:
            update_data["password"] = password
        modified = update_staff_info(staff_id, update_data)
        if modified:
            flash("Cập nhật thông tin nhân viên thành công", "success")
        else:
            flash("Không có thay đổi nào", "info")
        return redirect(url_for('admin_accounts'))
    else:
        staff['_id'] = str(staff['_id'])
        return render_template('edit_staff.html', staff=staff)

@app.route('/admin/accounts/delete/<staff_id>', methods=['POST'])
@admin_required
def delete_staff_route(staff_id):
    result = delete_staff(staff_id)
    if result:
        flash("Xóa nhân viên thành công", "success")
    else:
        flash("Không thể xóa nhân viên", "danger")
    return redirect(url_for('admin_accounts'))

@app.template_filter('date_format')
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

@app.route('/time', methods=['GET'])
def get_time():
    return jsonify({"current_utc_time": datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(debug=True)
