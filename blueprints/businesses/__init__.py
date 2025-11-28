from flask import Blueprint

businesses_bp = Blueprint('businesses', __name__)

from . import routes