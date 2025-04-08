# routes/account_routes.py
from flask import Blueprint, flash, render_template, request, redirect, url_for
from db_mongo import staff_collection, get_all_staff, create_staff, update_staff_role, get_staff_by_id, update_staff_info, delete_staff
from utils.auth import admin_required

account_bp = Blueprint('account', __name__, template_folder='../templates/admin')

@account_bp.route('/accounts', methods=['GET', 'POST'])
@admin_required
def admin_accounts():
    if request.method == 'POST':
        HoTen = request.form.get('HoTen')
        Email = request.form.get('Email')
        password = request.form.get('password')
        role = request.form.get('role')
        if not (HoTen and Email and password and role):
            flash("Vui lòng nhập đầy đủ thông tin", "danger")
            return redirect(url_for('account.admin_accounts'))
        new_staff = {
            "HoTen": HoTen,
            "Email": Email,
            "password": password,
            "role": role
        }
        create_staff(new_staff)
        flash("Thêm nhân viên thành công", "success")
        return redirect(url_for('account.admin_accounts'))
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

@account_bp.route('/update-role', methods=['POST'])
@admin_required
def update_staff_role_route():
    staff_id = request.form.get("staff_id")
    new_role = request.form.get("role")
    if not staff_id or new_role not in ['admin', 'staff']:
        flash("Thông tin không hợp lệ", "danger")
        return redirect(url_for('account.admin_accounts'))
    modified = update_staff_role(staff_id, new_role)
    if modified:
        flash("Cập nhật quyền thành công", "success")
    else:
        flash("Không có thay đổi nào", "info")
    return redirect(url_for('account.admin_accounts'))

@account_bp.route('/accounts/edit/<staff_id>', methods=['GET', 'POST'])
@admin_required
def edit_staff_route(staff_id):
    staff = get_staff_by_id(staff_id)
    if not staff:
        flash("Nhân viên không tồn tại", "danger")
        return redirect(url_for('account.admin_accounts'))
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
        return redirect(url_for('account.admin_accounts'))
    else:
        staff['_id'] = str(staff['_id'])
        return render_template('edit_staff.html', staff=staff)

@account_bp.route('/accounts/delete/<staff_id>', methods=['POST'])
@admin_required
def delete_staff_route(staff_id):
    result = delete_staff(staff_id)
    if result:
        flash("Xóa nhân viên thành công", "success")
    else:
        flash("Không thể xóa nhân viên", "danger")
    return redirect(url_for('account.admin_accounts'))