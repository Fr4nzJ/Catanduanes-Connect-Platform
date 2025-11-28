from flask import Blueprint

verification_bp = Blueprint('verification', __name__)

from . import routes