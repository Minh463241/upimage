from flask import Blueprint, flash, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import io

# Import các hàm và collection từ db_mongo
from db_mongo import (
    staff_collection,
    get_all_room_types,
    add_room_type,
    add_room_with_image,
    add_room_to_db,
    get_all_rooms,
    get_room_by_id,
    update_room,
    rooms_collection
)

# Hàm kiểm tra định dạng file
from utils.helpers import allowed_file

# Hàm bảo vệ route (yêu cầu đăng nhập với quyền staff/admin)
from utils.auth import staff_or_admin_required

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = staff_collection.find_one({"Email": email})
        if user and user.get("password") == password:
            session['user_id'] = str(user['_id'])
            session['role'] = user.get('role', 'staff')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            error = "Thông tin đăng nhập không chính xác"
            return render_template('admin_login.html', error=error)
    return render_template('admin_login.html')

@admin_bp.route('/dashboard')
@staff_or_admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/add_room_type', methods=['GET', 'POST'])
@staff_or_admin_required
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
            return redirect(url_for('admin.add_room_type_route'))
        room_type_data = {
            'name': ten_loai,
            'price': gia_phong,
            'description': mota
        }
        result = add_room_type(room_type_data)
        if result:
            flash("Thêm loại phòng thành công!", "success")
            return redirect(url_for('admin.add_room_type_route'))
        else:
            flash("Thêm loại phòng thất bại.", "error")
            return redirect(url_for('admin.add_room_type_route'))

@admin_bp.route('/add_room', methods=['GET', 'POST'])
@staff_or_admin_required
def add_room():
    if request.method == 'GET':
        room_types = get_all_room_types()
        rooms = get_all_rooms()

        # Tạo mapping cho room_types theo ID (key là chuỗi)
        room_type_map = {str(rt['_id']): rt for rt in room_types}
        for phong in rooms:
            # Map trường số phòng và trạng thái theo tên mà template mong đợi
            phong['room_number'] = phong.get('SoPhong')
            phong['status'] = phong.get('TrangThai')
            ma_loai = phong.get('MaLoaiPhong')
            phong['room_type'] = room_type_map.get(ma_loai, {'name': ma_loai})
        return render_template('add_room.html', room_types=room_types, rooms=rooms)
    
    so_phong = request.form.get('room_number')
    ma_loai_phong = request.form.get('room_type')
    mo_ta = request.form.get('description')
    trang_thai = "Trống"  # Mặc định là "Trống"
    
    if not ma_loai_phong or not ma_loai_phong.strip():
        flash("Chưa chọn loại phòng.", "error")
        return redirect(url_for('admin.add_room'))
    
    file = request.files.get('room_image')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_bytes = file.read()
        file_stream = io.BytesIO(file_bytes)
        file_stream.seek(0)
        add_room_with_image(file_stream, f"room_{filename}", so_phong, ma_loai_phong, mo_ta, "", trang_thai)
    else:
        add_room_to_db(so_phong, ma_loai_phong, mo_ta, trang_thai)
    
    flash("Thêm phòng thành công!", "success")
    return redirect(url_for('admin.add_room'))

@admin_bp.route('/edit_room/<room_id>', methods=['GET', 'POST'])
@staff_or_admin_required
def edit_room(room_id):
    room = get_room_by_id(room_id)
    if not room:
        flash("Phòng không tồn tại.", "error")
        return redirect(url_for('admin.add_room'))
    
    if request.method == 'GET':
        room_types = get_all_room_types()
        return render_template('edit_room.html', room=room, room_types=room_types)
    
    # POST: Cập nhật thông tin phòng
    so_phong = request.form.get('room_number')
    ma_loai_phong = request.form.get('room_type')
    mo_ta = request.form.get('description')
    trang_thai = request.form.get('status')  # 'Trống' hoặc 'Đã đặt'
    
    update_data = {
        'SoPhong': so_phong,
        'MaLoaiPhong': ma_loai_phong,
        'MoTa': mo_ta,
        'TrangThai': trang_thai,
    }
    
    file = request.files.get('room_image')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_bytes = file.read()
        file_stream = io.BytesIO(file_bytes)
        file_stream.seek(0)
        from upload_cloudinary import upload_image
        try:
            image_url = upload_image(file_stream)
            update_data['image_url'] = image_url
            update_data['image_url_hd'] = image_url
        except Exception as e:
            flash("Cập nhật ảnh thất bại", "error")
    
    result = update_room(room_id, update_data)
    if result:
        flash("Cập nhật phòng thành công", "success")
    else:
        flash("Cập nhật phòng thất bại", "error")
    return redirect(url_for('admin.add_room'))

@admin_bp.route('/delete_room/<room_id>', methods=['GET'])
@staff_or_admin_required
def delete_room(room_id):
    result = rooms_collection.delete_one({'MaPhong': room_id})
    if result.deleted_count:
        flash("Xóa phòng thành công", "success")
    else:
        flash("Xóa phòng thất bại", "error")
    return redirect(url_for('admin.add_room'))
