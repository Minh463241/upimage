import cloudinary
import cloudinary.uploader

def upload_image(file):
    """
    Upload ảnh lên Cloudinary và trả về URL an toàn (secure_url).
    Nếu xảy ra lỗi, in lỗi và trả về None.
    """
    try:
        result = cloudinary.uploader.upload(file)
        return result.get("secure_url")
    except Exception as e:
        print("Lỗi khi upload ảnh lên Cloudinary:", e)
        return None
