import os
from flask import Flask, request, render_template_string, redirect, url_for
from dotenv import load_dotenv
import cloudinary
import pymongo
from datetime import datetime
import mongondb  # module quản lý MongoDB của bạn
from upload_cloudinary import upload_image  # Import hàm upload từ file riêng

# Load biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)

# Cấu hình Cloudinary từ biến môi trường (sử dụng CLOUDINARY_URL)
cloudinary.config(secure=True)

# --- Route: Thêm phòng ---
@app.route("/add_room", methods=["GET", "POST"])
def add_room():
    if request.method == "POST":
        so_phong     = request.form.get("so_phong")
        ma_loai_phong = request.form.get("ma_loai_phong")
        mo_ta        = request.form.get("mo_ta")
        trang_thai   = request.form.get("trang_thai", "Trống")
        image_file   = request.files.get("room_image")

        image_url = None
        if image_file:
            # Sử dụng hàm upload_image() từ file upload_cloudinary.py
            image_url = upload_image(image_file)
        
        # Tạo dữ liệu phòng với trường image_url (nếu có)
        room_data = {
            "SoPhong": so_phong,
            "MaLoaiPhong": ma_loai_phong,
            "MoTa": mo_ta,
            "TrangThai": trang_thai,
            "created_at": datetime.utcnow(),
            "image_url": image_url  # Lưu đường dẫn ảnh
        }
        
        # Sử dụng hàm create_room() từ module mongondb.py để lưu vào MongoDB
        room_id = mongondb.create_room(room_data)
        
        # Nếu có ảnh, lưu thông tin ảnh vào collection room_images (tùy chọn)
        if image_url:
            room_image_data = {
                "MaPhong": room_id,          # Liên kết với phòng vừa tạo
                "DuongDanAnh": image_url,     # Đường dẫn ảnh từ Cloudinary
                "MoTa": f"Ảnh phòng {so_phong}",
                "uploaded_at": datetime.utcnow()
            }
            mongondb.create_room_image(room_image_data)
        
        return redirect(url_for("list_rooms"))
    
    # Form thêm phòng
    return render_template_string('''
        <h1>Thêm phòng</h1>
        <form method="POST" enctype="multipart/form-data">
            <label>Số phòng:</label>
            <input type="text" name="so_phong" required><br><br>
            
            <label>Mã loại phòng:</label>
            <input type="text" name="ma_loai_phong" required><br><br>
            
            <label>Mô tả:</label>
            <textarea name="mo_ta" rows="4" cols="50"></textarea><br><br>
            
            <label>Trạng thái:</label>
            <input type="text" name="trang_thai" value="Trống"><br><br>
            
            <label>Ảnh phòng:</label>
            <input type="file" name="room_image"><br><br>
            
            <button type="submit">Thêm phòng</button>
        </form>
        <br>
        <a href="{{ url_for('list_rooms') }}">Xem danh sách phòng</a>
    ''')

# --- Route: Hiển thị danh sách phòng ---
@app.route("/rooms")
def list_rooms():
    rooms = mongondb.get_all_rooms()
    html = '<h1>Danh sách phòng</h1>'
    for room in rooms:
        html += f"<h3>Số phòng: {room.get('SoPhong')}</h3>"
        if room.get("image_url"):
            html += f'<img src="{room.get("image_url")}" alt="Room Image" style="max-width:200px;"><br>'
        html += "<hr>"
    html += '<br><a href="/add_room">Thêm phòng mới</a>'
    return html

if __name__ == "__main__":
    app.run(debug=True)
