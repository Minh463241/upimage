# routes/utility_routes.py
from flask import Blueprint, redirect, request, jsonify, url_for
from datetime import datetime

utility_bp = Blueprint('utility', __name__)

@utility_bp.route('/change_language/<lang>')
def change_language(lang):
    referrer = request.referrer or url_for('user.index')
    response = redirect(referrer)
    response.set_cookie('lang', lang)
    return response

@utility_bp.route('/time', methods=['GET'])
def get_time():
    return jsonify({"current_utc_time": datetime.utcnow().isoformat()})