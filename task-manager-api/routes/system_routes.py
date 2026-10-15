from datetime import datetime

from flask import Blueprint, jsonify

API_NAME = 'Task Manager API'
API_VERSION = '1.0'

system_bp = Blueprint('system', __name__)


@system_bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': str(datetime.now())})


@system_bp.route('/')
def index():
    return jsonify({'message': API_NAME, 'version': API_VERSION})
