# routes/staff_routes.py
from flask import Blueprint, render_template

staff_bp = Blueprint('staff', __name__, template_folder='../templates/staff')

@staff_bp.route('/dashboard')
def staff_dashboard():
    return render_template('staff_dashboard.html')